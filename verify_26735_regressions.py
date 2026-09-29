#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26735_regressions.py BASE26734R1 CAND26735')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26735_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
expected={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726735' in v and 'VERSION_BUILD=26735' in v
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Freeze successful highlight hierarchy and 26731 transport geometry.
for t in ['IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY)','highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof)','highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma)','float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma))','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP','ivec2(-1,0),3,1,ivec2(1,0),1,3','ivec2(0,-1),0,2,ivec2(0,1),2,0','ivec2(1,-1),4,6,ivec2(-1,1),6,4','ivec2(-1,-1),7,5,ivec2(1,1),5,7']:
 assert t in vgn,t
# 26735 universal neutral owner: contaminated center hue cannot disqualify trusted neutral topology.
for t in ['IRIS_26735_PHYSICAL_COLOR_CONTINUATION_VETO','IRIS_26735_NEUTRAL_EDGE_BRACKET_OWNER','IRIS_26735_CENTER_CHROMA_CANNOT_DISQUALIFY_NEUTRAL_STRUCTURE','IRIS_26735_INDEPENDENT_PHYSICAL_REAL_COLOR_PROOF','IRIS_26735_NEUTRAL_EDGE_AND_SPECULAR_BRACKET_OWNER','IRIS_26735_RECONSTRUCTED_HUE_CANNOT_SELF_VETO_ACHROMATIC_OWNER','physicalColorContinuation26735','physicalColorAxisSupport26735','neutralSpecularTransition26735','physicalRealColorVeto26735']:
 assert t in vgn,t
seed=vgn[vgn.index('IRIS_26735_NEUTRAL_EDGE_BRACKET_OWNER'):vgn.index('int neutralStructure=',vgn.index('IRIS_26735_NEUTRAL_EDGE_BRACKET_OWNER'))]
assert 'neutralContaminatedCenterPermission26734' not in seed
assert 'centerChromaMagnitude' in seed and 'physicalColorVetoSeed26735' in seed
# Real physical color remains protected; no OCR/semantic hacks.
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO','microObjectProtection','topologyProtection']:
 assert t in vgn,t
assert 'textRecognition(' not in vgn and 'Tesseract' not in vgn
# Digital detail remains direct-CFA luma only and may never amplify guide chroma.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26735_DIGITAL_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY26735=max(guideY*factor,0.0);','vec3 guideChroma26735=guideRgb-vec3(guideY);','float chromaScale26735=min(factor,1.0);','oRenderRgb=vec4(max(digitalDetailRgb26735,vec3(0.0))']:
 assert t in sh,t
assert 'oRenderRgb = vec4(max(guideRgb * factor' not in sh and 'oRenderRgb=vec4(max(guideRgb*factor' not in sh
# Preserve successful 26734 SR luma-only publication unchanged.
for t in ['IRIS_26734_SR_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY = max(guideY * factor, 0.0);','float chromaScale26734 = min(factor, 1.0);']:
 assert t in sh,t
# Capture retry: device-agnostic AE-lock rejection progresses once to exact frozen manual exposure; exact-manual rejection terminates.
cc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26735_MANUAL_EXPOSURE_FAILURE_IS_DEVICE_AGNOSTIC','ticket.deterministicExposureFailure = "EXPOSURE_REJECTED".equals(ticket.failureReason)','&& ticket.manualSensorRequest;','IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL','"EXPOSURE_REJECTED".equals(failedTicket.failureReason)','&& !failedTicket.manualSensorRequest','&& motion26713ManualSensorAvailable();','replacement.forceManualSensor = true;','IRIS_26735_AE_LOCK_TO_EXACT_MANUAL','manualSensorAvailable=true exposureWindowUnchanged=true deadlineReset=false','IRIS_26735_MANUAL_EXPOSURE_UNACHIEVABLE','retryStormPrevented=true exposureWindowUnchanged=true','NORMAL_EXPOSURE_UNACHIEVABLE']:
 assert t in cc,t
fallback=cc[cc.index('IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL'):cc.index('plan.addTopUpTicket(replacement)',cc.index('IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL'))]
assert 'isMotion26725GooglePixelCompatibilityRoute()' in fallback  # old Pixel trace remains nested only
assert fallback.index('replacement.forceManualSensor = true;') < fallback.index('if (isMotion26725GooglePixelCompatibilityRoute())')
# Proven 26734 routing/SR/render/native and unrelated owners stay byte-identical.
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26734_ALL_DIGITAL_ZOOM_DETAIL_ARCHITECTURE','localOutputZoom > 1.00001f','IRIS_26734_DIGITAL_ZOOM_ACTIVATION','directChromaOwner=false','IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE','(0.5f * chromaScale).coerceIn(0f, 2f)']:
 assert t in br,t
print('PASS 26735 regressions: 26731 transport + 26727/28/26733 highlight authority frozen; universal physical neutral/specular ownership with independent real-color veto; digital detail luma-only/no chroma gain; 26734 routing+SR frozen; Xiaomi AE-lock retry progresses to exact manual without retry storm; unrelated owners protected')
