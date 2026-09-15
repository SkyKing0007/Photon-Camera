#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26641_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26641_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b,c=tree(base),tree(cand)
assert len(b)==len(c)==1717 and set(b)==set(c)
actual=sorted(k for k in b if b[k]!=c[k]); assert actual==sorted(changed),(actual,changed)
assert len(actual)==5
# Owners intentionally changed in 26641.
gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
glt=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java').read_text()
hevc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java').read_text()
ver=(cand/'app/version.properties').read_text()
# Matched UHDR intent: restore the full matched SDR-compressed delta exactly once.
for x in ['IRIS_26641_TRUE_MATCHED_SDR_HDR_INTENT_QUOTIENT','IRIS_26641_TRUE_MATCHED_INTENT_DELTA',
          'float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);','float hdrIntentY=sdr+matchedIntentDelta;',
          'ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);',
          'const float UHDR_OFFSET = 0.015625;']:
 assert x in gain,x
for stale in ['compressionFraction','const float hdrEntry=0.65','const float hdrFullEntry=0.85']:
 assert stale not in gain,stale
# Half-linear Motion map is pre-divide; Night branch stays on its inherited path.
for x in ['IRIS_26641_LINEAR_LIGHT_SDR_PREDIVIDE_DOWNSAMPLE','iris26641BilinearSdrLinear(sourcePixel)',
          'private static final int GAINMAP_DOWNSAMPLE = 2;','final int gainDownsample = iris26550Night ? 4 : GAINMAP_DOWNSAMPLE;',
          'matchedIntentPreDivideDownsample=']:
 assert x in gain+render,x
assert 'gainMapResamplingRequired=true' in render
# HEIC hardware bitstream color aspects mirror Android 16 HEIC Ultra-HDR intent.
for x in ['IRIS_26641_ANDROID16_HEIC_UHDR_HEVC_COLOR_ASPECTS','IRIS_26641_COLOR_STANDARD_DISPLAY_P3 = 10',
          'IRIS_26641_COLOR_TRANSFER_SRGB = 2','MediaFormat.KEY_COLOR_STANDARD','MediaFormat.KEY_COLOR_TRANSFER',
          'IRIS_26641_HW_HEVC_COLOR_ASPECTS']:
 assert x in hevc,x
# Shared GL: no object-name-as-unit/slot; dynamic generation-safe ownership and FBO namespace cleanup.
for stale in ['GL_TEXTURE1+mTextureID','GL_TEXTURE1 + mTextureID','ids[mTextureID]','glDeleteBuffers(1,new int[]{mBuffer}']:
 assert stale not in glt,stale
for x in ['IRIS_26641_SHARED_GL_TEXTURE_OWNERSHIP','Map<Integer, Long> liveTextureTokens',
          'mTrackingToken = registerTexture(mTextureID);','unregisterTexture(mTextureID, mTrackingToken)',
          'glGetIntegerv(GL_TEXTURE_BINDING_2D, previousBinding, 0);','glBindTexture(GL_TEXTURE_2D, previousBinding[0]);',
          'glDeleteFramebuffers(1,new int[]{mBuffer},0)']:
 assert x in glt,x
# Frozen prior owners remain present in protected bytes.
sabre=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for x in ['IRIS_26640_LOCAL_SHORT_PROPAGATION_SUPPORT','IRIS_26640_LOCAL_GEOMETRY_SAFE_COMPONENT_PROPAGATION']:
 assert x in sabre,x
jni=(cand/'app/src/main/cpp/iris_heic_jni.cpp').read_text()
assert 'heif_context_encode_gain_map_image' in jni
# Version convention inherited unchanged except name/build.
assert 'VERSION_MINOR=9726440' in ver and 'VERSION_NAME=0.9726641' in ver and 'VERSION_BUILD=26641' in ver
print('PASS 26641 semantics: true matched UHDR intent + Android16 HEVC color aspects + generation-safe shared GL + half-linear pre-divide gain map; exact 5-file scope')
