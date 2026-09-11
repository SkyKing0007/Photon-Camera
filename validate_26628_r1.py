#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26628_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
CHANGED=[x.strip() for x in (Path(__file__).resolve().parent/'R1_26628_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def universe(root): return {str(p.relative_to(root)):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
b=universe(B); c=universe(C)
if len(b)!=1713 or len(c)!=1713: raise SystemExit(f'FAIL app universe count {len(b)} {len(c)}')
diff=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
if diff!=sorted(CHANGED): raise SystemExit(f'FAIL runtime changed-file allowlist: {diff}')
v=(C/'app/version.properties').read_text()
for t in ['VERSION_NAME=0.9726628','VERSION_BUILD=26628']:
    if t not in v: raise SystemExit(f'FAIL version token {t}')
# User-requested domain boundary: legacy Photon and all reconstruction/merge owners remain byte-identical.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
]
for rel in protected:
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL protected mode/reconstruction owner changed {rel}')
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
for tok in ['if(mParameters.irisNightActive){','add(new MotionV2ColorTransform());','add(new MotionV2AdaptiveColorAppearance());','if (mParameters.motionV2Active) {']:
    if tok not in post: raise SystemExit(f'FAIL Motion/Night active-path token missing {tok}')
image=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
for tok in ['parameters.motionV2SuperResOutputEnabled','MotionV2Jpeg444Encoder.writeTrue2x(']:
    if tok not in image: raise SystemExit(f'FAIL SuperRes-on publication gate missing {tok}')
# DNG-style solver contract. Equal ForwardMatrix anchors must be valid; no heuristic device/manufacturer rejection.
solver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java').read_text()
for tok in [
'IRIS_26628_BJZHOU_EQUIVALENT_JPEG_COLOR_SPEC','IRIS_26628_BJZHOU_DNG_COLOR_SOLVED',
'neutralToXy(profile, neutral)','matricesForWhite(profile, sceneXy)','normalizeColorMatrix','normalizeForwardMatrix',
'interpolateOptional(p.forward1, p.forward2, firstWeight)','individualToReference = invert(matrices.calibration)',
'referenceWhite = map(individualToReference, cameraWhite)','cameraToD50 = multiply(matrices.forward',
'cameraToD50 = invert(pcsToCamera)','secondAnchorWeight','BRADFORD','BRADFORD_INV','ROBERTSON_R',
]:
    if tok not in solver: raise SystemExit(f'FAIL DNG color-spec contract token {tok}')
for forbidden in ['IRIS_26627_DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT','forwardDelta <= 1.0e-6f','colorMatrixDelta >= 0.05f','Build.MANUFACTURER','Build.MODEL','Xiaomi','OnePlus','COLOR_CORRECTION_GAINS','RggbChannelVector']:
    if forbidden in solver: raise SystemExit(f'FAIL solver stale/device/double-WB authority {forbidden}')
# Selected sensor profile is frozen before inherited legacy ForwardMatrix substitutions; full Iris-only 3D tables are parallel to legacy tables.
params=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
for tok in [
'IRIS_26628_SELECTED_PROFILE_COLOR_INPUT','final ColorSpaceTransform irisForward1 = forwardt1;',
'IRIS_26628_MOTION_NIGHT_SR_DCP_PROFILE_OWNER','irisJpegHueSatMap','irisJpegHueSatMapSize = new int[]{0, 0, 0}',
'irisJpegLookMap','irisJpegLookMapSize = new int[]{0, 0, 0}','buildIrisJpegProfileMaps(solution.interpolationFactor)',
'IRIS_26628_MOTION_NIGHT_SR_COLOR_OWNER','profileEncoding=LINEAR','legacyPhotonColorUnchanged=true',
]:
    if tok not in params: raise SystemExit(f'FAIL Parameters color-owner token {tok}')
if params.find('final ColorSpaceTransform irisForward1 = forwardt1;') > params.find('// Check if forward matrices have each component non-zero'):
    raise SystemExit('FAIL selected Iris profile metadata frozen after legacy ForwardMatrix substitution')
for tok in ['public float[] HSVMap = null;','public float[] LookMap = null;']:
    if tok not in params: raise SystemExit(f'FAIL legacy Photon profile field missing {tok}')
# Motion/Night color node is mode-guarded and implements full DNG HSV tables; no global legacy path changes.
ctj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java').read_text()
for tok in [
'IRIS_26628_MOTION_NIGHT_DNG_PROFILE_COLOR_OWNER','motionV2Active || basePipeline.mParameters.irisNightActive',
'USE_PROFILE_HUESAT','USE_PROFILE_LOOK','irisJpegHueSatMap','irisJpegLookMap','GL_NEAREST',
'row=(value*hueDivisions+hue)','legacyPhotonColorAffected=false','negativeProfileExcursionMapBypass=true',
]:
    if tok not in ctj: raise SystemExit(f'FAIL Motion/Night color node contract {tok}')
cts=(C/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
for tok in [
'IRIS_26628_DNG_HSV_PROFILE_MAP','iris26628RgbToHsv','iris26628HsvToRgb','iris26628SampleMap','iris26628ApplyMap',
'value*hueDivisions+hue','modify.x*6.0/360.0','hsv.y=clamp(hsv.y*modify.y,0.0,1.0)',
'if(min(color.r,min(color.g,color.b))<0.0)return color;','if(negativeFloor<0.0)linearDisplay-=vec3(negativeFloor);',
]:
    if tok not in cts: raise SystemExit(f'FAIL DNG HSV shader contract {tok}')
# Restrained 26626-style appearance is a contraction only, not another adaptive color owner.
adj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java').read_text()
ads=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
for tok in ['IRIS_26628_PRESENTATION_CHROMA_SCALE','0.95f']:
    if tok not in adj: raise SystemExit(f'FAIL presentation Java contract {tok}')
for tok in ['IRIS_26628_RESTRAINED_COLOR_PRESENTATION','chroma*scale',
            'float negativeFloor=min(rgb.r,min(rgb.g,rgb.b));','if(negativeFloor<0.0)rgb-=vec3(negativeFloor);']:
    if tok not in ads: raise SystemExit(f'FAIL presentation shader contract {tok}')
if 'max(texelFetch(InputBuffer' in ads or 'Output=max(' in ads:
    raise SystemExit('FAIL restrained presentation per-channel clamp regression')
for forbidden in ['1.32','1.12','coherentColorActivation','gamutGainLimit','MAX_WEAK_CHROMA_GAIN']:
    if forbidden in ads: raise SystemExit(f'FAIL stale adaptive chroma authority {forbidden}')
# SuperRes ON/true2x receives the same matrices/profile tables and 0.95 contraction; profile tables forbid GPU omission.
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
nat=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['parameters.irisJpegHueSatMap','parameters.irisJpegLookMap','writeTrue2xNative(','sensorToProPhoto, profileToDisplay']:
    if tok not in enc: raise SystemExit(f'FAIL true2x Java shared color contract {tok}')
for tok in ['iris26628ApplyDcp','dcpHueSatMap','dcpLookMap','mul(c,0.95f)','c*0.95','p.dcpHueSatMap.empty()&&p.dcpLookMap.empty()','jin_watermark_or_dcp_profile']:
    if tok not in nat: raise SystemExit(f'FAIL true2x native color contract {tok}')
for forbidden in ['1.32f','1.22f']:
    if forbidden in nat: raise SystemExit(f'FAIL stale true2x adaptive color gain {forbidden}')
print('PASS 26628 semantic/ownership/domain: exact 9-path delta; Motion/Night/SuperRes-only bjzhou-equivalent DNG color; full 3D HSV profile tables; 0.95 contraction; legacy Photon and reconstruction protected')
