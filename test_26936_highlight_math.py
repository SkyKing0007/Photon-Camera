#!/usr/bin/env python3
"""Executable numerical replay of unchanged sensor clip gating and new B ON chroma-aware rolloff.
Standalone, no mocks of the actual Android compiler. Regression acceptance tests
exercise broad yellow/orange highlight materials, pink fully-clipped cores,
continuous transitions, no negative/luminance collapse, and B OFF saturation.
"""
import math,sys
from build_26936_incremental import R,fail

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3-2*t)
def fade(rgb,cfa=(0.,0.,0.),coverage=0.):
 peak=max(rgb);second=sorted(rgb)[1];third=min(rgb)
 balanced=smooth(.42,.72,third/max(peak,.0001))
 visual=smooth(.72,1.02,second)*smooth(.74,1.08,peak)*balanced
 all_colors=min(cfa)
 green_color=min(cfa[1],max(cfa[0],cfa[2]))
 physical=max(smooth(.12,.70,all_colors),.65*balanced*smooth(.20,.82,green_color))
 sensor=smooth(.12,.82,coverage)*physical*smooth(.60,.94,peak)
 return max(visual,sensor)
def white(rgb,clip=(0.,0.,0.),coverage=0.):
 f=fade(rgb,clip,coverage)
 return tuple(c*(1-f)+max(rgb)*f for c in rgb)
def main():
 h=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt' if '--live' in sys.argv
    else R/'handoff_payload_26936/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt').read_text()
 for token in ('smoothstep(0.42,0.72,third/max(peak,0.0001))',
               'smoothstep(0.72,1.02,second)','smoothstep(0.74,1.08,peak)',
               'smoothstep(0.12,0.70,allColors)','smoothstep(0.20,0.82,greenAndColor)',
               'smoothstep(0.12,0.82,coverage)','smoothstep(0.60,0.94,peak)',
               'vec3 corrected=mix(original.rgb,vec3(localPeak),fade);'):
  if token not in h:fail('numerical test no longer matches LIVE shader math '+token)
 for c in ((1.0,.88,.08),(.95,.65,.16),(1.5,1.42,.11),(.6,.2,.1)):
  if fade(c)>1e-7 or white(c)!=c:fail('genuine saturated material bleached '+str(c))
 if fade((1.2,1.2,1.2))<.95:fail('broad visible neutral white not smoothly neutralized')
 if fade((1.03,.55,.80),(1.,1.,1.),1.)<.95:fail('independently all-channel clipped pink retained')
 # Binary, sparse green/red physical clip cannot whitewash a physically unclipped blue channel.
 if fade((1.,.91,.12),(1.,1.,0.),1.)>.000001:fail('two-channel physical clip bleached real yellow')
 # The new output never becomes darker than the pixel's original individual channels.
 for x in range(101):
  k=x/100
  for col in ((k,.9*k,.05*k),(.89*k,.96*k,.95*k),(.9*k,.3*k,.15*k)):
   out=white(col,(k,k,k),k)
   if any((a-b)<-1e-6 for a,b in zip(out,col)) or not all(math.isfinite(a) for a in out):
    fail('color/white boundary nonfinite or darkens original material')
 for x in range(1,1000):
  k=x/1000
  a=white((k,.8*k,.2*k),(k,k,k),k)
  b=white((k+1e-5,.8*(k+1e-5),.2*(k+1e-5)),(k,k,k),k)
  if max(abs(z-w) for z,w in zip(a,b))>.002:fail('discontinuous smooth rolloff curve')
 # Both SDR and UHDR routing frozen to the B OFF selection only.
 motion=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java' if '--live' in sys.argv else R/'handoff_payload_26936/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 native=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java' if '--live' in sys.argv else R/'handoff_payload_26936/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java').read_text()
 if 'iris26936BOffSaturation ? 1.02f' not in motion or 'iris26936BOffSaturation ? 1.02f' not in native:
  fail('B OFF SDR/UHDR saturation not 1.02')
 print('PASS physical R/G/B evidence preserving yellow hue, smooth non-darkening transition, all-channel clipped pink, B OFF SDR/UHDR saturation')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
