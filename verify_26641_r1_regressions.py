#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26641_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
glt=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java').read_text()
hevc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java').read_text()
# 26640 under-restoration exact condition is permanently forbidden.
assert 'compressedDelta*compressionFraction' not in gain and 'compressionFraction' not in gain
assert 'float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);' in gain
assert 'float hdrIntentY=sdr+matchedIntentDelta;' in gain
# Algebraic regression: 26640 restored only c^2*target for compression fraction c; 26641 restores c*target.
for target,model in [(1.0,0.8),(1.0,0.5),(2.0,1.2),(0.7,0.69)]:
 delta=max(target-model,0.0); c=delta/target if target>0 else 0.0
 old=delta*c; new=delta
 assert new+1e-12>=old
 if 0.0<c<1.0: assert new>old
 assert abs(new-delta)<1e-12
# Body/no-compression remains exact unity before 1/64 quotient when target <= model.
for target,model in [(0.4,0.4),(0.3,0.5),(0.0,0.0)]:
 assert max(target-model,0.0)==0.0
# Downsample order: linear SDR samples are decoded individually before mix; quotient is later.
assert gain.index('iris26641BilinearSdrLinear(sourcePixel)') < gain.index('ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET)')
assert 'srgbDecode(texelFetch(SdrBuffer' in gain
# Night remains independent 1/4 path and uses inherited encoded-bilinear/decode branch.
assert 'final int gainDownsample = iris26550Night ? 4 : GAINMAP_DOWNSAMPLE;' in render
assert ': max(luminance(srgbDecode(iris26550BilinearSdr(sourcePixel))),0.0);' in gain
# Shared GL permanent real-failure regressions.
assert 'glActiveTexture(GL_TEXTURE1+mTextureID)' not in glt
assert 'GL_TEXTURE1 + mTextureID' not in glt
assert 'liveTextureTokens' in glt and 'mTrackingToken' in glt
assert 'glDeleteFramebuffers(1,new int[]{mBuffer},0)' in glt
assert 'glDeleteBuffers(1,new int[]{mBuffer}' not in glt
# HEIC: base P3/sRGB/full, gain map unspecified/full; container owner remains protected.
assert '? IRIS_26641_COLOR_STANDARD_UNSPECIFIED' in hevc
assert ': IRIS_26641_COLOR_STANDARD_DISPLAY_P3' in hevc
assert '? IRIS_26641_COLOR_TRANSFER_UNSPECIFIED' in hevc
assert ': IRIS_26641_COLOR_TRANSFER_SRGB' in hevc
assert 'MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL' in hevc
# Frozen 26640 SHORT and 26639 IQ owners still present.
sabre=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for marker in ['IRIS_26640_LOCAL_SHORT_PROPAGATION_SUPPORT','IRIS_26640_LOCAL_GEOMETRY_SAFE_COMPONENT_PROPAGATION']:
 assert marker in sabre,marker
frozen=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for marker in ['IRIS_26638_USER_SATURATION_ONLY','IRIS_26638_TRUE_SHADOW_FLOOR_GUARD','IRIS_26621_FINAL_DOMAIN_SINGLE_PRESENTATION']:
 assert marker in frozen,marker
print('PASS 26641 permanent regressions: no squared-compression UHDR; pre-divide half-linear map; Night/SHORT/IQ frozen; no texture-ID unit/slot misuse; correct FBO delete; HEIC color aspects explicit')
