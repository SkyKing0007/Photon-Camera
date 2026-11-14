#!/usr/bin/env python3
"""Real 26934 shader-equivalent host math: RawLens LKR brightness-driven white fade.
Tests do NOT replace full real GLSL/SPIRV/NDK/Kotlin/Java/assemble or device photos.
"""
import sys,math,re
from build_26934_incremental import R,fail

def ss(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3.-2.*t)
def fade(cam,gains=(2.,1.,1.55),clipped=0.):
 # Test post-WB camera RGB with same shared-white normalization as live GLSL.
 wb=[cam[i]*gains[i] for i in range(3)]
 peak=max(wb);safe=min(gains);v=peak/safe
 visual=max(ss(.70,.99,q/safe) for q in wb)
 physical=ss(.08,.26,clipped)*ss(.55,.78,v)
 return max(visual,physical)
def old26933(cam,gains=(2.,1.,1.55)):
 wb=[cam[i]*gains[i] for i in range(3)]; peak=max(wb)
 neutral=ss(.50,.75,min(wb)/max(peak,1e-4))
 return neutral*ss(.70,.99,peak/min(gains))
def main():
 p=R/('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt' if '--live' in sys.argv else 'handoff_payload_26934/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt')
 s=p.read_text()
 for k in ('smoothstep(vec3(0.70),vec3(0.99),visualRgb)',
           'float visualFade=max(whiteCurve.r,max(whiteCurve.g,whiteCurve.b));',
           'float clipFade=smoothstep(0.08,0.26,',
           'smoothstep(0.55,0.78,peak);',
           'float whiteTarget=max(peakWb,sharedWhite);',
           'vec3 corrected=mix(original.rgb,vec3(whiteTarget),fade);'):
  if k not in s:fail('current live GLSL and numerical test disagree '+k)
 # 26933 error reproduced: pink due to low green despite visibly clipped red/blue.
 samples=((.9,.04,.85),(.85,.2,.85),(.96,.05,.80),(.86,.4,.2),(.25,.995,.3))
 for pix in samples:
  if fade(pix)<.99999:fail('visually clipped colored light NOT fully whitened '+str(pix))
  if old26933(pix)>.6:fail('regression sample does not distinguish old 26933 color veto')
 # No color/brightness effect on ordinary (non-highlight) pixels.
 for pix in ((0.,0.,0.),(.1,.1,.1),(.25,.25,.20),(.3,.3,.3)):
  if fade(pix)!=0:fail('midtone affected without clipping '+str(pix))
 # Continuous 0.70..0.99 RawLens shoulder; no chromaticity gating.
 last=-1
 for n in range(101):
  x=n*.01
  f=fade((x/2.,x,x/1.55))
  if f+1e-9<last:fail('white fade not monotone')
  last=f
 if abs(fade((.70/2.,.70,.70/1.55)))>1e-8 or abs(fade((.99/2.,.99,.99/1.55))-1.)>1e-8:
  fail('RawLens exact 0.70..0.99 shoulder endpoints wrong')
 for x in (.73,.82,.9,.95):
  f=fade((x/2.,x,x/1.55))
  if not 0<f<1:fail('continuous neutral highlight fade broken '+str(x))
 # Sensor source evidence may help near-clip, but never gate the visual fade.
 pix=(.36,.73,.35)
 if fade(pix,.0 if False else (2.,1.,1.55),clipped=.5)<fade(pix):fail('RAW binary clip witness vetoes visual fade')
 # Fading to locally neutral max never darkens individual channels and
 # never creates a color tint from a neutral input. No additional WB cycles.
 for pix in ((.82,.12,1.04),(.9,.8,.85),(.5,.5,.5)):
  f=fade(pix);pre=[pix[i]*[2.,1.,1.55][i] for i in range(3)];white=max(1.,*pre)
  target=[pre[i]*(1-f)+white*f for i in range(3)]
  if any(v+1e-8<x or v>white+1e-8 for v,x in zip(target,pre)):fail('nonconvex white output')
 print('PASS 26934 RawLens actual 0.70..0.99 brightness-driven fade, colored clipped sources, binary RAW clip, B ON only')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
