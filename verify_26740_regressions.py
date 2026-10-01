#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26740_regressions.py BASE26739 CAND26740')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
changed=set((pkg/'26740_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726740' in v and 'VERSION_BUILD=26740' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
bsh=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
bst=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
bv=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# 26739 Wronski normalized-convolution accumulator remains byte-identical. 26740 observes it; it does not rewrite its math.
def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
assert section(bsh,'IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR','IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY') == section(sh,'IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR','IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY')
# Sensor-linear RGB boundary remains the faithful 26739 owner; no second demosaic is resurrected.
for t in ['IRIS_26739_WRONSKI_SENSOR_LINEAR_ACCUMULATION','IRIS_26739_FAITHFUL_WRONSKI_RGB_PUBLICATION','whiteBalanceDuringMerge=false resolveSabre=false secondDemosaic=false','vgn26733Downstream=true']:
 assert t in st,t
# 26740 adds read-only phase/temporal reconstruction evidence and a pre-VGN confidence publication gate.
for t in ['IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_STABILITY_EVIDENCE','highZoomRgbStabilityMerge26740','IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE','highZoomRgbStabilize26740']:
 assert t in sh,t
for t in ['nativeVgnGuideTexture = nativeHdrAuthority26601','uReferenceObservation26740','phaseAuthority=LOCAL_PIXEL_GATE','temporalAuthority=LOCAL_PIXEL_GATE','shapeBound=true','nativeRgbFallback=LOCAL_CONFIDENCE_ONLY']:
 assert t in st,t
# New gate must feed BOTH physical HDR comparison and VGN; unresolved direct RGB cannot bypass it.
gate_start=st.index('val stabilized26740 = createTexture'); gate_end=st.index('val proof =',gate_start)
gate=st[gate_start:gate_end]
for t in ['sensorRgb = stabilized26740','uDirectRgb", 0, resolved','uNativeVgnGuide", 3, nativeVgnGuideTexture']:
 assert t in gate,t
assert 'sensorRgb = resolved' not in gate
# 26740 additions are generic reconstruction evidence, not a semantic barcode/font/text special case.
added_shader=section(sh,'IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE','IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION') + section(sh,'IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_STABILITY_EVIDENCE','IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE')
added_stacker=st[st.index('val stabilized26740 = createTexture'):st.index('val proof =',st.index('val stabilized26740 = createTexture'))]
for forbidden in ['barcode','fontdetector','textdetector','semanticclass']:
 assert forbidden not in added_shader.lower() and forbidden not in added_stacker.lower(),forbidden
# Full reconstruction failure still fails closed to the already-complete native Sabre/VGN path.
for t in ['IRIS_26732_HIGH_ZOOM_CLEAN_NATIVE_FALLBACK','fallback=NATIVE_SABRE_VGN_NO_DETAIL']:
 assert t in st,t
# Preserve 26729+ / 26731 material/color transport. These sections are byte-identical.
def marker_section(s,marker):
 i=s.index(marker); j=s.find('/* IRIS_',i+len(marker)); return s[i:] if j<0 else s[i:j]
for marker in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP']:
 assert marker_section(bv,marker)==marker_section(vgn,marker),marker
# Keep the successful 26727/26728 headroom thresholds; only bright-color opt-back is tightened with independent physical proof.
for t in ['smoothstep(0.72,0.92,centerNormalizedY)','IRIS_26740_BRIGHT_COLOR_REQUIRES_INDEPENDENT_PHYSICAL_CONTINUATION','physicalColorContinuation26735','IRIS_26740_HEADROOM_OVERRIDE_REQUIRES_PHYSICAL_REAL_COLOR','physicalRealColorVeto26735']:
 assert t in vgn,t
assert 'smoothstep(0.62,0.90,physicalColorContinuation26735)' in vgn
assert 'smoothstep(0.55, 0.88, physicalRealColorVeto26735)' in vgn
# Ordinary non-highlight material ownership remains present; no global chroma muting knob is added.
for t in ['microObjectProtection','supportedMaterialBoundary','coherentCenterProtection','topologyProtection']:
 assert t in vgn,t
# 26739 direct-CFA post-hoc moire/color guessing remains retired.
for t in ['IRIS_26739_NO_POST_HOC_CFA_MOIRE_OWNER','IRIS_26739_WRONSKI_OWNS_CFA_ALIAS_REMOVAL']:
 assert t in vgn,t
for stale in ['IRIS_26738_UNIVERSAL_CFA_PERIOD_CHROMA_OWNER','IRIS_26738_FINAL_ALIAS_FLOOR_VETO']:
 assert stale not in vgn,stale
# Shared capture/render/UHDR/native/settings owners remain exactly protected.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Flicker authority stays single-owner: new read-only evidence applies row reliability only to the reference, while comparison rejection remains inherited.
assert 'uReferenceObservation26740' in sh and 'iris26740ReferenceRowReliability' in sh
assert 'ev.frameIndex == 0 && hasRowFlickerEvidence26720(frame)' in st
# No Plan B / no alternative SR owner in this build.
for forbidden in ['LINEAR_TRANSLATIONAL_SR_26740','IPOL_26740','PLAN_B_26740']:
 assert forbidden not in sh+st+vgn
print('PASS 26740 regressions: 26739 Wronski accumulation preserved; generic phase/temporal/shape confidence gates RGB before VGN; bright opt-back requires independent physical color; 26729+/26731 color transport and protected owners preserved')
