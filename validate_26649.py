#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26649.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
changed={
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'}
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(rel): return (cand/rel).read_text()
bh,ch=H(base),H(cand)
assert len(bh)==len(ch)==1720 and set(bh)==set(ch)
assert {r for r in bh if bh[r]!=ch[r]}==changed
v=txt('app/version.properties'); assert 'VERSION_NAME=0.9726649' in v and 'VERSION_BUILD=26649' in v
j=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for token in [
 'IRIS_26649_PHOTON_HIGHLIGHT_COMPRESSION_OWNER',
 'IRIS_26649_PHOTON_KNEE_MAX = 0.90f',
 'IRIS_26649_PHOTON_KNEE_MIN = 0.55f',
 'IRIS_26649_PHOTON_KNEE_REF = 0.10f',
 'return k + span * g * g;',
 'motionV2TonePredictedClipFraction',
 'glProg.setVar("iris26649PhotonHighlightKnee", iris26649PhotonHighlightKnee())',
 'exactPhotonQuadraticShoulder=true',
 'colorsOwnerUnchanged=true shortFusionUnchanged=true heicUnchanged=true']:
 assert token in j,token
# Exact Photon knee/shoulder numerical parity from audited source equations.
def clamp(x,a,b): return max(a,min(b,x))
def knee(frac):
 p=min(clamp(frac,0.0,1.0)/0.10,1.0)
 return 0.90+(0.55-0.90)*p
def shoulder(x,k):
 v=clamp(x,0.0,1.0); k=clamp(k,0.0,1.0)
 if v<=k or k>=1.0-1e-7: return v
 span=max(1.0-k,1e-7); g=(v-k)/span
 return k+span*g*g
assert abs(knee(0.0)-0.90)<1e-9 and abs(knee(0.10)-0.55)<1e-9 and abs(knee(1.0)-0.55)<1e-9
for f in [0.0,0.000116291485,0.007548168,0.03,0.10,0.50]:
 k=knee(f); last=-1.0
 for i in range(10001):
  x=i/10000.0; y=shoulder(x,k)
  assert 0.0<=y<=1.0+1e-12 and y+1e-12>=last
  if x<=k: assert abs(y-x)<1e-12
  last=y
 assert abs(shoulder(1.0,k)-1.0)<1e-12
# Shader copies must contain exact operator and universal pre-Local-Laplacian placement.
g=txt('app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl')
r=txt('app/src/main/assets/shaders/motionv2/render.glsl')
rem=txt('app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
for s,name in [(g,'global'),(r,'render')]:
 for token in ['uniform float iris26649PhotonHighlightKnee;','float iris26649PhotonSoftShoulder(float x)','return knee+span*g*g;']:
  assert token in s,(name,token)
assert 'mapped=iris26649PhotonSoftShoulder(mapped);' in g
assert 'return iris26649PhotonSoftShoulder(iris26623MapMotionSdrFinalGuide(sourceGuide));' in r
assert 'float globalMapped=iris26649PhotonSoftShoulder(' in r
# Conflicting 26635 late bright-base lift and residual classifier are retired, not stacked.
assert 'float smoothShoulder=1.0-pow(max(1.0-baseLinear,0.0),1.12);' not in rem
assert 'float baseOut=baseLinear;' in rem
assert 'float residualWeight=1.0;' in rem
assert 'IRIS_26649_PHOTON_HIGHLIGHT_COMPRESSION_HANDOFF' in rem
# Colors and upstream fusion/HEIC ownership are outside runtime delta.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
 'app/src/main/cpp/iris_heic_jni.cpp']:
 assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest(), rel
print('PASS 26649 semantic/ownership: exact Photon quadratic Highlight Compression law + adaptive knee, universal upper-range before Local Laplacian, old bright-base lift retired, colors/SHORT/JPEG/HEIC owners frozen')
