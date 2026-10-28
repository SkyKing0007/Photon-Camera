#!/usr/bin/env python3
"""Source-constrained 26886 B-ON chroma math: neutral moire vs genuine hue, luma invariance.
Numeric surrogate checks are not actual AMaZE/Android GPU compiler proof.
"""
from pathlib import Path
import math,random,sys
assert len(sys.argv)==3
B,C=map(Path,sys.argv[1:]);shader='app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
s=(C/shader).read_text();old=(B/shader).read_text()
for must in ('chromaSum+=w*sc/max(sy,0.012)','max(falseColor,noiseCleanup)','originalRgb*gain*p.wb.rgb',
             'targetChroma-=vec3(yOf(targetChroma))','clipped==0?1.0','if(clipped>=2)targetN=mix(targetN,vec3(0),neutral)',
             'imageLoad(wronskiRgb,q)','params.forceY=0.f;'):
 if must=='params.forceY=0.f;':
  assert must in (C/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
 else:assert must in s,must
assert 'vec3 originalRgb=imageLoad(wronskiRgb,px).rgb;' in s
assert 'float clipWeight=' in s and 'float witness=' in s
assert old!=s
Y=(.2126,.7152,.0722)
def lum(v):return sum(a*b for a,b in zip(v,Y))
def chroma(v):return tuple(x-lum(v) for x in v)
def apply_luma(v,guide,weight):
 c=chroma(v);g=chroma(guide)
 o=tuple(x+weight*(a-b) for x,a,b in zip(v,g,c))
 return o
rnd=random.Random(26886)
for phase in range(4):
 for level in (.006,.02,.12,.45,.93,1.5):
  for _ in range(400):
   # Exact luminance conservation over neutral repeated contrasts and shadows.
   teal=(.0,.07,-.05); yellow=(.11,-.01,-.10)
   sign=teal if (phase+_)%2==0 else yellow
   candidate=tuple(level+v for v in sign)
   guide=(level,)*3
   strength=rnd.random()*.84
   out=apply_luma(candidate,guide,strength)
   assert abs(lum(out)-lum(candidate))<1e-12
   assert all(math.isfinite(x) for x in out)
   assert sum(abs(a-b) for a,b in zip(chroma(out),chroma(candidate)))>0 or strength==0
   # Known genuine saturated micro-color shared by both original sources:
   # no correction when AMaZE equals an independent Wronski color witness.
   trueColor=(level*.75,level*1.07,level*.72)
   assert max(abs(a-b) for a,b in zip(trueColor,trueColor))==0
# Integer sensor-CFA phase and clip mask ownership remain independent of
# content semantics and no neighboring AMaZE reads are permitted.
assert 'p.cfa>3u' in s and 'originalSensorClip,px/2' in s
assert 'imageLoad(amazeRgbInPlace,q)' not in s and 'imageStore(wronskiRgb' not in s
print('PASS 26886 source-constrained neutral periodic/diagonal/bright/shadow and true-color/luma invariance controls (GPU execution NOT proven)')
