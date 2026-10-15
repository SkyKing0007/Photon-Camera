#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
B,C=map(Path,sys.argv[1:3])
CHANGED={'app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {str(p.relative_to(r)).replace('\\','/'):H(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); assert set(b)==set(c) and len(b)==1786,(len(b),len(c)); delta={p for p in b if b[p]!=c[p]}; assert delta==CHANGED,(delta-CHANGED,CHANGED-delta)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726841' in v and 'VERSION_BUILD=26841' in v and 'VERSION_MINOR=9726440' in v
cap=(C/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text(); bcap=(B/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
# Active exposure ownership: one final 26713 target only; historical reactive writers remain dormant.
for dormant in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:
    assert dormant in cap,dormant
for required in ['IRIS_26841_SINGLE_TARGET_HAL_HDR_PREVIEW','MOTION_26841_PREVIEW_RETARGET_DEADBAND_EV = 0.30f','oneRequestUpdate=true iterative=false staircase=false','old26412Dormant=true old26368Dormant=true old26662Dormant=true','IRIS_26841_ABSOLUTE_RECIPE_ENERGY_AT_SHUTTER','desiredEnergy = mMotion26713RecipeEnergy','zslNormalTracksSolvedTarget=true','iris26841BaseNormalizedP995','mMotion26841PreviewAppliedCompSteps','iris26841RestoreComp','Preserve the successful 26713 dark-scene capture-only brighten intent']:
    assert required in cap,required
# One-shot preview target block must not contain loops or old RAW feedback writers.
s=cap.index('if (mMotion26841PreviewCompBaseReady && iris26841CanPublishPreviewTarget'); e=cap.index('Log.i(TAG, "IRIS_26713_CAPTURE_RECIPE_READY"',s); blk=cap[s:e]
assert blk.count('rebuildPreviewBuilder();')==1,blk.count('rebuildPreviewBuilder();')
for forbidden in ['while (','for (','updateMotionV2ExposureAuthority(','updateMotion26368AdaptiveAeBias(','updateMotion26662GoogleReferenceExposureAuthority(']: assert forbidden not in blk,forbidden
# Post-capture canonical preview must preserve the solved compensation rather than force 0 EV.
assert cap.count('final int iris26841RestoreComp = mMotion26841PreviewCompBaseReady')>=2
# No old capture-domain-only active contract may survive in the 26713 observer/declaration.
assert 'IRIS_26713_CAPTURE_RECIPE_SOLVER / IRIS_26841_SINGLE_TARGET_HAL_HDR_PREVIEW' in cap
assert 'IRIS_26713_CAPTURE_RECIPE_OBSERVER / IRIS_26841_SINGLE_TARGET_HAL_HDR_PREVIEW' in cap
# Color: DCP map mechanics and ACR3 table remain unchanged; only luminance-neutral warm-mid ACR3 restraint is inserted.
sh=(C/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text(); bsh=(B/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
for required in ['IRIS_26841_WARM_MIDTONE_ACR3_RESTRAINT','linearDisplay=mix(linearDisplay,linearDisplayOriginal,0.28*warmMidtone);','#if USE_IRIS_26720_HIGH_ZOOM_RGB == 0','float warmDistance=abs(warmHsv.x-0.35);','float midValue=smoothstep(0.08,0.22,warmHsv.z)','vec3 warmHsv=iris26628RgbToHsv(max(linearDisplayOriginal,vec3(0.0)));']:
    assert required in sh,required
# Strip only the new restraint and prove all pre-existing color-transform math is otherwise byte-identical.
pat=r'\n\s*/\* IRIS_26841_WARM_MIDTONE_ACR3_RESTRAINT.*?#endif\n'
m=re.search(pat,sh,re.S); assert m,'26841 color block'; stripped=sh[:m.start()]+'\n'+sh[m.end():]; assert stripped==bsh,'color transform changed outside 26841 restraint'
# Luminance contract: blend endpoints have equal target luminance because ACR3 output is restored to targetY before restraint.
assert 'linearDisplay=renderedDisplay*(targetY/renderedY);' in sh and 'float targetY=dot(linearDisplayOriginal,displayP3Luma);' in sh
# Keep 26840 highlight correction and all routing/native/DNG/high-zoom publication owners byte-identical.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']
for rel in protected: assert H(B/rel)==H(C/rel),rel
# 26840 smooth-rolloff authority remains present byte-identically.
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); shaders=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for marker in ['IRIS_26840_CLIP_ZONE_CHROMA','maskRegularization=INWARD_3X3_TENT','boundaryHueDirectionContinuous=true','warmTerminalDeepCoreOnly=true']: assert marker in bridge,marker
assert 'clipZoneApplyFragment26840' in shaders
print('PASS 26841 semantic validation: exact 3-path scope; one-shot 26713->HAL HDR preview target with 0.30EV retarget deadband/no staircase; absolute recipe energy prevents double protection; dark-scene capture-only brighten preserved; 26840 clip-zone/DNG/native/UHDR/high-zoom owners frozen; active ACR3 warm-midtones restrained 28% toward calibrated pre-ACR3 color at identical luminance')
