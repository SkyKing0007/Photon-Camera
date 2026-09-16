#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26649_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r): return hashlib.sha256((base/r).read_bytes()).digest()==hashlib.sha256((cand/r).read_bytes()).digest()
# Permanent 26649 scope regressions: unrelated owners must remain byte-identical.
for r in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/cpp/iris_heic_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert same(r),r
j=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
g=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl').read_text()
r=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
rem=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
# Must never regress to the 26635 policy that lifts smooth highlights toward white after compression.
for forbidden in [
'float smoothShoulder=1.0-pow(max(1.0-baseLinear,0.0),1.12);',
'float smallResidualWeight=mix(1.0,0.78,upperGate);']:
 assert forbidden not in rem,forbidden
# Exact Photon law must exist in Java + both production shader carriers.
assert 'IRIS_26649_PHOTON_KNEE_MAX = 0.90f' in j
assert 'IRIS_26649_PHOTON_KNEE_MIN = 0.55f' in j
assert 'IRIS_26649_PHOTON_KNEE_REF = 0.10f' in j
assert j.count('return k + span * g * g;')==1
assert g.count('return knee+span*g*g;')==1
assert r.count('return knee+span*g*g;')==1
# No per-channel highlight curve or chroma mutation in the new owner.
for s in [g,r]:
 assert 'iris26649PhotonSoftShoulder(vec' not in s
# Version contract.
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726649' in v and 'VERSION_BUILD=26649' in v
print('PASS 26649 permanent regressions: SHORT/color/UHDR/HEIC/DNG/capture frozen; no post-compression bright-base lift; exact scalar Photon knee/shoulder retained')
