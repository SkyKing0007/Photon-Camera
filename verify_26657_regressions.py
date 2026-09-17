#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26657_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def req(c,m):
 if not c: raise SystemExit('FAIL '+m)
def same(r): return hashlib.sha256((base/r).read_bytes()).digest()==hashlib.sha256((cand/r).read_bytes()).digest()
rr='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
b=(base/rr).read_text(); c=(cand/rr).read_text()
old='GLTexture out = new GLTexture(source.mSize, new GLFormat(GLFormat.DataType.FLOAT_16));'
new='GLTexture out = new GLTexture(source.mSize, new GLFormat(GLFormat.DataType.FLOAT_16, 4));'
# Exact field failure from 26656 must be represented and permanently rejected.
req(b.count(old)==1,'26656 red-only failure condition not represented in authority')
req(c.count(new)==1 and old not in c,'RGB-producing Photon prepare still uses one-channel carrier')
req(c.replace(new,old,1)==b,'carrier fix contains unrelated MotionV2Render edits')
glf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java').read_text()
req('mChannels = 1;' in glf,'single-argument GLFormat semantics unexpectedly changed')
prep=(cand/'app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl').read_text(); down=(cand/'app/src/main/assets/shaders/local_laplacian/downsample.glsl').read_text()
req('out vec4 Output;' in prep,'Photon prepare output ceased to be RGB/vec4')
req('boolean rgbInput = true;' in c and 'GLTexture next = iris26656PhotonDownsample(levelInput, rgbInput);' in c and 'rgbInput = false;' in c,'LocalLaplacian RGB-first/scalar-later contract changed')
# Parse destination channels: permanent >=3 rule for RGB stage.
m=re.search(r'GLTexture out = new GLTexture\(source\.mSize, new GLFormat\(GLFormat\.DataType\.FLOAT_16,\s*(\d+)\)\);',c)
req(m is not None and int(m.group(1))>=3,'Photon-New RGB producer destination has <3 channels')
# Scalar-only allocations are still intentionally scalar; do not "fix" them into RGB.
req('GLTexture output = new GLTexture(size, new GLFormat(GLFormat.DataType.FLOAT_16));' in c,'LocalLaplacian scalar downsample carrier altered')
req('GLFormat scalar = new GLFormat(GLFormat.DataType.FLOAT_16, 1);' in c,'true2x shared log-luma carrier altered')
# Everything that computes exposure/tone/color/SR/UHDR remains successful-26656 bytes.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/assets/shaders/motionv2/photon_new_precolor.glsl',
'app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl',
'app/src/main/assets/shaders/local_laplacian/downsample.glsl',
'app/src/main/assets/shaders/local_laplacian/reconstruct.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']
for r in protected: req(same(r),'successful-26656 protected owner changed '+r)
# No stale 26655 B+R / Iris display owner should regain Motion ownership.
for t in ['oldIrisDisplayGain=false old26655BPlusR=false old26623Tone=false','irisColor=true irisSaturation=true']:
 req(t in c,'inherited Photon-New ownership marker missing '+t)
print('PASS 26657 permanent regressions: 26656 red-only R16F carrier exactly reproduced in base and eliminated by explicit RGBA16F; RGB consumer compatibility >=3 channels enforced; exposure/tone/color/SR/UHDR/capture/Wronski owners byte-identical')
