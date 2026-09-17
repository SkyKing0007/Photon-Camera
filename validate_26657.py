#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26657.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def req(c,m):
 if not c: raise SystemExit('FAIL '+m)
bh,ch=H(base),H(cand); req(len(bh)==len(ch)==1726,'app count')
allow={'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties'}
actual={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}; req(actual==allow,f'allowlist mismatch {sorted(actual^allow)}')
render_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
b=txt(base,render_rel); c=txt(cand,render_rel)
old='GLTexture out = new GLTexture(source.mSize, new GLFormat(GLFormat.DataType.FLOAT_16));'
new='GLTexture out = new GLTexture(source.mSize, new GLFormat(GLFormat.DataType.FLOAT_16, 4));'
req(b.count(old)==1 and new not in b,'successful 26656 red-carrier failure condition not exact')
req(c.count(new)==1 and old not in c,'26657 RGB carrier correction missing/non-unique')
req(c.replace(new,old,1)==b,'MotionV2Render delta is not exactly the one carrier-format correction')
# The constructor semantics prove why the old line was R16F.
glf=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java')
req(re.search(r'public GLFormat\(DataType format\)\s*\{\s*mFormat = format;\s*mChannels = 1;\s*\}',glf,re.S) is not None,'GLFormat single-argument channel semantics changed')
prep=txt(cand,'app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl')
req('out vec4 Output;' in prep,'Photon prepare no longer produces RGB/vec4 output')
req('boolean rgbInput = true;' in c and 'GLTexture next = iris26656PhotonDownsample(levelInput, rgbInput);' in c and 'rgbInput = false;' in c,'Photon LocalLaplacian RGB->scalar input-state contract changed')
# Intentional scalar luminance pyramid/log-map carriers remain scalar; only prepare output is RGBA16F.
req('GLTexture output = new GLTexture(size, new GLFormat(GLFormat.DataType.FLOAT_16));' in c,'intentional scalar downsample carrier changed')
req('GLFormat scalar = new GLFormat(GLFormat.DataType.FLOAT_16, 1);' in c,'intentional scalar log-luma carrier changed')
# Exact prior 26656 architecture remains active.
for t in ['IRIS_26656_PHOTON_NEW_PRESENTATION','iris26656PhotonPrepare','iris26656PhotonLocalLaplacian','iris26656PublishTrue2xToneMap','iris26656BuildMotionGainMap','IRIS_26656_PHOTON_NEW_FINAL']:
 req(t in c,'missing inherited 26656 presentation marker '+t)
for r in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/assets/shaders/motionv2/photon_new_precolor.glsl',
'app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl',
'app/src/main/assets/shaders/local_laplacian/downsample.glsl',
'app/src/main/assets/shaders/local_laplacian/reconstruct.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java']:
 req(bh[r]==ch[r],'protected successful-26656 owner changed '+r)
# Version change only.
bv=txt(base,'app/version.properties'); cv=txt(cand,'app/version.properties')
req('VERSION_NAME=0.9726656' in bv and 'VERSION_BUILD=26656' in bv,'base version authority')
req('VERSION_NAME=0.9726657' in cv and 'VERSION_BUILD=26657' in cv,'candidate version')
req(cv.replace('VERSION_NAME=0.9726657','VERSION_NAME=0.9726656').replace('VERSION_BUILD=26657','VERSION_BUILD=26656')==bv,'version.properties contains extra delta')
print('PASS 26657 semantic/ownership: exact successful 26656 authority; only Photon prepare carrier R16F->RGBA16F plus version; Photon exposure/tone/Laplacian/SR/UHDR/capture/Wronski/Iris color/denoise/DNG bytes protected')
