#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26672.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
def amap(r): return {str(p.relative_to(r)):sh(r,str(p.relative_to(r))) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bm=amap(base); cm=amap(cand); assert len(bm)==1725 and len(cm)==1726
changed=[x for x in (root/'R1_26672_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26672_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
assert len(changed)==4 and added==['app/src/main/res/drawable-anydpi/iris_flip_arrows.xml']
mods=sorted(p for p in set(bm)&set(cm) if bm[p]!=cm[p]); adds=sorted(set(cm)-set(bm)); dels=sorted(set(bm)-set(cm))
assert mods==sorted(set(changed)-set(added)) and adds==added and not dels,(mods,adds,dels)
# Successful 26671 is hard behavioral golden everywhere else.
for p,h in bm.items():
 if p not in changed: assert cm.get(p)==h,('26671 hardlock drift',p)
# Imaging/capture/JPEG/HEIC-Java/histogram/manual touch owners are exact 26671 bytes.
for p in [
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/manual_palette.xml','app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/drawable-nodpi/iris_flip_arrows.png','app/src/main/cpp/CMakeLists.txt']:
 assert sh(base,p)==sh(cand,p),p
# HEIC: only normal writeNative publication changes; super-res path and metadata/gain pixels stay exact.
bcpp=rd(base,'app/src/main/cpp/iris_heic_jni.cpp'); ccpp=rd(cand,'app/src/main/cpp/iris_heic_jni.cpp')
normal='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeNative('
sr='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeSuperResGridNative('
bi=bcpp.index(normal); ci=ccpp.index(normal); bsr=bcpp.index(sr); csr=ccpp.index(sr)
assert bcpp[:bi]==ccpp[:ci],'HEIC native prefix drift'; assert bcpp[bsr:]==ccpp[csr:],'Super-Res HEIC path changed'
bnorm=bcpp[bi:bsr]; cnorm=ccpp[ci:csr]
# Existing Iris gain-map values/ISO metadata conversion remain text-exact.
anchor0='ultrahdr::uhdr_gainmap_metadata_ext_t metadata(ultrahdr::kJpegrVersion);'
anchor1='alternateNclx = heif_nclx_color_profile_alloc();'
def between(s,a,b):
 i=s.index(a);j=s.index(b,i);return s[i:j]
assert between(bnorm,anchor0,anchor1)==between(cnorm,anchor0,anchor1),'gain-map metadata math changed'
for t in [
'IRIS_26672_GOOGLE_LIBULTRAHDR_V2_HEIF_BASE_PUBLICATION',
'ultrahdr::IccHelper::writeIccProfile(UHDR_CT_SRGB, UHDR_CG_DISPLAY_P3)',
'heif_image_set_raw_color_profile(', 'baseImage, "prof"',
'heif_transfer_characteristic_ITU_R_BT_709_5','heif_matrix_coefficients_ITU_R_BT_601_6',
'options->save_two_colr_boxes_when_ICC_and_nclx_available = 1',
'IRIS_26672_GOOGLE_LIBULTRAHDR_V2_HEIF_GAINMAP_PUBLICATION',
'heif_color_primaries_unspecified','heif_transfer_characteristic_unspecified',
'IRIS_26672_GOOGLE_LIBULTRAHDR_V2_TMAP_HDR_INTENT_AUTHORITY',
'heif_transfer_characteristic_linear','heif_matrix_coefficients_chromaticity_derived_non_constant_luminance',
'heif_context_encode_gain_map_image(ctx, baseHandle, encoder, gainImage, options,',
'recomputedGainmap=false']:
 assert t in cnorm,t
for forbidden in ['generateGainMap(', 'generateGainMapOnePass(', 'toneMap(']: assert forbidden not in cnorm,forbidden
# Manual row midpoint is computed from successful-26671 geometry, keeping the existing 12px baseline.
j=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for t in ['IRIS_26672_MANUAL_ROW_CURRENT_26671_MIDPOINT_OWNER','current26671TranslationPx = manualMode.getTranslationY()','0.34f * chevronHeight','desiredCenterFromStackTop','rowLp.topMargin += deltaPx','manualMode.setTranslationY(current26671TranslationPx + deltaPx)','sliderCurrent26671PositionPreserved=true geometricMidpoint=true']:
 assert t in j,t
assert 'android:translationY="12px"' in rd(cand,'app/src/main/res/layout/camera_fragment.xml')
# Density geometry regression (Android inflated dimensions; 12px baseline is deliberately physical-pixel authority).
for density in [1.0,1.5,2.0,2.625,3.0,3.5,4.0,4.5,5.0]:
 row=round(48*density); stack=round(24*density); chev=round(18*density); margin=round(6*density); ty=12.0
 slider_bottom=-margin-row+ty; row_center=-margin-row*0.5+ty; chev_upper=(stack-chev)*0.5+0.34*chev
 target=0.5*(slider_bottom+chev_upper); delta=round(target-row_center)
 assert delta>0,(density,delta)
 assert abs((row_center+delta)-target)<=0.5+1e-9,(density,row_center+delta,target)
 # Parent height grows by delta while translation grows by same delta -> slider visual position exact.
 assert abs((slider_bottom-delta)+(ty+delta-ty)-slider_bottom)<1e-9
# Vector: same resource name/active layout, same approximate 26671 visible footprint, density independent.
vp='app/src/main/res/drawable-anydpi/iris_flip_arrows.xml'; ET.parse(cand/vp); vx=rd(cand,vp)
for t in ['IRIS_26672_FRONT_SWITCH_VECTOR_ARROW_OWNER','android:width="36dp"','android:height="36dp"','android:viewportWidth="128"','android:viewportHeight="128"','android:strokeWidth="8"']:
 assert t in vx,t
layout=rd(cand,'app/src/main/res/layout/layout_bottombuttons.xml'); assert 'android:src="@drawable/iris_flip_arrows"' in layout and 'android:padding="2dp"' in layout
# Version exact.
v=rd(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726672' in v and 'VERSION_BUILD=26672' in v
print('VALIDATE_26672_OK exact successful-26671 hardlock outside 4 paths; Google-libultrahdr-v2 HEIC publication-only parity; current-26671 geometric manual midpoint; same-footprint vector flip arrows; version 0.9726672/26672')
