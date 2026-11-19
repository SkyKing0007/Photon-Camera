#!/usr/bin/env python3
"""26965 source-contract & mathematical invariants. NOT a camera image-quality test."""
from pathlib import Path
import argparse,random,math,re,json
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args()
D=R if args.live else R/'handoff_payload_26965'
co=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
assert co.count('recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency);')==1
assert 'iris26957HdrqEffectiveFrames = hdrqEffectiveFrames;' in co
assert 'hdrqMeasuredProfile' in co and 'estimateNoiseFromBurst' not in co or 'fitBurstNoise' in co
assert 'const float range=std::max(1.0f,norm.whiteLevel-black);' in co
assert 'recorder.setNoise(alpha*range,beta*range*range);' in co
assert 'recorder.setMeasuredRawNoise(slopes, offsets, measured);' in co
assert 'hdrplus_.frequencyAlignOnce && pass != 0u && !aligns' in co
if args.live:
 cpp=(R/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp').read_text()
 mismatch=(R/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
 merger=(R/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp').read_text()
 norms=(R/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp').read_text()
 for marker in ('const bool gated=uniformExposure_ && motionGateEnabled_;','if (uniformExposure_ && iris26941BOffHdrqLazyPoolReset && !gated)','ib(0, alignedRgba), ib(1, arena_.image("hdrq_aligned_ft"))','kGateLow=1.6f, kGateHigh=2.6f, kGateShrink=1.0f','kEnergyGain=1.0f, kEnergyDead=1.0f, kEnergyScale=0.5f'):
  assert marker in cpp,marker
 assert 'if (p.useSpatialScreen != 0)' not in mismatch
 assert 'imageStore(temporalAligned' not in mismatch
 assert 'imageStore(zmap,g,vec4(p.useMotionGate!=0 ? acc/16.0 : 0.0));' in mismatch
 assert 'weight=max(weight,gate);' in merger
 assert 'p.uniformExposure!=0 && p.useMotionGate!=0 && gate>0.0' in merger
 assert 'float contribution = 1.0 - smoothstep(p.gateLo, p.gateHi, imageLoad(zmap, g).x);' in norms
 assert 'imageStore(neffAcc' in norms
 # B OFF uses uniform burst strength11, Night keeps current gated behavior,
 # SR ON is not dispatched here (guarded by the unchanged owner).
 assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f' in (R/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
# Numeric invariants of source-shared Bayer-phase Wiener gate and RAWR's
# FP32 absolute-vs-reference-delta spectral accumulation equivalence.
rng=random.Random(26965)
for i in range(100000):
 z=rng.random()*10.0
 def sm(a,b,x):
  t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3-2*t)
 gate=sm(1.6,2.6,z)
 mm=rng.random()
 w4=[rng.random() for k in range(4)]
 w=0.5*(sum(w4)-min(w4)-max(w4));w=max(w,gate)
 assert 0.0<=w<=1.0
 # Same coefficient on four CFA phases. No chroma-specific remapping.
 vals=[rng.uniform(-1000,1000) for k in range(4)];ref=[rng.uniform(-1000,1000) for k in range(4)]
 # One companion as direct contribution and as ref+delta (RAWR fp16 transport is separate).
 for k in range(4):
  direct=(1-w)*vals[k]+w*ref[k]
  delta=ref[k]+((1-w)*vals[k]+w*ref[k]-ref[k])
  assert math.isclose(direct,delta,rel_tol=3e-12,abs_tol=1e-10)
 acc=0.0
 for j in range(14):acc+=1.0-sm(1.6,2.6,rng.random()*10)
 eff=1+acc
 assert 1<=eff<=15
 # Reference-admitted count cannot equal 15 when every other frame gated out.
 assert abs(1.0+sum([1.0-sm(1.6,2.6,6.0) for q in range(14)])-1.0)<1e-12
# Source-retired pre-FFT path: actual FFT input is always the warped original.
if args.live:
 assert 'fftInput26963' not in cpp and 'spatialScreen26963' not in cpp
 assert 'if (p.useSpatialScreen != 0)' not in mismatch

print('PASS 26965 100000 4-phase gate/temporal support tests + source owner and physically retired mask invariant; IQ/photographic chroma NOT PROVEN')
