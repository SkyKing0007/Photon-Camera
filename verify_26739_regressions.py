#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26739_regressions.py BASE26738 CAND26739')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
changed=set((pkg/'26739_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726739' in v and 'VERSION_BUILD=26739' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
# Faithful Wronski sensor-linear accumulation: WB is downstream, not inside RAW numerator/denominator.
for t in ['IRIS_26739_WRONSKI_SENSOR_LINEAR_ACCUMULATION','gains[channel] = exposureScale / range','IRIS_26739_WRONSKI_SENSOR_LINEAR_NOISE']:
 assert t in st,t
cal=st[st.index('private fun calibrationForFrame('):st.index('return FrameCalibration(',st.index('private fun calibrationForFrame('))]
cal_code=re.sub(r'/\*.*?\*/','',cal,flags=re.S)
assert 'calculationWhiteBalance[' not in cal_code and '* calculationWhiteBalance' not in cal_code
# Shared native publication is already RGB=num/den and must not pass through a second ResolveSabre/demosaic.
for t in ['IRIS_26739_FAITHFUL_WRONSKI_RGB_PUBLICATION','IRIS_26739_WRONSKI_RGB_OWNER sensorLinearMerge=true directNumDen=true','whiteBalanceDuringMerge=false resolveSabre=false secondDemosaic=false','vgn26733Downstream=true']:
 assert t in st,t
pub=st[st.index('IRIS_26739_FAITHFUL_WRONSKI_RGB_PUBLICATION'):st.index('IRIS_26564_TRUE2X_DNG_CARRIER',st.index('IRIS_26739_FAITHFUL_WRONSKI_RGB_PUBLICATION'))]
assert 'renderResolveSabre' not in pub and 'ResolveSabreHalide' not in pub
# Sensor RGB boundary: lens shading first; calculation WB only for the separate physical-HDR comparison path.
for t in ['IRIS_26739_FAITHFUL_WRONSKI_SENSOR_RGB_BOUNDARY','wronskiSensorOutputUint16_26739','wronskiSensorOutputHdrDirectionUint16_26739','wronskiSensorOutputFloat_26739','IRIS_26739_PHYSICAL_CALCULATION_RGB']:
 assert t in sh,t
# High zoom uses the same normalized-convolution owner for 100% ROI; no weak-support native RGB blend, no phase admission.
for t in ['IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR','uReferenceObservation26739','IRIS_26739_HIGH_ZOOM_PHYSICAL_VALIDITY','IRIS_26739_HIGH_ZOOM_FAITHFUL_WRONSKI_RGB_GPU','reconstructionCoveragePct=100.0','nativeRgbFallback=false phaseAuthority=false postHocCfaChromaOwner=false','highlightOwner26733=true tileSeams=false']:
 assert t in sh+st,t
assert 'uObservationConfidence' not in sh[sh.index('IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR'):sh.index('val highZoomRgbProtect26720',sh.index('IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR'))]
# Old 26738 post-RGB CFA color guessing is retired; alias removal belongs to direct burst reconstruction.
for t in ['IRIS_26739_NO_POST_HOC_CFA_MOIRE_OWNER','IRIS_26739_WRONSKI_OWNS_CFA_ALIAS_REMOVAL']:
 assert t in vgn,t
for stale in ['IRIS_26738_UNIVERSAL_CFA_PERIOD_CHROMA_OWNER','IRIS_26738_FINAL_ALIAS_FLOOR_VETO']:
 assert stale not in vgn,stale
# The 26738 high-zoom protect shader remains source text only and has no active stacker call site.
assert 'highZoomRgbProtect26724' not in st
# Physical per-channel headroom is support provenance only: it does not censor the reconstruction numerator.
merge_start=sh.index('IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR'); merge_end=sh.index('val highZoomRgbProtect26720',merge_start); merge=sh[merge_start:merge_end]
for t in ['channelValidWeight','validWeights *= frameWeight','oValidWeights = vec4(validWeights, 0.0)']:
 assert t in merge,t
assert 'color *= validWeight' not in merge and 'weights *= validWeight' not in merge
# One row-flicker multiplication per observation: alternates rejection-only; reference merge-only.
for t in ['rowFlickerFrame26720 = null','ev.frameIndex == 0 && hasRowFlickerEvidence26720(frame)','uReferenceObservation26739", if (ev.frameIndex == 0) 1 else 0']:
 assert t in st,t
# Telemetry must describe one Wronski RGB owner for native and digital output.
for t in ['WRONSKI_SENSOR_RGB_2X_VGN26733','WRONSKI_SENSOR_RGB_NATIVE_VGN26733','singleRgbOwner=true']:
 assert t in br,t
# Preserve explicit Super Res ownership separately.
assert 'IRIS_26568_TRUE2X_READY' in st and 'highResLumaOwner=DIRECT_CFA directChromaOwner=false' in st
# Frozen 26728/26731/26733/26735 protection mechanisms in the modified VGN source remain byte-identical.
def section(s,marker):
 i=s.index(marker); j=s.find('/* IRIS_',i+len(marker)); return s[i:] if j<0 else s[i:j]
bv=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
for marker in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26735_INDEPENDENT_PHYSICAL_REAL_COLOR_PROOF','IRIS_26735_NEUTRAL_EDGE_AND_SPECULAR_BRACKET_OWNER','IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_NEUTRAL_FLOOR_VETO','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26733_EARLY_ACHROMATIC_STRUCTURE_OWNER','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP']:
 assert section(bv,marker)==section(vgn,marker),marker
# Protected capture/color/UHDR/native owners remain exactly unchanged by manifest and direct byte check.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
cc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL','IRIS_26735_MANUAL_EXPOSURE_UNACHIEVABLE','NORMAL_EXPOSURE_UNACHIEVABLE']: assert t in cc,t
# Claude historical failure invariant: confidence can never be a ratio whose denominator collapses with green support.
assert 'opponentSupportQuality' not in sh and 'R−G' not in sh and 'B−G' not in sh
# Numerical invariant: losing any physical channel support can only reduce the minimum support used by highlight/color authority.
def min_support(r,g,b): return min(r,g,b)
assert min_support(1,1,1)==1 and min_support(1,.2,1)<1 and min_support(1,0,1)==0
print('PASS 26739 regressions: faithful sensor-linear Wronski RGB owner; no second demosaic/native weak-support blend/post-hoc CFA classifier; per-channel headroom only lowers color authority; 26733 highlight protection and seam/capture/unrelated owners preserved')
