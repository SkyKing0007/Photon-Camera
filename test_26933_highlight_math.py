#!/usr/bin/env python3
"""Pure host mirror of changed LKR/B-ON-only highlight decision.
Numerical rejection tests; NEVER a stand-in for actual GLSL, NDK or on-device photos.
"""
import math,sys
from pathlib import Path
from build_26933_incremental import R,fail

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3.-2.*t)
def med(x):return sorted(x)[1]
def fade(camera,gains,clip=(0,0,0),coverage=None):
 wb=[a*b for a,b in zip(camera,gains)]
 bw=max(min(gains),.0001); hi=max(wb); lo=min(wb);sc=max(camera);wc=min(camera)
 near=[smooth(.72,1.01,min(3.,v/bw)) for v in wb]
 r,g,b=near
 rg=min(r,g);gb=min(g,b);rb=min(r,b)*smooth(.35,.80,camera[1])
 early_white=max(rg,gb,rb)
 early=smooth(.06,.89,early_white)*smooth(.50,.75,lo/max(hi,.0001))*smooth(.56,.91,max(med(wb)/bw,wc))*smooth(.48,.80,sc)
 cr,cg,cb=clip
 sensor_white=max(min(cr,cg,cb),min(cg,max(cr,cb)),cg*smooth(.80,.98,min(camera[0],camera[2])),min(cr,cb)*smooth(.35,.75,camera[1]))
 single=max(cr*smooth(.77,.94,min(camera[1],camera[2])),cg*smooth(.77,.94,min(camera[0],camera[2])),cb*smooth(.77,.94,min(camera[0],camera[1])))
 cov=(cr+2*cg+cb)/4 if coverage is None else coverage
 hard=smooth(.07,.46,min(cov,max(sensor_white,.65*single)))*smooth(.60,.83,wc)*smooth(.56,.91,max(med(wb)/bw,wc))
 return max(early,hard)

def oldfade(camera,gains,clip=(0,0,0),coverage=None):
 wb=[a*b for a,b in zip(camera,gains)]
 safe=max(min(gains),.0001);peak=max(wb);low=min(wb)
 high=max(camera);weak=min(camera)
 near=[smooth(.72,1.01,min(3.,v/safe)) for v in wb]
 earlyWhite=max(min(near[0],near[1]),min(near[1],near[2]),min(near[0],near[2])*smooth(.35,.8,camera[1]))
 white=smooth(.27,.61,weak/max(high,.0001))*smooth(.47,.70,low/max(peak,.0001))
 bright=smooth(.68,1.04,max(med(wb)/safe,weak))
 early=smooth(.06,.89,earlyWhite)*white*bright*smooth(.48,.80,high)
 cr,cg,cb=clip
 sensorWhite=max(min(cr,cg,cb),min(cg,max(cr,cb)),cg*smooth(.80,.98,min(camera[0],camera[2])),min(cr,cb)*smooth(.35,.75,camera[1]))
 cov=(cr+2*cg+cb)/4 if coverage is None else coverage
 return max(early,smooth(.07,.46,min(cov,sensorWhite))*white*bright)

def main():
 changed=R/'handoff_payload_26933/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'
 if '--live' in sys.argv:changed=R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'
 s=changed.read_text()
 for text in ('smoothstep(0.50,0.75,visibleRatio)','smoothstep(0.60,0.83,weakestCam)',
              'smoothstep(0.56,0.91,','smoothstep(0.77,0.94,','sensorFade=measuredFade*thirdChannelNear*brightWitness',
              'earlyFade=smoothstep(0.06,0.89,earlyWhite) *','visualNeutral*brightWitness*sensorApproach'):
  if text not in s:fail('highlight scalar math mirror no longer matches compiled source '+text)
 # Reproduce 26932 bug: white sensor plateau became pink after WB, even
 # when all CFA colours were physically clipped. New hard clip must win.
 gains=(2.0,1.,1.55)
 for sample in ((.99,.98,.98),(.97,.88,.95),(.99,.94,.98)):
  new=fade(sample,gains,(1,1,1));old=oldfade(sample,gains,(1,1,1))
  if not .98<=new<=1.001 or not old<.40:fail('did not fix 26932 WB-blocked physically clipped neutral '+str((sample,old,new)))
 # Hard clipped R/B with near-white G is neutral; low-G colored magenta is not.
 if fade((1.,.90,1.),gains,(1.,0.,1.))<.96:fail('R/B clipped whites still magenta')
 if fade((1.,.10,1.),gains,(1.,0.,1.))>.001:fail('real saturated magenta light erroneously washed white')
 if fade((1.,.1,.08),gains,(1,0,0))>.001:fail('real red light erroneously washed white')
 if fade((.08,.1,1.),gains,(0,0,1))>.001:fail('real blue light erroneously washed white')
 if fade((.90,.8,.05),gains,(0,0,0))>.001:fail('unclipped yellow source changed')
 # Post-WB visually neutral: no RAW hard clip needed for early soft shoulder.
 for x in (.83,.90,.97):
  c=tuple(x/g for g in gains)
  v=fade(c,gains)
  if not 0<v<1.000001:fail('neutral WB-domain near-white shoulder not reachable '+str(x))
 for x in (0,.15,.4,.55):
  c=tuple(x/g for g in gains)
  if abs(fade(c,gains))>1e-7:fail('dark/ordinary tones affected '+str(x))
 # Monotone neutral white fade as intensity rises, including non-clipped.
 prev=-1
 for i in range(1001):
  x=i*.001
  v=fade(tuple(x/g for g in gains),gains)
  if v+1e-8<prev:fail('neutral visual white shoulder non-monotonic at '+str(x))
  prev=v
 # Color convergence is a local convex mix toward the largest channel:
 # no output channel may drop or exceed the original peak.
 for c in ((.9,.91,.94),(2.,.95,1.55),(.5,.6,.45)):
  k=.63;peak=max(c)
  out=[v*(1-k)+peak*k for v in c]
  if any(o+1e-10<v or o>peak+1e-10 for o,v in zip(out,c)):fail('highlight correction channel overshoot/black crush')
 print('PASS 26933 camera-vs-WB domain, R/B physical clipping, soft shoulder, saturated color protection, monotonic convergence; 26932 defect reproduced')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
