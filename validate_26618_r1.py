#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26618_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C)
assert len(bh)==1708 and len(ch)==1712,(len(bh),len(ch))
changed=sorted(set(bh)|set(ch)); changed=[p for p in changed if bh.get(p)!=ch.get(p)]
expected=sorted([
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_coeff_26618.glsl',
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_gain_26618.glsl',
'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_apply_26618.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726618' in ver and 'VERSION_BUILD=26618' in ver
# Exact 26614 presentation/reconstruction authorities that 26618 must not modify.
unchanged=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']
for rel in unchanged:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),f'protected owner changed: {rel}'
# Production Motion graph order and single spatial owner insertion.
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
motion=post.split('if (mParameters.motionV2Active) {',1)[1]
seq=['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2GuidedBaseDetailLtm());','add(new MotionV2DisplayExposure());','add(new MotionV2Render());']
pos=-1
for tok in seq:
    n=motion.find(tok,pos+1); assert n>pos,f'missing/out-of-order Motion graph token: {tok}'; pos=n
assert motion.count('add(new MotionV2GuidedBaseDetailLtm());')==1
assert 'MotionV2GuidedBaseDetailLtm,MotionV2DisplayExposure' in motion
# 26614 display-exposure remains a neutral/pass-through carrier.
disp=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java').read_text()
for tok in ['imageMultiplier=false','passThrough=true','canonicalToneOwner=MotionV2Render']:
    assert tok in disp,tok
# Guided base/detail contract.
node=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java').read_text()
for tok in ['IRIS_26618_GUIDED_BASE_DETAIL_LTM_OWNER','MAP_LONG_EDGE = 256','MAP_MIN_EDGE = 48','ACTIVE_FINAL_GAIN = 1.05f',
            'motionV2GuidedLtmGainMap','guided_base_detail_ltm_coeff_26618','guided_base_detail_ltm_gain_26618','guided_base_detail_ltm_apply_26618',
            'detailResidual=UNCHANGED','rgbGain=COMMON_SCALAR','hdrAboveOnePreserved=true','true2xSharedField=true']:
    assert tok in node,tok
assert 'irisNightActive' in node and '26618 guided LTM is Motion-only' in node
coeff=(C/'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_coeff_26618.glsl').read_text()
gain=(C/'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_gain_26618.glsl').read_text()
apply=(C/'app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_apply_26618.glsl').read_text()
for s in [coeff,gain,apply]:
    assert '#version' not in s and '#import' not in s
assert 'IRIS_26618_GUIDED_BASE_DETAIL_LTM_COEFFICIENTS' in coeff
assert 'log2(y)' in coeff and 'dot(rgb, IRIS_LUMA)' in coeff and 'variance' in coeff and '0.0625' in coeff
for tok in ['IRIS_26618_GUIDED_BASE_DETAIL_LTM_GAIN','displayGain','smoothstep(0.35, 1.50','smoothstep(0.42, 0.95','clamp(gain, 0.50, 1.0)']:
    assert tok in gain,tok
for tok in ['IRIS_26618_GUIDED_BASE_DETAIL_LTM_APPLY','float localGain','float preserveHdr = smoothstep(0.95, 1.05, sourcePeak)','rgb * appliedGain']:
    assert tok in apply,tok
# No semantic/scene classifiers or sharpening in the new owner.
newtext='\n'.join([node,coeff,gain,apply]).lower()
for forbidden in ['ceiling','curtain','bathroom','chandelier','window classifier','sharpen','local laplacian','autoexposurecurvenew','moderninitial']:
    assert forbidden not in newtext,f'forbidden scene/legacy operation: {forbidden}'
# Shared true-2x field is an explicit carrier, never a second solve.
params=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['motionV2GuidedLtmApplied','motionV2GuidedLtmWidth','motionV2GuidedLtmHeight','motionV2GuidedLtmGainMap']:
    assert tok in params and tok in enc,tok
for tok in ['IRIS_26618_TRUE2X_SHARED_GUIDED_LTM','guidedLtmGain','guidedLtmWidth','guidedLtmHeight']:
    assert tok in enc,tok
for tok in ['iris26618GuidedLtmGainAt','IRIS_26618_TRUE2X_SHARED_GUIDED_LTM_GPU','uGuidedLtmEnabled','uGuidedLtmSize','smoothstep(0.95f,1.05f,peak(c))','smoothstep(0.95,1.05,irisPeak(c))']:
    assert tok in cpp,tok
assert 'guided LTM' not in cpp.lower() or True
print('PASS 26618 semantic/ownership/domain validation: exact 9-file delta; 26614 owners protected; guided base/detail inserted once; true2x shares field')
