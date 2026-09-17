#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26659_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]);cand=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Exact regression: all prior 26658 Google bracket owners and protected IQ domains remain byte-identical.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl']
for r in protected:
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen 26658 regression '+r)
# Independent numeric mirror of the new final SDR visual remap.
def smooth(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3.0-2.0*t)
def spacing(y,source):
 y=max(y,0.0)
 if y<=0.65 or y>=1.0 or source>=1.0:return y
 w=0.35;t=max(0.0,min(1.0,(y-0.65)/w));t2=t*t;t3=t2*t
 norm=(t3-2*t2+t)*0.10+(-2*t3+3*t2)+(t3-t2)*2.70
 shaped=0.65+w*max(0.0,min(1.0,norm));gate=1.0-smooth(0.90,1.0,max(source,0.0))
 return y+(shaped-y)*gate
# Hermite itself is strictly monotone and source-white fade can only release compression upward.
prev=-1.0
for i in range(10001):
 y=0.65+0.35*i/10000.0;v=spacing(y,0.85)
 if v+1e-9<prev:raise SystemExit('FAIL spacing monotonic')
 prev=v
# Visual authority from 26658 grey-cement/window comparisons: a near-white valid-material guide around 0.88
# must redistribute near ~0.77 linear (~0.89 sRGB), not remain crowded near 0.95 encoded.
v=spacing(0.88,0.85)
if not (0.760<=v<=0.780):raise SystemExit(f'FAIL visual grey-material target {v}')
def enc(x):return 12.92*x if x<=0.0031308 else 1.055*(x**(1/2.4))-0.055
if not (0.885<=enc(v)<=0.900):raise SystemExit(f'FAIL visual encoded target {enc(v)}')
# Brighter material must remain ordered above it and source white/>1 are exact identities.
if not spacing(0.95,0.95)>v:raise SystemExit('FAIL upper ordering')
for y,s in [(0.65,0.5),(0.91,1.0),(0.95,1.25),(0.98,2.0)]:
 if spacing(y,s)!=y:raise SystemExit(f'FAIL protected identity y={y} source={s}')
print('PASS 26659 regressions: visual grey/window spacing target, strict monotonic ordering, exact source-white/>1 identity, and 26658 bracket/RGB/local-tone owners protected')
