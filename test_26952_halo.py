#!/usr/bin/env python3
"""Conservative high-contrast bright-edge overshoot bound, no global sky/green darkening."""
import math,re,sys
from build_26952_incremental import R,fail,scope,sha
src=R/('app/src/main/assets/shaders/motionv2/render.glsl' if '--live' in sys.argv else 'handoff_payload_26952/app/src/main/assets/shaders/motionv2/render.glsl')
s=src.read_text()
start=s.index('vec3 iris26952ConstrainRim(');end=s.index('\nvoid main()',start)
code=s[start:end]
for needle in ('iris26948BUniversalSdrEnabled==0','iris26592MotionHdrHandoff==0','irisOutputZoom>1.00001','if(peak<=0.60)return rgb;','for(int axis=0;axis<4;axis++)','for(int side=-1;side<=1;side+=2)','edgeContrast>0.15*max(plateau,0.05)','plateauDelta<0.075*max(plateau,0.05)','peak>plateau+0.006*max(peak,0.05)','limited=min(limited,cap);','max(peak*0.975,limited)'):
 if needle not in code:fail('rim gate missing '+needle)
# 26952 V3 real GLSLang failure: `flat` is a reserved ESSL interpolation keyword.
# A local numeric test formerly accepted `float flat=...`; enforce valid names
# on the real production GLSL region and retain an explicit negative control.
active=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)
if re.search(r'\bflat\b',active) or re.search(r'\b(?:float|int|bool|vec[234]|ivec[234])\s+(?:coherent|volatile|restrict|readonly|writeonly)\b',active):
 fail('26952 V3 GLSLang unexpected FLAT/other reserved GLSL identifier regression')
if code.count('float plateauDelta=abs(bright1-bright2);')!=1:
 fail('corrected non-reserved halo GLSL plateauDelta variable absent')
if 'mix(' in code or 'texture(' in code or 'textureLod' in code:fail('rim gate must not resample/color blend')
if s.index('iris26952ConstrainRim(sourceXY,linearSrgb);')>s.index('linearSrgb=iris26822ApplySingleOwnerFalseColor('):fail('rim correction illegally late')
# Mathematically mirror the GLSL source on deterministic one-dimensional scenes.
def bound(g,center,active=True,zoom=1.0):
 peak=g[center]
 if not active or zoom>1.00001 or peak<=.60 or center<3 or center>=len(g)-3:return peak
 limited=peak
 for side in (-1,1):
  b1=g[center+side];b2=g[center+2*side];d1=g[center-side];d2=g[center-2*side]
  plateau=max(b1,b2);dark=max(d1,d2);step=max(plateau-dark,0);plateauDelta=abs(b1-b2)
  if step>.15*max(plateau,.05) and plateauDelta<.075*max(plateau,.05) and peak>plateau+.006*max(peak,.05):
   limited=min(limited,plateau+.003*peak)
 return max(peak*.975,limited)
checks=0
for value in (.65,.80,.90,1.0,1.3):
 for dark in (.01,.07,.17,.32):
  sky=[dark]*16+[value]*16
  for pos in range(10,23):
   res=bound(sky,pos)
   if res!=sky[pos]:fail('unmodified step/sky plateau darkened')
   checks+=1
  # 1-pixel brightness overshoot exactly at bright side of thin tree edge
  g=sky.copy();g[16]=value*1.04
  correction=bound(g,16)
  if not (correction<g[16] and correction>=.975*g[16] and correction>value*.98):fail('overshoot not bounded without loss of real sky')
  if bound(g,16,False)!=g[16] or bound(g,16,True,1.2)!=g[16]:fail('A/A+B/high zoom route illegally changed')
  checks+=1
# Preserve original gainmap math: matched actual rendered SDR base remains the only denominator.
old=scope()[2]
p='app/src/main/assets/shaders/motionv2/gainmap.glsl'
if '--live' in sys.argv:
 gm=(R/p).read_text()
 if sha(R/p)!=old[p] or 'vec3 iris26641BilinearSdrLinear' not in gm or 'textureSize(SdrBuffer,0)' not in gm:fail('gainmap actual SDR denominator changed')
print('PASS 26952 limited high-contrast bright-side-only rim correction '+str(checks)+' 1D checks, unchanged SDR base gainmap authority')
