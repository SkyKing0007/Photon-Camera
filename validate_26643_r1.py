#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26643_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def text(r): return (cand/r).read_text()
def same(r): return hashlib.sha256((base/r).read_bytes()).digest()==hashlib.sha256((cand/r).read_bytes()).digest()
# Modified XML resources must parse.
for r in ['app/src/main/res/layout/layout_manual_toggle_panel.xml','app/src/main/res/color/black_white_selectable.xml']:
 ET.parse(cand/r)
# Quick menu: RAW, Battery Saver and prior Exposure Bracketing UI owners are absent; seven rows reflow naturally.
bar=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
for stale in ['saveRawEntry','createSaveRawEntry','batterySaverEntry','createBatterySaverEntry','bracketingEntry','createBracketingEntry']:
 assert stale not in bar,stale
assert 'private final List<SettingsBarEntryModel> allEntries = new ArrayList<>(7);' in bar
ctor=bar[bar.index('public SettingsBarEntryProvider()'):bar.index('public void createEntries()')]
adds=[ln.strip() for ln in ctor.splitlines() if ln.strip().startswith('allEntries.add(')]
assert len(adds)==7 and all(x in ctor for x in ['flashEntry','timerEntry','quadEntry','eisEntry','fpsEntry','gridEntry','superResEntry'])
# Quick-menu selection is glyph-only yellow/white with no circular/background state.
entry=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java')
for x in ['IRIS_26643_QUICK_MENU_GLYPH_SELECTION_OWNER','android.R.attr.colorControlActivated','new int[]{activatedColor, Color.WHITE}','button.setBackgroundColor(Color.TRANSPARENT)','button.setStateListAnimator(null)']:
 assert x in entry,x
assert 'R.drawable.aux_button_background' not in entry and 'setBackgroundResource(R.drawable.aux_button_background)' not in entry
# Lens selection is text-glyph-only yellow/white; no circular background survives.
aux=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java')
for x in ['IRIS_26643_LENS_TEXT_SELECTION_OWNER','b.setBackgroundColor(android.graphics.Color.TRANSPARENT)','b.setStateListAnimator(null)']:
 assert x in aux,x
assert 'R.drawable.aux_button_background' not in aux
sel=text('app/src/main/res/color/black_white_selectable.xml')
assert 'android:state_selected="true" android:color="?android:colorControlActivated"' in sel
assert '<item android:color="@android:color/white"/>' in sel
# Manual chevron matches lens-label visual scale and has no pill/border/elevation.
manual=text('app/src/main/res/layout/layout_manual_toggle_panel.xml')
for x in ['android:layout_width="35dp"','android:layout_height="24dp"','android:textSize="13sp"','android:textStyle="bold"']:
 assert x in manual,x
for stale in ['iris_outline_pill','android:elevation=']:
 assert stale not in manual,stale
# AOSP Android-16 HEIC publication authority: base P3/sRGB/unspecified/full, gain unspecified/full,
# tmap P3/sRGB/unspecified/full, single NCLX base authority, ISO gain payload retained.
cpp=text('app/src/main/cpp/iris_heic_jni.cpp')
for x in ['IRIS_26643_AOSP_ANDROID16_HEIC_ULTRAHDR_BASE_AUTHORITY','IRIS_26643_AOSP_ANDROID16_HEIC_ULTRAHDR_ITEM_AUTHORITY',
          'baseNclx, heif_color_primaries_SMPTE_EG_432_1','baseNclx, heif_transfer_characteristic_IEC_61966_2_1',
          'baseNclx, heif_matrix_coefficients_unspecified','baseNclx->full_range_flag = true',
          'gainmapNclx, heif_color_primaries_unspecified','gainmapNclx, heif_transfer_characteristic_unspecified',
          'gainmapNclx, heif_matrix_coefficients_unspecified','gainmapNclx->full_range_flag = true',
          'alternateNclx, heif_color_primaries_SMPTE_EG_432_1','alternateNclx, heif_transfer_characteristic_IEC_61966_2_1',
          'alternateNclx, heif_matrix_coefficients_unspecified','alternateNclx->full_range_flag = true',
          'metadata.use_base_cg = 1','heif_context_encode_gain_map_image','save_two_colr_boxes_when_ICC_and_nclx_available = 0',
          'IRIS_26643_HEIC_AOSP_ANDROID16_ISO21496']:
 assert x in cpp,x
for stale in ['IccHelper::writeIccProfile','heif_image_set_raw_color_profile(']: assert stale not in cpp,stale
# Dependency patch is the sole post-Google AOSP container correction; old 26642 local patch is neutralized/unreferenced.
patch=text('app/src/main/cpp/iris26643_libheif_aosp_contract.patch')
assert patch.count('+  pixi->add_channel_bits(8);')==3 and patch.count('-  pixi->add_channel_bits(10);')==3
assert 'diff --git a/libheif/image-items/image_item.cc b/libheif/image-items/image_item.cc' in patch
assert 'diff --git a/libheif/context.cc b/libheif/context.cc' not in patch
assert '+    infe_box->set_hidden_item(false);' in patch and '-    infe_box->set_hidden_item(true);' in patch
assert '+  assoc.essential = true;' in patch
assert 'format != heif_compression_HEVC' in patch and 'if (miaf_compatible && format != heif_compression_HEVC)' in patch
cm=text('app/src/main/cpp/CMakeLists.txt')
for x in ['IRIS_26643_AOSP_ANDROID16_HEIC_CONTAINER_OWNER','IRIS26643_LIBHEIF_AOSP_PATCH_SHA256','IRIS26643_LIBHEIF_AOSP_PATCH_ACTUAL_SHA256',
          'IRIS_26643_PINNED_V2_LIBHEIF_PATCH_REPLAY','google/libultrahdr/v2.0.0/cmake/patches/libheif_pr1503.patch',
          'IRIS26636_LIBHEIF_PATCH_BLOB "da5494f223f369781bbabcdaf6dbe192e0d74ca1"',
          'COMMAND ${GIT_EXECUTABLE} apply --check --ignore-space-change --whitespace=nowarn "${IRIS26643_LIBHEIF_AOSP_PATCH}"',
          'COMMAND ${GIT_EXECUTABLE} apply --ignore-space-change --whitespace=nowarn "${IRIS26643_LIBHEIF_AOSP_PATCH}"']:
 assert x in cm,x
assert cm.index('apply --check --ignore-space-change --whitespace=nowarn "${IRIS26643_LIBHEIF_AOSP_PATCH}"') < cm.index('apply --ignore-space-change --whitespace=nowarn "${IRIS26643_LIBHEIF_AOSP_PATCH}"', cm.index('apply --check'))
assert 'iris26642_libheif_android16_tmap.patch' not in cm
assert same('app/src/main/cpp/iris26642_libheif_android16_tmap.patch')
# MediaCodec no longer publishes a conflicting requested VUI color contract; output-format values remain diagnostic only.
enc=text('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
assert 'IRIS_26643_AOSP_ANDROID16_CODEC_CONFIGURATION_OWNER' in enc
for stale in ['format.setInteger(MediaFormat.KEY_COLOR_STANDARD','format.setInteger(MediaFormat.KEY_COLOR_TRANSFER','format.setInteger(MediaFormat.KEY_COLOR_RANGE']:
 assert stale not in enc,stale
for x in ['of.containsKey(MediaFormat.KEY_COLOR_STANDARD)','of.containsKey(MediaFormat.KEY_COLOR_TRANSFER)','of.containsKey(MediaFormat.KEY_COLOR_RANGE)']:
 assert x in enc,x
# Android post-save decode proof remains inherited for both formats.
saver=text('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
for x in ['IRIS_26642_ANDROID_ULTRAHDR_DECODE_PROOF','iris26642ScheduleUltraHdrDecodeProof(fileToSave, "HEIC")','iris26642ScheduleUltraHdrDecodeProof(fileToSave, "JPEG")','hasGainmap()']:
 assert x in saver,x
# Successful 26642 UHDR/IQ/performance/SHORT/color/capture owners remain byte-identical.
for r in [
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImagePath.java',
 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
 'app/src/main/res/xml/preferences.xml']:
 assert same(r),r
ver=text('app/version.properties')
assert 'VERSION_MINOR=9726440' in ver and 'VERSION_NAME=0.9726643' in ver and 'VERSION_BUILD=26643' in ver
print('PASS 26643 semantics: single Android-16 AOSP HEIC publication authority + ISO21496 retained + requested quick-menu/lens/manual UI cleanup; successful 26642 image pipeline frozen')
