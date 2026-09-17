#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26660_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]);cand=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Exact regression: Google bracket and all protected IQ owners stay byte-identical to successful 26659 authority / 26658 lineage.
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
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen bracket/IQ regression '+r)
render=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
# Exact 26659 visual failure may never survive: the source-faded Hermite band created ground/foliage nonuniformity and a visible contour.
for stale in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING','iris26659BrightMaterialSpacing','const float startSlope=0.10;','const float endSlope=2.70;','smoothstep(0.90,1.0,max(sourceGuide']:
 if stale in render or stale in gain:raise SystemExit('FAIL 26659 contour mechanism survived '+stale)
# Independent mirror of 26660 analytic gamma. No spatial coordinate/source threshold participates.
GAMMA=2.50;POWER=6.0;WHITE=0.90
END_SLOPE=POWER*(WHITE-1.0)+WHITE*GAMMA
def curve(y):
 y=max(y,0.0)
 if y<=1.0:
  w=max(0.0,min(1.0,y))**POWER
  gm=WHITE*(max(y,1e-8)**GAMMA)
  return y+(gm-y)*w
 return WHITE+(y-1.0)*END_SLOPE
prev=-1.0
for i in range(20001):
 y=i/20000.0;v=curve(y)
 if not math.isfinite(v) or v+1e-10<prev:raise SystemExit(f'FAIL gamma monotonic y={y} v={v} prev={prev}')
 prev=v
# Body is effectively protected: no visible global gamma shift in normal midtones.
if abs(curve(0.50)-0.50)>0.006:raise SystemExit('FAIL body 0.50 changed too much')
if abs(curve(0.65)-0.65)>0.030:raise SystemExit('FAIL body 0.65 changed too much')
# Visual authority: the prior Iris near-white material (~0.88 linear model) should land close to Photon-like ~0.89 encoded,
# while remaining ordered and continuous through brighter material values.
def enc(x):return 12.92*x if x<=0.0031308 else 1.055*(x**(1/2.4))-0.055
v=curve(0.88)
if not (0.765<=v<=0.785):raise SystemExit(f'FAIL bright-material linear target {v}')
if not (0.888<=enc(v)<=0.900):raise SystemExit(f'FAIL bright-material encoded target {enc(v)}')
for a,b in [(0.75,0.80),(0.80,0.85),(0.85,0.90),(0.90,0.95),(0.95,1.0)]:
 if not curve(a)<curve(b):raise SystemExit(f'FAIL ordered material response {a} {b}')
# C1 continuation at 1.0, no source-domain fade seam.
eps=1e-5;left=(curve(1.0)-curve(1.0-eps))/eps;right=(curve(1.0+eps)-curve(1.0))/eps
if abs(left-right)>2e-3:raise SystemExit(f'FAIL gamma C1 white continuation left={left} right={right}')
# Production code must preserve chromaticity by one scalar and must not sample neighbors for the new correction.
for token in ['sourceRgb*(mappedGuide/sourceGuide)','mapped=rgb*(mappedGuide/guide)']:
 if token not in render:raise SystemExit('FAIL scalar RGB chromaticity proof '+token)
for token in ['textureOffset(','texelFetchOffset(','sourceGuide>=','smoothstep(0.90,1.0']:
 # These may occur elsewhere in shader for inherited functions, so restrict to new function body text.
 body=render.split('float iris26660ObjectColorGamma',1)[1].split('float mapFinalSdrGuide',1)[0]
 if token in body:raise SystemExit('FAIL new gamma has spatial/source threshold '+token)
# UHDR target remains exact 26658 pre-gamma local-structure target.
if 'sharedSdrGuide26658/globalSdrGuide' not in gain or '? sharedSdrGuide/globalSdrGuide : 1.0' in gain:raise SystemExit('FAIL UHDR 26658 target preservation')
print('PASS 26660 regressions: 26659 contour mechanism absent; analytic gamma monotone/C1; Photon-like bright-material target; scalar RGB chromaticity and exact 26658 UHDR HDR target preserved')
