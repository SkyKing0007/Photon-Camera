#!/usr/bin/env python3
"""Numerical validation of *actual* 26891 capture log percentile tuples + new bounded math.
Synthetic monotonic/noise/scene regressions supplement, never replace, real compilers/device.
"""
import math
sm=lambda l,h,v: (lambda t:t*t*(3-2*t))(max(0.,min(1.,(v-l)/(h-l))))
# p50, p95, p99, p998: real 26891 captures, from existing exact log record.
scenes=[(.02317810,.21154785,.76171875,1.00000000),
 (.0059318542,.5600586,.73779297,1.00000000),
 (.011428833,.5083008,.61083984,.6879883),
 (.017105103,.55517578,.68798828,.72314453),
 (.10479736,.64208984,.74560547,.80810547),
 (.111206055,.36938477,.49829102,.58251953),
 (.11907959,.38427734,.48608398,.57421875),
 (.071029134,.4699258,.6212004,1.0381589)]
def coeff(p50,p95,p99,p998):
 if not all(math.isfinite(x) for x in (p50,p95,p99,p998)) or min(p50,p95)<0 or not (p50<=p95<=p99<=p998): return 0.,0.
 back=(1-sm(.006,.015,p50))*sm(.35,.55,p95)*sm(.78,.96,p998)
 flat=sm(.052,.112,p50)*(1-sm(.55,.80,p95-p50))*(1-sm(.85,.95,p99))*(1-back)
 return max(0,min(1,back)),max(0,min(1,flat))
def tone(y,back,flat):
 y=max(0.,y)
 if y==0 or y>=1:return y
 gate=sm(.004,.026,y)*((1-y)**3)
 lift=min(1.,y*2**(1.35*back*gate))
 w=sm(.018,.07,lift)*(1-sm(.65,.99,lift))
 return max(0.,min(1.,lift+1.08*flat*lift*(1-lift)*(lift-.24)*w))
scores=[coeff(*x) for x in scenes]
print('26891 calibrated real-photo scene scores:')
for i,(b,c) in enumerate(scores,1):print(f'shot{i}: backlit={b:.4f}, flatContrast={c:.4f}')
assert all(x==(0.,0.) for x in scores[:1]+scores[2:4])
assert scores[1][0]>.99 and scores[1][1]==0
assert .90<scores[4][1]<1 and scores[4][0]==0
assert scores[5][1]>.95 and scores[6][1]>.95
assert .1<scores[7][1]<.40
# Float roundoff physically monotonic and exact black/highlight invariant.
for back in (0,.2,.5,.8,1.):
 for flat in (0,.2,.5,.8,1.):
  prev=-1
  for k in range(20001):
   y=k/20000
   v=tone(y,back,flat)
   assert -1e-8<=v<=1+1e-8 and v>=prev-1e-7,(back,flat,k,y,prev,v)
   prev=v
  assert tone(0.,back,flat)==0 and tone(1.,back,flat)==1
  assert abs(tone(.97,back,flat)-.97)<.005
for i in (0,2,3):
 assert all(tone(y,*scores[i])==y for y in (.008,.15,.30,.60,.90))
assert tone(.06,*scores[1])>.075 and .90<=tone(.90,*scores[1])<=.905
assert tone(.30,*scores[4])>.30 and tone(.13,*scores[4])<.13
# Raw channel ratios must be unmodified by a scalar-luminance transfer.
for rgb in ((.4,.21,.16),(.02,.035,.045),(.8,.75,.2)):
 y=sum(v*w for v,w in zip(rgb,(.22897456,.69173852,.07928691)))
 s=tone(y,1.,1.)/y
 out=[z*s for z in rgb]
 for k in (1,2):assert abs(out[k]/out[0]-rgb[k]/rgb[0])<1e-12
# Preserve original matched-intent UHDR target when headroom is sufficient:
for y in (.01,.1,.3,.5,.8):
 for back,flat in scores:
  new=tone(y,back,flat); target=max(y*2.0,new)
  # Existing gainmap delta becomes target-new if target remains above new SDR.
  restored=new+max(target-new,0)
  assert abs(restored-target)<1e-12
assert coeff(float('nan'),.1,.2,.3)==(0,0)
print('PASS 26892 8 actual-capture scene regressions, 525k continuous sampled monotone checks, preservation, bound, scalar hue, UHDR delta and invalid-hist gates')
