#!/usr/bin/env python3
"""Host scalar/scope numerical regressions, NOT a substitute for device shader or real compiler."""
from pathlib import Path
import sys,math,re
from build_26932_incremental import R,fail

def smooth(a,b,x):
 t=min(max((x-a)/(b-a),0),1)
 return t*t*(3-2*t)
def bridge(y,src):
 if y<=0 or y>=0.95:return y
 c=min(max((max(src,0)-y)/max(src,0.01),0),1)
 body=smooth(.005,.065,y)*(1-smooth(.28,.95,y))
 return min(y*(1+body*(.18+.40*c)),1)
def tone(y):
 if y>=.74:return y
 tg=1-smooth(.012,.165,y);toe=y*(1-.2*tg)
 cg=smooth(.130,.205,y)*(1-smooth(.520,.740,y))
 ct=.230*pow(max(toe/.230,1e-6),1.20)
 return max(toe*(1-cg)+ct*cg,0)

def main():
 for strength in (0,.15,.4,.65,1):
  ys=[i*.0005 for i in range(2001)];old=-1
  for y in ys:
   val=bridge(y,y/(1-.58*strength) if strength<1 else y*5)
   if val<old-1e-6:fail('SDR bridge is not monotone')
   if val<y-1e-9:fail('SDR bridge unexpectedly darkens')
   old=val
 assert bridge(0,.8)==0 and bridge(1,2)==1
 assert tone(.02)<.02 and tone(.74)==.74 and abs(tone(.23)-.23)<.005
 old=-1
 for i in range(2001):
  t=tone(i*.0005)
  if t<old-1e-5:fail('B ON target toe/contrast has inversion')
  old=t
 root=R if '--live' in sys.argv else R/'handoff_payload_26932'
 render=(root/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 gain=(root/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
 def function(txt):
  start=txt.index('float iris26932BOffSdrBridge(')
  end=txt.index('float iris26906BVisualTone(',start)
  return txt[start:end].strip()
 if function(render)!=function(gain):fail('SDR renderer and UHDR gain-map denominator use different curves')
 old_guide=(root/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
 if 'float hdrIntentY=sdr+matchedIntentDelta;' not in old_guide or 'float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);' not in old_guide:fail('unchanged HDR delta and gainmap parity lost')
 print('PASS numerical monotone/smooth 26932 B ON toe and B OFF SDR, exact matched HDR numerator/denominator, not device-quality proof')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
