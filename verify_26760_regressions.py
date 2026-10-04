#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26760_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def read(root,rel): return (root/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
def same(rel): assert sha(base,rel)==sha(cand,rel),f'protected regression changed: {rel}'
shader_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
shader=read(cand,shader_rel); base_shader=read(base,shader_rel)
# All routing/evidence/VGN/publication owners remain byte-identical to successful 26759.
for rel in [
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/IrisZoomController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLPreview.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/MainRenderer.java',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
]:
 if (base/rel).is_file(): same(rel)
# Shader source may change ONLY in the live true2x Super Res guide resolver.
start='val true2xGuideRender26568 ='
end='    /* IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_OWNER'
a=shader.index(start); b=shader.index(end,a); ba=base_shader.index(start); bb=base_shader.index(end,ba)
assert shader[:a]+base_shader[ba:bb]+shader[b:]==base_shader,'shader source changed outside live true2x Super Res resolver'
# Ordinary >=1.1x zoom resolver is byte-identical to successful 26759.
zs='val highZoomDetailResolve26718: String by lazy'; ze='    private val outputTransformBody'
za=shader.index(zs); zb=shader.index(ze,za); zba=base_shader.index(zs); zbb=base_shader.index(ze,zba)
assert shader[za:zb]==base_shader[zba:zbb],'ordinary zoom detail resolver changed'
# 26759 confidence-gated luma detail/microcontrast remains unchanged in true2x.
for token in ['IRIS_26759_CONFIDENCE_GATED_DETAIL_REINFORCEMENT','float microcontrastGain=1.0+0.36*provenStructure','float combinedDetailGain=min(2.0,detailReinforcement*microcontrastGain)','clamp(targetY / guideY, 0.68, 1.47)']:
 assert token in shader,token
# Combined chroma contract: preserve inherited non-SR cleanup and add stronger Super-Res-only Lightroom-like strength 0.50.
seg=shader[a:b]
for token in ['IRIS_26760_SUPER_RES_CHROMA_DENOISE_50','chromaDenoise26760 = 0.50','0.90 * selectedMag26760','centerColor26760','coherentHue26760','materialBoundary','uNativeVgnGuide']:
 assert token in seg,token
assert shader.count('IRIS_26760_SUPER_RES_CHROMA_DENOISE_50')==1
assert 'IRIS_26760_SUPER_RES_CHROMA_DENOISE_50' not in shader[za:zb]
# Inherited non-Super-Res chroma cleanup from successful 26759 is mandatory and byte-identical.
shared = read(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
bridge = read(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for token in ['IRIS_26733_NEUTRAL_FLOOR_VETO','validNeutralConsensus','neutralFloorVeto']:
 assert token in shared,token
for token in ['IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE','(0.5f * chromaScale)','CUSTOM_EXACT','AUTO_SNR_HALF','!parameters.irisNightActive && customResidualChroma == null']:
 assert token in bridge,token
# Luma stays exact; direct CFA never becomes a chroma owner.
assert 'return vec3(bilinearY) + selectedChroma * clamp(nonNegativeScale, 0.0, 1.0);' in seg
assert 'No direct-CFA chroma enters.' in seg
# Inherited 26758 safety and 26759 gain protections remain.
for token in ['IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION','unsupportedRow','unsupportedCol','unsupportedChecker','aliasGate','highlightGate','temporalGate','phaseGate','agreementGate']:
 assert token in seg,token
# Version exact.
ver=read(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726760' in ver and 'VERSION_BUILD=26760' in ver
print('PASS 26760 regressions: combined chroma policy preserved — inherited non-SR neutral/fine-structure veto + Motion AUTO_SNR_HALF remain exact; Super Res adds 0.50 same-material chroma consensus; Custom Exact/Night/luma/detail/highlight/UHDR/DNG owners protected')
