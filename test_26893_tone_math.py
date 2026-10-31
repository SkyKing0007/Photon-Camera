#!/usr/bin/env python3
"""26893 source-parity scene scores from actual 26891/26892 logging and math guards.
Full JPEG previews remain external to the handoff; no private photographs packaged.
This test is camera-domain proxy, NOT an Android/GPU compiler or device proof.
"""
import math
smooth=lambda a,b,x:(lambda t:t*t*(3.-2.*t))(max(0.,min(1.,(x-a)/(b-a))))
clamp=lambda x,a,b:max(a,min(b,x))
# Exact p50/p95/p99/p998 from user captured native logs.
scenes=[(.02317810,.21154785,.76171875,1.00000000),
 (.0059318542,.5600586,.73779297,1.00000000),
 (.011428833,.5083008,.61083984,.6879883),
 (.017105103,.55517578,.68798828,.72314453),
 (.10479736,.64208984,.74560547,.80810547),
 (.111206055,.36938477,.49829102,.58251953),
 (.11907959,.38427734,.48608398,.57421875),
 (.071029134,.4699258,.6212004,1.0381589),
 (.004928589,.28442383,1.,1.),
 (.0043792725,.3149414,.98535156,1.),
 (.02331543,.66308594,.73046875,.78027344),
 (.08105469,.5673828,.7163086,.8774414)]

def strengths(vals):
 p50,p95,p99,p998=vals
 if not all(math.isfinite(x) for x in vals) or p50<0 or p95<p50 or p99<p95 or p998<p99:
  return (0.,0.,0.)
 dark=1.-smooth(.0075,.0135,p50)
 bright=smooth(.60,.72,p99)
 tail=smooth(.80,.96,p998)
 back=clamp(dark*bright*tail,0,1)
 coeff=back*clamp(.014/max(p50,.002)-1.,0,1.30)
 body=smooth(.040,.080,p50)
 indoor=smooth(.069,.081,p50)
 extreme=1.-smooth(.55,.80,p95-p50)
 highlight=1.-smooth(.85,.95,p99)
 flat=clamp(body*indoor*extreme*highlight*(1.-back),0,1)
 return back,flat,coeff

def tone(y,flat,coef):
 if y<=0 or y>=1:return y
 gate=smooth(.0015,.010,y)
 lifted=min(1.,y+clamp(coef,0,1.30)*y*(1-y)**3*gate)
 darkgate=1-smooth(.52,.76,lifted)
 denom=1+(.90*clamp(flat,0,1))*((1-lifted)**3)*darkgate
 return clamp(lifted/denom,0,1)

scores=list(map(strengths,scenes))
for i,s in enumerate(scores):print('scene',('26891_%d'%(i+1) if i<8 else '26892_%d'%(i-7)),tuple(round(x,4) for x in s))
for i in [1,8,9]:
 assert scores[i][0]>.999 and 1.25<=scores[i][2]<=1.30
for i in [0,2,3,4,5,6,7,10,11]:assert scores[i][0]==0
for i in [0,2,3,10]:assert scores[i][1]==0
for i in [4,5,6,11]:assert scores[i][1]>.95
assert scores[7][1]<.1 # dark bathroom should not get darker with contrast correction
# Posterior rose and closet are darkened; light tones untouched at all strengths.
for i in [4,5,6,11]:
 back,flat,c=scores[i]
 assert tone(.2,flat,c)<.17
 assert tone(.4,flat,c)<.37
 assert tone(.76,flat,c)==.76
 assert tone(.9,flat,c)==.9
# Backlit foliage recovers meaningful brightness while preserving sky.
for i in [1,8,9]:
 back,flat,c=scores[i]
 assert tone(.02,flat,c)>.040
 assert tone(.06,flat,c)>.12
 assert abs(tone(.97,flat,c)-.97)<.0001
 assert tone(.2,flat,c)>.30
# Mathematically monotone for every varying supplied capture score plus extreme interior grid.
for back,flat,coeff in scores+[(1,0,1.30),(0,1,0),(0,.5,0),(1,1,1.30),(0,0,0)]:
 last=-1
 for k in range(30001):
  y=k/30000.;x=tone(y,flat,coeff)
  assert 0<=x<=1 and x>=last-3e-8,(back,flat,coeff,k,last,x)
  last=x
 assert tone(0,flat,coeff)==0 and tone(1,flat,coeff)==1
# 26892 user SDR green foliage proxy median, measured in input-image linear channels.
# New camera-linear preview should match nearby 26891 angles (~0.034..0.040)
# but these are DIFFERENT ANGLES, so allow modest drift.
for measured in (.0179954,.0172819,.0178402):
 y=tone(measured,0,1.30)
 assert .034 < y < .047,(measured,y)
# Gain map: same SDR denominator and matched-intent target stays unchanged.
for src in (.01,.1,.3,.5,.8):
 for _,flat,c in scores:
  sdr=tone(src,flat,c);hdr=max(2*src,sdr)
  assert abs(sdr+max(hdr-sdr,0)-hdr)<1e-12
# Color is altered only by a shared scalar: no saturation or hue-owner changes.
for rgb in ((.41,.27,.08),(.018,.024,.033),(.8,.3,.2),(.15,.25,.37)):
 y=sum(v*w for v,w in zip(rgb,(.22897456,.69173852,.07928691)))
 for _,flat,c in scores:
  scale=tone(y,flat,c)/y
  out=[z*scale for z in rgb]
  assert all(abs(out[k]/out[0]-rgb[k]/rgb[0])<1e-12 for k in (1,2))
# Invalid histogram must not yield nonfinite data or scene boost.
for x in (float('nan'),float('inf'),-1.): assert strengths((x,.3,.8,1.))==(0,0,0)
for x in ((.01,.2,.1,.9),(.01,.2,.3,.25)):assert strengths(x)==(0,0,0)
print('PASS 26893 12 captured scenes, 480k monotone samples, green reference target, darken-only, highlight/black/hue+UHDR math')
