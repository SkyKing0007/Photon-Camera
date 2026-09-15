#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26643_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def T(r): return (cand/r).read_text()
def H(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
# Real UI failures/requests: quick menu must never resurrect RAW, Battery Saver or Exposure Bracketing.
bar=T('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
for stale in ['saveRawEntry','createSaveRawEntry','batterySaverEntry','createBatterySaverEntry','bracketingEntry','createBracketingEntry']:
 assert stale not in bar,stale
ctor=bar[bar.index('public SettingsBarEntryProvider()'):bar.index('public void createEntries()')]
adds=[ln.strip() for ln in ctor.splitlines() if ln.strip().startswith('allEntries.add(')]
assert 'new ArrayList<>(7)' in bar and len(adds)==7
# Selection highlight must stay within icon/text glyphs: no circle background can survive in active quick/lens owners.
entry=T('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/settingsbar/SettingsBarEntryView.java')
aux=T('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java')
sel=T('app/src/main/res/color/black_white_selectable.xml')
assert 'R.drawable.aux_button_background' not in entry and 'R.drawable.aux_button_background' not in aux
assert 'button.setBackgroundColor(Color.TRANSPARENT)' in entry and 'android.R.attr.colorControlActivated' in entry
assert 'b.setBackgroundColor(android.graphics.Color.TRANSPARENT)' in aux
assert '?android:colorControlActivated' in sel and '@android:color/white' in sel
manual=T('app/src/main/res/layout/layout_manual_toggle_panel.xml')
assert 'iris_outline_pill' not in manual and 'android:elevation=' not in manual and 'android:textSize="13sp"' in manual and 'android:layout_width="35dp"' in manual
# HEIC: no second hybrid. One Android-16 publication authority only.
cpp=T('app/src/main/cpp/iris_heic_jni.cpp')
assert 'baseNclx, heif_matrix_coefficients_unspecified' in cpp
assert 'save_two_colr_boxes_when_ICC_and_nclx_available = 0' in cpp
assert 'IccHelper::writeIccProfile' not in cpp and 'heif_image_set_raw_color_profile(' not in cpp
assert 'gainmapNclx, heif_matrix_coefficients_unspecified' in cpp
assert 'alternateNclx, heif_transfer_characteristic_IEC_61966_2_1' in cpp and 'alternateNclx, heif_matrix_coefficients_unspecified' in cpp
# ISO 21496 metadata generation and gain-map handoff remain present.
for x in ['uhdr_gainmap_metadata_frac::gainmapMetadataFloatToFraction','uhdr_gainmap_metadata_frac::encodeGainmapMetadata','heif_context_encode_gain_map_image']:
 assert x in cpp,x
# New dependency patch must parse as a real git patch: malformed-hunk failure is permanent.
p=cand/'app/src/main/cpp/iris26643_libheif_aosp_contract.patch'
subprocess.run(['git','apply','--numstat',str(p)],check=True,stdout=subprocess.DEVNULL)
patch=p.read_text()
assert '+    infe_box->set_hidden_item(false);' in patch
assert '+  assoc.essential = true;' in patch
assert 'if (miaf_compatible && format != heif_compression_HEVC)' in patch
assert patch.count('+  pixi->add_channel_bits(8);')==3
# Old 26642 patch may remain as protected history, but it must be neutralized and unreferenced.
assert H(base,'app/src/main/cpp/iris26642_libheif_android16_tmap.patch')==H(cand,'app/src/main/cpp/iris26642_libheif_android16_tmap.patch')
assert 'iris26642_libheif_android16_tmap.patch' not in T('app/src/main/cpp/CMakeLists.txt')
# Do not reintroduce explicit requested MediaCodec color-aspect keys.
enc=T('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
for stale in ['format.setInteger(MediaFormat.KEY_COLOR_STANDARD','format.setInteger(MediaFormat.KEY_COLOR_TRANSFER','format.setInteger(MediaFormat.KEY_COLOR_RANGE']:
 assert stale not in enc,stale
# Android decode proof stays active for working JPEG and HEIC.
saver=T('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
assert 'iris26642ScheduleUltraHdrDecodeProof(fileToSave, "HEIC")' in saver and 'iris26642ScheduleUltraHdrDecodeProof(fileToSave, "JPEG")' in saver
# Successful 26642 HDR/IQ/performance/SHORT and filename/mode owners remain exact bytes.
for r in ['app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ImagePath.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
 assert H(base,r)==H(cand,r),r
print('PASS 26643 permanent regressions: no RAW/Battery/bracketing quick rows; glyph-only selection; no manual pill; no hybrid HEIC signaling; dependency patch parses; ISO21496 and 26642 image owners retained')
