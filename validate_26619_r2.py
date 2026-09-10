#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26619_r2.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C)
assert len(bh)==1712 and len(ch)==1711,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted([
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_apply_26618.glsl',
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_gain_26618.glsl',
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_coeff_26618.glsl',
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_coeff_26619.glsl',
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_base_26619.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726619' in ver and 'VERSION_BUILD=26619' in ver
# Reconstruction, physical color, display-target and UHDR gain authority are not reopened.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),f'protected owner changed: {rel}'
# Final graph: display target/pass-through and optional manual controls precede the one guided decomposition,
# which sits immediately before the final renderer. No 26618 image-multiplying node remains.
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
motion=post.split('if (mParameters.motionV2Active) {',1)[1]
seq=['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());','IrisMotionSettings.Snapshot irisMotionSettings','add(new MotionV2GuidedBaseDetailLtm());','add(new MotionV2Render());']
pos=-1
for tok in seq:
    n=motion.find(tok,pos+1); assert n>pos,f'missing/out-of-order Motion graph token: {tok}'; pos=n
assert motion.count('add(new MotionV2GuidedBaseDetailLtm());')==1
assert 'MotionV2DisplayExposure,IrisManualOptional,MotionV2GuidedBaseDetailLtm,MotionV2Render' in motion
node=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java').read_text()
for tok in ['IRIS_26619_GUIDED_BASE_DETAIL_FINAL_COMPOSITION','MAP_LONG_EDGE = 256','MAP_MIN_EDGE = 48','ACTIVE_FINAL_GAIN = 1.05f',
            'guided_base_detail_ltm_coeff_26619','guided_base_detail_ltm_base_26619','motionV2GuidedBaseLogMap',
            'imageMutation=false','preRenderRgbGain=false','detailResidual=RECOMBINED_IN_FINAL_RENDER','true2xSharedField=true']:
    assert tok in node,tok
assert 'guided_base_detail_ltm_gain_26618' not in node and 'guided_base_detail_ltm_apply_26618' not in node
for retired in ['guided_base_detail_ltm_gain_26618.glsl','guided_base_detail_ltm_apply_26618.glsl','guided_base_detail_ltm_coeff_26618.glsl']:
    assert not (C/'app/src/main/assets/shaders/motionv2'/retired).exists(),retired
coeff=(C/'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_coeff_26619.glsl').read_text()
base=(C/'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_base_26619.glsl').read_text()
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for s in [coeff,base,render]: assert '#import' not in s
for tok in ['IRIS_26619_GUIDED_BASE_DETAIL_LTM_COEFFICIENTS','max(max(y, peak)','variance','0.0625']:
    assert tok in coeff,tok
for tok in ['IRIS_26619_GUIDED_BASE_DETAIL_LTM_BASE','guidedBaseLog','meanAb.x * logGuide + meanAb.y']:
    assert tok in base,tok
for tok in ['IRIS_26619_MONOTONIC_GUIDED_BASE_MAP','IRIS_26619_BROAD_BASE_WHITE = 0.86','IRIS_26619_DETAIL_LIMIT_STOPS = 2.0',
            'smoothstep(1.05,1.80,requestedFinalGain)','bodyGain=min(requestedFinalGain,4.0*broadWhite-1.0e-4)',
            'mappedBase*exp2(detailStops)','return rgb*(mappedGuide/guide)']:
    assert tok in render,tok
for forbidden in ['rgb * appliedGain','smoothstep(0.95, 1.05','guidedLtmGain','motionV2GuidedLtmGainMap']:
    assert forbidden not in '\n'.join([node,coeff,base,render]),forbidden
# Shared true-2x consumes the same base field and exact constants/equation, not a second solve.
params=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['motionV2GuidedBaseDetailApplied','motionV2GuidedBaseDetailWidth','motionV2GuidedBaseDetailHeight','motionV2GuidedBaseLogMap']:
    assert tok in params and tok in enc,tok
for tok in ['IRIS_26619_TRUE2X_SHARED_GUIDED_BASE_DETAIL','guidedBaseLog','guidedLtmWidth','guidedLtmHeight']:
    assert tok in enc,tok
for tok in ['iris26619GuidedBaseLogAt','IRIS_26619_TRUE2X_SHARED_GUIDED_BASE_DETAIL_GPU','IrisGuidedBaseLog','iris26619MapMotionBroadBase',
            'broadAnchor=0.86f','smooth01((requested-1.05f)/(1.80f-1.05f))','smoothstep(1.05,1.80,requested)','exp2(detailStops)']:
    assert tok in cpp,tok
for forbidden in ['smoothstep(0.95f,1.05f','smoothstep(0.95,1.05','guidedLtmGain']:
    assert forbidden not in cpp,forbidden
# No new scene semantic classifier or Photon implementation in the 26619-owned sources.
owned='\n'.join([node,coeff,base,render]).lower()
for forbidden in ['chandelier','curtain','bathroom','window classifier','local laplacian','autoexposurecurve','moderninitial','sharpen']:
    assert forbidden not in owned,f'forbidden semantic/legacy operation: {forbidden}'

# IRIS_26619_R2_NATIVE_NAMESPACE_COMPILE_REGRESSION
cpp_r2=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
assert 'float spatialStrength=iris26564::smooth01((requested-1.05f)/(1.80f-1.05f));' in cpp_r2
assert 'float spatialStrength=smooth01((requested-1.05f)/(1.80f-1.05f));' not in cpp_r2
print('PASS 26619 R2 semantic/ownership/domain validation + native namespace regression: exact 13-path delta; defective 26618 pre-tone gain retired; final guided base/detail owner shared by 1x/true2x')
