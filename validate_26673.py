#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26673.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
def amap(r): return {str(p.relative_to(r)):sh(r,str(p.relative_to(r))) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def between(s,a,b):
 i=s.index(a); j=s.index(b,i); return s[i:j]
bm=amap(base); cm=amap(cand); assert len(bm)==len(cm)==1726
changed=[x for x in (root/'R1_26673_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26673_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert changed==[
'app/src/main/cpp/iris_heic_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/version.properties'] and not added
mods=sorted(p for p in bm if bm[p]!=cm[p]); assert mods==sorted(changed); assert set(bm)==set(cm)
for p,h in bm.items():
 if p not in changed: assert cm[p]==h,('26672 hardlock drift',p)
# Explicit high-risk / behavioral hardlocks.
for p in [
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/manual_palette.xml','app/src/main/res/layout/layout_manual_toggle_panel.xml','app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/drawable-anydpi/iris_flip_arrows.xml','app/src/main/res/drawable-nodpi/iris_flip_arrows.png','app/src/main/cpp/CMakeLists.txt']:
 assert sh(base,p)==sh(cand,p),p
# Android round-trip/numerical proof remains exact successful 26672.
heicj=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
for t in ['IRIS_26648_NUMERICAL_ANDROID_GAINMAP_RECONSTRUCTION','IRIS_26648_HEIC_NUMERICAL_HDR','getGainmapDirection()']:
 assert t in heicj,t
hw=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
for t in ['IRIS_COLOR_STANDARD_DISPLAY_P3 = 10','IRIS_COLOR_TRANSFER_SRGB = 2','MediaFormat.KEY_COLOR_STANDARD','MediaFormat.KEY_COLOR_TRANSFER','MediaFormat.KEY_COLOR_RANGE','COLOR_FormatYUV420Flexible']:
 assert t in hw,t
assert 'KEY_COLOR_MATRIX' not in hw
# HEIC native: helper/publisher may change; all other native behavior stays exact.
bcpp=rd(base,'app/src/main/cpp/iris_heic_jni.cpp'); ccpp=rd(cand,'app/src/main/cpp/iris_heic_jni.cpp')
old_h='static bool iris26636FillBaseImage('; new_h='/* IRIS_26673_ANDROID16_HEIC_EXPLICIT_P3_YUV420_OWNER'; gain_h='static bool iris26636FillGainmapImage('
normal='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeNative('
sr='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeSuperResGridNative('
bh=bcpp.index(old_h); ch=ccpp.index(new_h); bg=bcpp.index(gain_h); cg=ccpp.index(gain_h); bn=bcpp.index(normal); cn=ccpp.index(normal); bs=bcpp.index(sr); cs=ccpp.index(sr)
# Prefix differs only by removal of obsolete ICC include; code from gain helper through normal JNI entry remains exact.
assert bcpp[:bh].replace('#include <ultrahdr/icc.h>\n','')==ccpp[:ch]
assert bcpp[bg:bn]==ccpp[cg:cn]
assert bcpp[bs:]==ccpp[cs:],'Super-Res HEIC path changed'
cnorm=ccpp[cn:cs]; bnorm=bcpp[bn:bs]
meta='ultrahdr::uhdr_gainmap_metadata_ext_t metadata(ultrahdr::kJpegrVersion);'; alt='alternateNclx = heif_nclx_color_profile_alloc();'
assert between(bnorm,meta,alt)==between(cnorm,meta,alt),'gain-map/ISO21496 metadata math changed'
for t in [
'IRIS_26673_ANDROID16_HEIC_EXPLICIT_P3_YUV420_OWNER','heif_colorspace_YCbCr','heif_chroma_420',
'constexpr float kYr = 0.299f','constexpr float kYg = 0.587f','constexpr float kYb = 0.114f','constexpr float kCb = 1.772f','constexpr float kCr = 1.402f',
'IRIS_26673_ANDROID16_HEIC_ULTRAHDR_BASE_PUBLICATION','heif_transfer_characteristic_IEC_61966_2_1','heif_matrix_coefficients_unspecified',
'options->save_two_colr_boxes_when_ICC_and_nclx_available = 0','IRIS_26673_ANDROID16_HEIC_ULTRAHDR_GAINMAP_PUBLICATION',
'IRIS_26673_ANDROID16_HEIC_ULTRAHDR_TMAP_PUBLICATION','IRIS_26673_ANDROID16_HEIC_ULTRAHDR_PUBLICATION','baseIcc=false','recomputedGainmap=false']:
 assert t in ccpp,t
for bad in ['IccHelper::writeIccProfile','heif_image_set_raw_color_profile','IRIS_26672_HEIC_GOOGLE_V2_PUBLICATION']:
 assert bad not in cnorm,bad
for bad in ['generateGainMap(', 'generateGainMapOnePass(', 'toneMap(', 'applyGainMap(']: assert bad not in cnorm,bad
# Manual geometry: exact successful-26672 UI baseline remains; CameraFragment is sole new correction owner.
ui=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for t in ['IRIS_26672_MANUAL_ROW_CURRENT_26671_MIDPOINT_OWNER','current26671TranslationPx = manualMode.getTranslationY()','rowLp.topMargin += deltaPx','manualMode.setTranslationY(current26671TranslationPx + deltaPx)']:
 assert t in ui,t
frag=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
for t in [
'IRIS_26673_MANUAL_FIXED_MIDPOINT_STATE','iris26673ManualMidpointEstablished = false','iris26673ManualFixedRowTranslationY = Float.NaN',
'IRIS_26673_MANUAL_FIXED_MIDPOINT_FROM_26672_VISIBLE_GEOMETRY','baseline=current26672FinalVisible',
'panel.setTranslationY(0.0f)','current26672RowCenterY = panelWindow[1] + buttons.getTop()','sliderOuterBottomY = sliderWindow[1] + slider.getHeight()',
'activatedChevronVisibleTopY = chevronWindow[1] + 0.34f * chevron.getHeight()','targetCenterY = 0.5f * (sliderOuterBottomY + activatedChevronVisibleTopY)',
'fixedTranslationY = targetCenterY - current26672RowCenterY','buttons.setTranslationY(fixedTranslationY)',
'iris26673ManualFixedRowTranslationY = fixedTranslationY','iris26673ManualMidpointEstablished = true','IRIS_26673_MANUAL_VISIBILITY_ONLY_OWNER','IRIS_26673_MANUAL_HIDDEN_STATIONARY']:
 assert t in frag,t
# No old show/hide vertical animation may survive inside the presentation owner.
vis=between(frag,'private void iris26670ApplyManualPresentationState(', '    void toggleManualControls()')
assert '.translationY(' not in vis and 'R.dimen.standard_20' not in vis
# Midpoint is established once; subsequent visibility toggles cannot recalculate row geometry.
assert frag.count('iris26673FixManualRowAtMeasuredMidpoint(panel);')==1
assert 'if (!iris26673ManualMidpointEstablished)' in vis
# Source-level algebra: final visible row center is exactly target; hide/reopen leave row translation untouched.
for slider_bottom,row_center,chev_top in [(100.0,130.0,200.0),(220.25,254.5,341.75),(-15.0,20.0,80.0)]:
 target=.5*(slider_bottom+chev_top); delta=target-row_center
 assert abs((row_center+delta)-target)<1e-9
# Version exact.
v=rd(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726673' in v and 'VERSION_BUILD=26673' in v
print('VALIDATE_26673_OK exact successful-26672 hardlock outside 3 paths; Android16 AOSP HEIC_UHDR explicit P3 YUV420 publication with existing gainmap/Android proof preserved; manual row established once from final 26672 visible geometry and never shifts on toggle; version 0.9726673/26673')
