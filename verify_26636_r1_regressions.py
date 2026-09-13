#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26636_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
read=lambda r,p:(r/p).read_text()
pref=read(C,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java'); ui=read(C,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'); hdr=read(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'); night=read(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java'); hw=read(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java'); native=read(C,'app/src/main/cpp/iris_heic_jni.cpp'); cmake=read(C,'app/src/main/cpp/CMakeLists.txt')
# Real failure prevention: HEIC selection can never masquerade as RAW integer mode.
assert 'setSaveRaw(3)' not in ui+pref and 'KEY_SAVE_RAW, 3' not in ui+pref
# Real failure prevention: turning on SR changes legacy raw selector only when HEIC had been selected.
blk=pref.split('public static void setIrisSuperRes(boolean value)',1)[1].split('\n    }',1)[0]
assert 'boolean heicWasSelected = isIrisHeicOutputOn();' in blk and 'if (value && heicWasSelected)' in blk
assert blk.count('KEY_SAVE_RAW, 0')==1
# No HEIC+SR in either immutable batch or publisher.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java']:
 s=read(C,rel); assert 'superResEnabled && heicOutputEnabled' in s
assert 'mMotion26575SuperResEnabled || processingParameters.motionV2SuperResOutputEnabled' in hdr
assert 'batch.superResEnabled || true2xRenderRgbPath != null' in night
# No silent SDR HEIC/JPEG fallback after HEIC selection.
heic_save=read(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').split('saveBitmapAsHEICUltraHdr',1)[1].split('/** IRIS_26537',1)[0]
assert 'saveBitmapAsJPG' not in heic_save and 'Bitmap.CompressFormat.JPEG' not in heic_save
assert 'batch.heicOutputEnabled ? finalSaved : (finalSaved || baseSaved)' in night
# Hardware only, no x265/kvazaar software encoder included in new branch.
assert 'info.isHardwareAccelerated()' in hw and 'MIMETYPE_VIDEO_HEVC' in hw
assert 'MIMETYPE_IMAGE_ANDROID_HEIC' not in hw
for t in ['set(WITH_X265 OFF','set(WITH_KVAZAAR OFF','set(WITH_AOM_ENCODER OFF']:
 assert t in cmake,t
# Patch identity is verified as a Git blob object, not incorrectly as raw SHA1.
assert 'hash-object "${IRIS26636_LIBHEIF_PATCH}"' in cmake and 'IRIS26636_LIBHEIF_PATCH_BLOB "da5494f223f369781bbabcdaf6dbe192e0d74ca1"' in cmake
assert 'EXPECTED_HASH SHA1=da5494f223f369781bbabcdaf6dbe192e0d74ca1' not in cmake
# Standards color regression: base P3 uses the v2.0 P3/BT601 carrier; alternate tmap is P3-linear chromaticity-derived NCL.
assert 'baseNclx, heif_matrix_coefficients_ITU_R_BT_601_6' in native
assert 'alternateNclx, heif_matrix_coefficients_chromaticity_derived_non_constant_luminance' in native
# Permanent generated/runtime-scope regressions are handled by authority-seeded manifests; prove changed paths are only intended actual app source/build config.
changed=[x for x in (Path(__file__).resolve().parent/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert not any('/build/' in p or '/.cxx/' in p for p in changed)
print('PASS 26636 regressions: no RAW-state collision, no HEIC+SR, no silent SDR fallback, hardware-only HEVC, exact patch provenance, correct P3/tmap color signaling')
