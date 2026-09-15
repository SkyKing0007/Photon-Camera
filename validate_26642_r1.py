#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26642_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def text(r): return (cand/r).read_text()
def same(r): return hashlib.sha256((base/r).read_bytes()).digest()==hashlib.sha256((cand/r).read_bytes()).digest()
# XML resources must parse.
for r in ['app/src/main/res/xml/preferences.xml','app/src/main/res/values/preference_keys.xml','app/src/main/res/values/strings.xml','app/src/main/res/drawable/ic_prefix_name.xml']:
 ET.parse(cand/r)
# Public selector: exactly five entries; visible Photo is internal Motion; legacy Photo action absent.
ui=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
a=ui.index('IRIS_26642_UI_PHOTO_IS_MOTION_OWNER'); z=ui.index('@Tunable',a); block=ui[a:z]
assert block.count('"Photo"')==1 and '"Motion"' not in block and 'CameraMode.PHOTO' not in block
for x in ['CameraMode.UNLIMITED','CameraMode.RAWVIDEO','CameraMode.MOTION','CameraMode.NIGHT','CameraMode.VIDEO']: assert block.count(x)==1,x
assert ui.count('this.mModePicker.setValues(MODE_DISPLAY_LABELS);')==1 and ui.count('MODE_ACTION_ORDER[index]')==1
assert 'CameraMode selectorMode = mode == CameraMode.PHOTO ? CameraMode.MOTION : mode;' in ui
assert 'return indexOfMode(CameraMode.MOTION);' in ui
# Quick menu: bracketing UI owner gone; Super Res remains.
bar=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
assert 'bracketingEntry' not in bar and 'createBracketingEntry' not in bar and 'superResEntry' in bar
# Settings cleanup + Prefix Name exact presentation/order.
prefs=text('app/src/main/res/xml/preferences.xml')
for x in ['pref_energy_safe_key','pref_hide_gallery_icon_key','pref_rawvideo_downscale_4x_key','pref_cfa_key','pref_align_method_key','pref_color_method_key','pref_tunable_submenu','Tunable Settings']:
 assert x not in prefs,x
assert prefs.count('pref_photo_prefix_name_key')==1
assert prefs.index('pref_save_per_lens_settings') < prefs.index('pref_photo_prefix_name_key')
segment=prefs[prefs.index('pref_save_per_lens_settings'):prefs.index('</PreferenceCategory>',prefs.index('pref_save_per_lens_settings'))]
assert segment.count('pref_photo_prefix_name_key')==1
assert 'ns0:title="@string/prefix_name"' in segment and 'ns0:dialogTitle="@string/photo_prefix_name"' in segment
assert 'ns0:defaultValue="IMG_"' in segment and '@drawable/ic_prefix_name' in segment
strings=text('app/src/main/res/values/strings.xml')
assert '<string name="prefix_name">Prefix Name</string>' in strings
assert '<string name="photo_prefix_name">Photo Prefix Name</string>' in strings
# Prefix persistence / policy.
pk=text('app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
for x in ['KEY_PHOTO_PREFIX_NAME','COMMON_KEYS.add(Key.KEY_PHOTO_PREFIX_NAME.mValue)','setInitial(SCOPE_GLOBAL, Key.KEY_PHOTO_PREFIX_NAME, "IMG_")','getPhotoPrefixName()']:
 assert x in pk,x
ip=text('app/src/main/java/com/particlesdevs/photoncamera/processing/ImagePath.java')
for x in ['IRIS_26642_PHOTO_PREFIX_NAME_OWNER','if ("IMG".equals(prefix))','PreferenceKeys.getPhotoPrefixName()','isValidPhotoPrefix','return prefix + "_" + timestamp;']:
 assert x in ip,x
settings=text('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
for x in ['IRIS_26642_PHOTO_PREFIX_SETTINGS_OWNER','setupPhotoPrefixPreference();','EditTextPreference.SimpleSummaryProvider.getInstance()','editText.setSelectAllOnFocus(true)','ImagePath.isValidPhotoPrefix(candidate)']:
 assert x in settings,x
# HEIC derived-item publication aligns with Android16 framework while retaining ISO gain metadata.
cpp=text('app/src/main/cpp/iris_heic_jni.cpp')
for x in ['IRIS_26642_ANDROID16_HEIC_ULTRAHDR_ITEM_AUTHORITY','gainmapNclx, heif_matrix_coefficients_unspecified','alternateNclx, heif_transfer_characteristic_IEC_61966_2_1','alternateNclx, heif_matrix_coefficients_unspecified','metadata.use_base_cg = 1','heif_context_encode_gain_map_image']:
 assert x in cpp,x
alt=cpp[cpp.index('alternateNclx ='):cpp.index('// Keep the established Iris gain-map publication quality authority.')]
assert 'heif_transfer_characteristic_linear' not in alt and 'heif_matrix_coefficients_chromaticity_derived_non_constant_luminance' not in alt
patch=text('app/src/main/cpp/iris26642_libheif_android16_tmap.patch')
assert patch.count('+  pixi->add_channel_bits(8);')==3 and patch.count('-  pixi->add_channel_bits(10);')==3
cm=text('app/src/main/cpp/CMakeLists.txt')
for x in ['IRIS_26642_ANDROID16_TMAP_PIXI_OWNER','IRIS26642_LIBHEIF_TMAP_PATCH_SHA256','IRIS26642_LIBHEIF_TMAP_PATCH_ACTUAL_SHA256','COMMAND ${GIT_EXECUTABLE} apply --ignore-space-change --whitespace=nowarn "${IRIS26642_LIBHEIF_TMAP_PATCH}"']:
 assert x in cm,x
# Android decoder proof applies to both formats and cannot rewrite the publication.
saver=text('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
for x in ['IRIS_26642_ANDROID_ULTRAHDR_DECODE_PROOF','BitmapFactory.decodeFile','hasGainmap()','getRatioMin()','getRatioMax()','getGamma()','getEpsilonSdr()','getEpsilonHdr()','getMinDisplayRatioForHdrTransition()','getDisplayRatioForFullHdr()','"HEIC"','"JPEG"']:
 assert x in saver,x
# Successful 26641 image/runtime owners stay byte-identical.
for r in [
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt']:
 assert same(r),r
ver=text('app/version.properties')
assert 'VERSION_MINOR=9726440' in ver and 'VERSION_NAME=0.9726642' in ver and 'VERSION_BUILD=26642' in ver
print('PASS 26642 semantics: Android16 HEIC tmap compatibility + Android decode proof + visible Photo/internal Motion UI + settings cleanup + literal photo prefix; 26641 image owners frozen')
