#!/usr/bin/env python3
"""Synthetic bounded chroma model, not actual device GPU/color proof."""
import math
from pathlib import Path
import sys
P=Path(__file__).resolve().parent
shader=(P/'handoff_payload_26929' if '--payload' in sys.argv else P)/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp'
s=shader.read_text()
for token in ('localVar=mix(singleVar,singleVar/max(p.mergedFrames,2.0),confidence);',
  'float need=', 'float singleVar=', 'float yRestore=',
  'shift-=vec3(dot(shift,kLuma));','if(total>=3.2)',
  'max(source.rgb.r,max(source.rgb.g,source.rgb.b))<0.97',
  'supportedMicroColor','max(center[k],0.0)/max(-shift[k],1e-8)'):
 assert token in s,token
f=lambda a,b,x:(lambda t:t*t*(3-2*t))(max(0.,min(1.,(x-a)/(b-a))))
# For every confidence, the noise envelope stays between fully merged and
# reference only; it is NOT fabricated Neff or a new Camera2 profile.
for n in (2,8,15,24):
 for conf in [i/10 for i in range(11)]:
  v=.00002*.06+.000002
  full=v/n
  local=(1-conf)*v+conf*full
  assert full-1e-12<=local<=v+1e-12
  assert abs(local-(v if conf==0 else full if conf==1 else local))<1e-12
# In weighted RGB opponent coordinates, subtracting the weighted luma of
# a chroma correction has exactly zero effect on brightness for any colors.
w=(.25,.5,.25)
for delta in [(0.002,-.001,-.002),(.03,.01,-.05),(-.08,.04,.01)]:
 m=sum(a*b for a,b in zip(w,delta))
 d=[v-m for v in delta]
 assert abs(sum(a*b for a,b in zip(w,d)))<1e-12
# Coherent same-luma neutral donors and a modest isolated false tint allow
# bounded movement; saturated real colored microdetail with high confidence
# strongly reduces the gate, while low-confidence shadows gain treatment.
def amount(y,conf,delta,spread,sigma,total,chroma_mag):
 shadow=1-f(.075,.32,y)
 need=(.16+.84*(1-conf))*shadow
 floor=max(1.35*sigma,.018*max(y,.03))
 coherent=1-f(1.5*floor,3.5*floor,spread)
 suspect=f(.45*floor,1.65*floor,delta)*(1-f(3*floor,5.5*floor,delta))
 protected=f(.19,.44,chroma_mag/max(y,.035))*f(.35,.85,conf)
 return .52*need*coherent*suspect*(1-protected)*f(3.2,6.,total)
q=amount(.045,.15,.008,.001,.003,6,.005)
assert q>.02,q
assert amount(.045,.9,.008,.001,.003,6,.015)<q
assert amount(.4,.15,.008,.001,.003,6,.005)==0
assert amount(.045,.15,.008,.06,.003,6,.005)==0
assert amount(.045,.15,.008,.001,.003,2,.005)==0
assert amount(.045,.95,.008,.001,.003,6,.035)<.01
print('PASS 26929 synthetic confidence/noise envelope, Y-invariance, shadow outlier, real hue and no-donor cases; device IQ NOT RUN')
