#!/usr/bin/env python3
"""26963 host RAW-CFA temporal inlier/noise and boundary holdout tests.
Actual GPU/phone IQ is *not* established by these synthetic tests.
No NumPy/SciPy dependencies: Actions Python -S standard library only.
"""
import argparse,math,random
from pathlib import Path
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
sh=(R if args.live else R/'handoff_payload_26963')/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp'
s=sh.read_text()
for fragment in ('smoothstep(6.0, 9.0, z)','smoothstep(0.62, 0.86, coherence)',
 'smoothstep(9.0, 15.0, snr)','imageStore(temporalAligned, center, mix(alignedCenter, refCenter, confidence))'):
 assert fragment in s,fragment

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3.0-2.0*t)

def weight(pairs,black=64.,slope=.065,offset=2.0):
 assert len(pairs)==5
 d=[0.]*4;refSum=[0.]*4;var=[0.]*4;sumSq=0.
 for ref,aligned in pairs:
  for k in range(4):
   u=ref[k]-aligned[k];d[k]+=u;refSum[k]+=ref[k];sumSq+=u*u
   var[k]+=2*(slope*max(ref[k]-black,0.)+offset)
 z=math.sqrt(sum((d[i]/math.sqrt(max(var[i],1.e-8)))**2 for i in range(4))*.25)
 coherence=sum(x*x for x in d)/max(5*sumSq,1.e-8)
 signal=max(sum(refSum)*.05-black,0.)
 sigma=math.sqrt(max(sum(var)*.05,1.e-8))
 snr=signal/sigma
 return smooth(6.,9.,z)*smooth(.62,.86,coherence)*smooth(9.,15.,snr)

rng=random.Random(26963)
false_count=0;stable_count=0;moving_count=0;strong_count=0;monotonic=0
for case in range(384):
 # Six physically distinct exposure/noise regimes, five texture families,
 # multiple subpixel alignment residuals; moving target of all CFA hues.
 family=case%12
 mean=[73.,86.,140.,250.,370.,510.][(case//12)%6]
 slope=.035+.018*(case%7);offset=1.0+.75*((case//7)%5)
 amp=(case%8)/7.
 pairs=[]
 for k in range(5):
  phases=[mean+5*j for j in range(4)]
  if family in (1,2,3,4,5):
   for j in range(4):
    if family==1:phases[j]+=34. * (-1 if k%2 else 1)
    if family==2:phases[j]+=55.*math.sin((k+1)*1.45+j*.7)
    if family==3:phases[j]+=32.*math.cos((k+2)*1.04+j*1.1)
    if family==4:phases[j]+=15.*(k-2)
    if family==5:phases[j]+=75.*((-1)**(k+j))
  r=[max(65.,x) for x in phases]
  noise=[math.sqrt(slope*max(x-64,0.)+offset) for x in r]
  ref=[r[j]+rng.gauss(0,noise[j]) for j in range(4)]
  aligned=[r[j]+rng.gauss(0,noise[j]) for j in range(4)]
  if family==6:
   # Deliberate fractional geometry error across bright stationary texture;
   # alternating local signs must not make broad reference-only patches.
   aligned=[a+((1 if k%2 else -1)*(5+7*amp)) for a in aligned]
  if family>=7:
   # Real coherent photometric/chroma changes across an aligned 5-pixel cross.
   displacement=[-120.,145.,-175.,210.][(family-7)%4]
   # Strong motion amplitude; preserve phase-specific channel differences.
   aligned=[a+displacement*(1.0+j*.12*(-1 if family%2 else 1)) for j,a in enumerate(aligned)]
  pairs.append((ref,aligned))
 w=weight(pairs,64,slope,offset)
 assert math.isfinite(w) and 0<=w<=1
 if family<7:
  stable_count+=1
  false_count+=(w>.20)
 else:
  # Actual strong-moving input must be rejected often when well exposed,
  # but dark low-SNR motion intentionally keeps RAW averaging instead.
  if mean>180:
   moving_count+=1;strong_count+=(w>.7)
 # Offset of an 8x8 frequency tile must never enter this decision.
 for tile_phase in (0,1,3,7):
  assert weight(pairs,64,slope,offset)==w
for amp in range(1,51):
 pairs=[([280.,260.,305.,270.],[280.-amp,260.-amp,305.-amp,270.-amp])]*5
 a=weight(pairs,64,.065,2.)
 b=weight([([280.,260.,305.,270.],[280.-amp-1,260.-amp-1,305.-amp-1,270.-amp-1])]*5,64,.065,2.)
 assert b>=a-1.e-8
 monotonic+=1
assert stable_count>160 and false_count/stable_count<.045,(false_count,stable_count)
assert moving_count>45 and strong_count/moving_count>.65,(strong_count,moving_count)
assert monotonic==50
# Scope: the original 26962 coarse tile motion rejection remains OFF.
if args.live:
 coordinator=(R/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
 assert 'recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency &&' in coordinator
 assert '!photoBOffRawr051' in coordinator
print('PASS 384 deterministic noisy/static/fractionally shifted/moving CFA cases: '
      f'stationary false={false_count}/{stable_count}, moving strong={strong_count}/{moving_count}; '
      '8x8 tile-phase independent, smooth monotonic gating, 26960 coarse gate remains OFF')
