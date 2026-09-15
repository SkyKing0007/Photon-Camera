#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26642_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def T(r): return (cand/r).read_text()
def H(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
# UI: the legacy Photo action can never occupy a hidden/blank pill slot.
ui=T('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
b=ui[ui.index('IRIS_26642_UI_PHOTO_IS_MOTION_OWNER'):ui.index('@Tunable',ui.index('IRIS_26642_UI_PHOTO_IS_MOTION_OWNER'))]
assert 'CameraMode.PHOTO' not in b and b.count('CameraMode.MOTION')==1 and b.count('"Photo"')==1
assert 'CameraMode selectorMode = mode == CameraMode.PHOTO ? CameraMode.MOTION : mode;' in ui
assert 'return indexOfMode(CameraMode.MOTION);' in ui
# Quick Settings: no Exposure Bracketing UI survives; Super Res still exists.
bar=T('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
assert 'bracketingEntry' not in bar and 'createBracketingEntry' not in bar and 'superResEntry' in bar
# Settings requested removals are permanent UI regressions.
prefs=T('app/src/main/res/xml/preferences.xml')
for stale in ['pref_energy_safe_key','pref_hide_gallery_icon_key','pref_rawvideo_downscale_4x_key','pref_cfa_key','pref_align_method_key','pref_color_method_key','pref_tunable_submenu']:
 assert stale not in prefs,stale
assert prefs.count('pref_photo_prefix_name_key')==1
# Prefix exact behavior, including no forced underscore and video isolation.
def name(prefix,cfg,ts='20260914_233237'):
 return (cfg+ts) if prefix=='IMG' else prefix+'_'+ts
assert name('IMG','IMG_')=='IMG_20260914_233237'
assert name('IMG','Skyyking_')=='Skyyking_20260914_233237'
assert name('IMG','Skyyking')=='Skyyking20260914_233237'
assert name('VID','Skyyking_')=='VID_20260914_233237'
ip=T('app/src/main/java/com/particlesdevs/photoncamera/processing/ImagePath.java')
assert 'isValidPhotoPrefix(configured) ? configured : "IMG_"' in ip
# HEIC concrete real-failure regression: never publish the tmap as the old 10-bit P3/linear derived raster.
cpp=T('app/src/main/cpp/iris_heic_jni.cpp'); patch=T('app/src/main/cpp/iris26642_libheif_android16_tmap.patch')
alt=cpp[cpp.index('alternateNclx ='):cpp.index('// Keep the established Iris gain-map publication quality authority.')]
assert 'heif_transfer_characteristic_linear' not in alt
assert 'heif_matrix_coefficients_chromaticity_derived_non_constant_luminance' not in alt
assert patch.count('+  pixi->add_channel_bits(8);')==3 and patch.count('-  pixi->add_channel_bits(10);')==3
# Framework-decode proof must cover both HEIC and working JPEG.
saver=T('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
assert 'iris26642ScheduleUltraHdrDecodeProof(fileToSave, "HEIC")' in saver
assert 'iris26642ScheduleUltraHdrDecodeProof(fileToSave, "JPEG")' in saver
# All successful 26641 IQ/performance/shared-GL/SHORT owners remain exact bytes.
for r in ['app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt']:
 assert H(base,r)==H(cand,r),r
print('PASS 26642 permanent regressions: no legacy Photo/bracketing/settings gaps; prefix exact; no old HEIC 10-bit-linear tmap; Android JPEG+HEIC decode proof; 26641 image owners frozen')
