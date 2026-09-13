#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys, xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26636_r1.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; added=set(x for x in (root/'R1_26636_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x)
assert len(changed)==18 and len(set(changed))==18 and len(added)==3
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(r): return {str(p.relative_to(r)):H(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b,c=files(B),files(C); assert len(b)==1713 and len(c)==1716; actual={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}; assert actual==set(changed),sorted(actual^set(changed)); assert set(c)-set(b)==added
for line in (root/'R1_26636_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines():
 if line.strip(): d,rel=line.split('  ',1); assert H(C/rel)==d,rel
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726636' in v and 'VERSION_BUILD=26636' in v
# UI is the exact existing LiquidGlassMenuText family, not a new widget/style system.
xml=C/'app/src/main/res/layout/camera_fragment.xml'; ET.parse(xml); x=xml.read_text();
for t in ['@+id/format_jpg_button','@+id/format_raw_button','@+id/format_raw_jpg_button','@+id/format_heic_button','style="@style/LiquidGlassMenuText"','android:text="HEIC"']: assert t in x,t
heic_block=x.split('android:id="@+id/format_heic_button"',1)[1].split('/>',1)[0]; assert 'style="@style/LiquidGlassMenuText"' in heic_block and 'android:visibility="gone"' in heic_block
ui=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text(); pref=(C/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text()
for t in ['mode == CameraMode.MOTION || mode == CameraMode.NIGHT','!PreferenceKeys.isIrisSuperResOn()','IrisHardwareHevcEncoder.isHeicUltraHdrAvailable()','formatHeicButton.setVisibility(heicAllowed ? View.VISIBLE : View.GONE)','PreferenceKeys.setIrisHeicOutput(true)']: assert t in ui,t
for t in ['KEY_IRIS_HEIC_OUTPUT','isIrisHeicOutputOn()','setIrisHeicOutput(boolean value)','if (value && isIrisSuperResOn()) value = false','boolean heicWasSelected = isIrisHeicOutputOn()','if (value && heicWasSelected)']: assert t in pref,t
assert 'if (value) preferenceKeys.settingsManager.set(SCOPE_GLOBAL, Key.KEY_SAVE_RAW, 0);' in pref
# Existing raw integer remains 0/1/2 authority; no fourth numeric value is introduced.
assert not re.search(r'setSaveRaw\(3\)|KEY_SAVE_RAW\s*,\s*3',ui+pref)
# Immutable capture ownership.
for rel,need in [
 ('app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',['final boolean heicOutputEnabled','superResEnabled && heicOutputEnabled']),
 ('app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',['final boolean heicOutputEnabled','superResEnabled && heicOutputEnabled']),
 ('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',['mMotion26636HeicAtShutter','mIrisNight26636Heic','PreferenceKeys.isIrisHeicOutputOn()']),
 ('app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java',['batch.heicOutputEnabled']),
]:
 s=(C/rel).read_text();
 for t in need: assert t in s,(rel,t)
# Publication-only routing and explicit SR exclusion.
hdr=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text(); night=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text(); saver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
for t in ['mMotion26636HeicOutputEnabled','saveBitmapAsHEICUltraHdr','26636 HEIC must not enter true-2x publication']: assert t in hdr,t
assert hdr.find('saveBitmapAsHEICUltraHdr') > hdr.find('pipeline.RunMotionV2FloatCfa'), 'HEIC must be downstream of completed Motion presentation'
for t in ['IrisNightUltraHdr.attachPostJin','saveBitmapAsHEICUltraHdr','26636 Night HEIC/SuperRes invariant violated']: assert t in night,t
assert night.find('IrisNightUltraHdr.attachPostJin') < night.find('saveBitmapAsHEICUltraHdr'), 'Night HEIC must use post-Jin attached/rebased gain map'
assert 'IRIS_26636_ISOLATED_HEIC_ULTRA_HDR_PUBLICATION' in saver and '.write(fileToSave, img, quality, exifData)' in saver
# Exact P3 publication conversion + existing gain map; no recompute in HEIC Java.
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java').read_text(); hw=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java').read_text(); native=(C/'app/src/main/cpp/iris_heic_jni.cpp').read_text(); cmake=(C/'app/src/main/cpp/CMakeLists.txt').read_text()
for t in ['completedSdr.hasGainmap()','completedSdr.getGainmap()','MotionV2Jpeg444Encoder.toDisplayP3BitmapCopy(completedSdr)','ColorSpace.Named.DISPLAY_P3','gm.getGainmapContents()']: assert t in enc,t
for forbidden in ['new Gainmap(','MotionV2UltraHdr.attach','UltraHdrSaver.save','createGainmapBitmap']:
 assert forbidden not in enc,forbidden
# Android 16 hardware HEVC-only contract; no dedicated opaque HEIC codec and no software fallback.
for t in ['Build.VERSION.SDK_INT < 36','MediaFormat.MIMETYPE_VIDEO_HEVC','info.isHardwareAccelerated()','COLOR_FormatYUV420Flexible','softwareFallback=false','dedicatedHeicCodec=false']: assert t in hw,t
for forbidden in ['MIMETYPE_IMAGE_ANDROID_HEIC','SOFTWARE_ENCODER','x265','kvazaar']:
 assert forbidden not in hw,forbidden
# ISO 21496-1 container authority / color signaling.
for t in ['heif_context_encode_gain_map_image','gainmapMetadataFloatToFraction','encodeGainmapMetadata','UHDR_CG_DISPLAY_P3','heif_color_primaries_SMPTE_EG_432_1','heif_transfer_characteristic_linear','heif_matrix_coefficients_chromaticity_derived_non_constant_luminance','metadata.use_base_cg = 1','heif_register_encoder_plugin']: assert t in native,t
assert 'heif_matrix_coefficients_ITU_R_BT_601_6' in native
# Exact dependency authority, patch-object verification, and all software HEVC disabled. CMake block is after proven native owners.
for t in ['4a3f74bc593ebfc29becc1ed5dd0a61cc66d40e1','da5494f223f369781bbabcdaf6dbe192e0d74ca1','hash-object','WITH_EXPERIMENTAL_GAIN_MAP ON','WITH_X265 OFF','WITH_KVAZAAR OFF','add_library(irisheic SHARED iris_heic_jni.cpp)']: assert t in cmake,t
assert cmake.find('add_subdirectory(mgc1271_upstream)') < cmake.find('IRIS_26636_ISOLATED_HEIC_ULTRA_HDR_NATIVE_OWNER')
# Super-Res implementation owners and 26635 highlight owners are not changed by 26636.
for rel in [
 'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
 'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt']:
 assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
print('PASS 26636 semantics: HEIC publication/UI only; Motion+Night frozen routing; Super Res/JPEG-R/26635 image pipeline protected; hardware HEVC + ISO gain-map container authority')
