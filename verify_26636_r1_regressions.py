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
# Real NDK failure 2026-09-13: libheif/api/libheif/heif.h includes <libheif/heif_version.h>,
# which pinned libheif generates under libheif_BINARY_DIR. The irisheic consumer must explicitly
# inherit that build-tree include root; source-tree API includes alone reproduce the exact fatal error.
iris_inc=cmake.split('target_include_directories(irisheic PRIVATE',1)[1].split('target_compile_definitions(irisheic PRIVATE',1)[0]
assert 'IRIS_26636_LIBHEIF_GENERATED_HEADER_INCLUDE' in iris_inc
assert '"${libheif_BINARY_DIR}"' in iris_inc
assert iris_inc.index('"${libheif_BINARY_DIR}"') < iris_inc.index('"${iris26636_libheif_SOURCE_DIR}/libheif/api"')
# Real NDK failure 2026-09-14: once the generated libheif header root was fixed, irisheic
# advanced into the inherited libultrahdr header graph and failed at <jerror.h>. The proven
# motionv2jpeg consumer carries BOTH libjpeg-turbo roots: source headers provide jerror.h /
# jpeglib.h, while the configured build tree provides generated jconfig.h. Preserve that exact
# transitive compile contract for irisheic; either root missing reproduces the failure chain.
assert 'IRIS_26636_LIBULTRAHDR_JPEG_HEADER_CLOSURE' in iris_inc
assert '${IRIS26507_JPEG}/src' in iris_inc
assert '${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo' in iris_inc
assert iris_inc.index('${IRIS26507_JPEG}/src') < iris_inc.index('${IRIS26507_UHDR}/lib/include')
assert iris_inc.index('${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo') < iris_inc.index('${IRIS26507_UHDR}/lib/include')
for rel in [
    'app/src/main/cpp/third_party_26507/libjpeg-turbo/src/jerror.h',
    'app/src/main/cpp/third_party_26507/libjpeg-turbo/src/jpeglib.h',
]:
    assert (C/rel).is_file(), rel
jdec=read(C,'app/src/main/cpp/third_party_26507/libultrahdr/lib/include/ultrahdr/jpegdecoderhelper.h')
jenc=read(C,'app/src/main/cpp/third_party_26507/libultrahdr/lib/include/ultrahdr/jpegencoderhelper.h')
for h in (jdec,jenc):
    assert '#include <jerror.h>' in h and '#include <jpeglib.h>' in h
assert cmake.index('add_subdirectory(${IRIS26507_JPEG} ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo)') < cmake.index('add_library(irisheic SHARED iris_heic_jni.cpp)')
assert 'target_link_libraries(irisheic PRIVATE heif iris26507-ultrahdr log jnigraphics android z)' in cmake
# Full pinned-libheif plugin ABI closure. The exact 1.19.7 commit has no public
# heif_register_encoder_plugin() API in the static/no-plugin-loading build; its compiled static
# registry exposes register_encoder()/get_encoder(). Keep the source-root include and prove Iris
# registers once, then verifies its priority-1000 HEVC plugin is the selected owner.
assert 'IRIS_26636_LIBHEIF_PINNED_REGISTRY_INCLUDE' in iris_inc
assert '"${iris26636_libheif_SOURCE_DIR}/libheif"' in iris_inc
assert '#include "plugin_registry.h"' in native
assert 'heif_register_encoder_plugin' not in native
assert 'register_encoder(&kIris26636MediaCodecHevcPlugin);' in native
assert 'get_encoder(heif_compression_HEVC) == &kIris26636MediaCodecHevcPlugin' in native
# libheif HEVC plugin packets are exactly one NAL without a start code. Java must normalize both
# Annex-B and 4-byte length-prefixed MediaCodec output before JNI returns byte[][] to the plugin.
assert 'startCodeLength(byte[] data, int p)' in hw
assert 'Arrays.copyOfRange(data, start, next)' in hw
assert 'Some codecs expose length-prefixed NALs' in hw
assert 'lengthPrefixed.add(Arrays.copyOfRange(data, p, p + n))' in hw
assert 'hasVps && hasSps && hasPps && hasImage' in hw
assert 'return nals.toArray(new byte[0][]);' in hw
assert '*data = nal.data();' in native and 'heif_encoded_data_type_HEVC_header' in native
# Pinned writer ABI is v1 and the callback includes context/data/size/userdata in that order.
assert 'static heif_error iris26636WriteCallback(heif_context*, const void* data, size_t size, void* userdata)' in native
assert 'heif_writer writer{1, iris26636WriteCallback};' in native
# HEIC EXIF must parse Photon's rational focal-length strings (e.g. 234/100), not silently treat
# the numerator as the final millimetre value.
assert 'IRIS_26636_EXIF_RATIONAL_PARSE' in native
assert "if (*end == '/')" in native
assert 'den <= 0.0' in native and 'v /= den;' in native
# Patch identity is verified as a Git blob object, not incorrectly as raw SHA1.
assert 'hash-object "${IRIS26636_LIBHEIF_PATCH}"' in cmake and 'IRIS26636_LIBHEIF_PATCH_BLOB "da5494f223f369781bbabcdaf6dbe192e0d74ca1"' in cmake
assert 'EXPECTED_HASH SHA1=da5494f223f369781bbabcdaf6dbe192e0d74ca1' not in cmake
# Standards color regression: base P3 uses the v2.0 P3/BT601 carrier; alternate tmap is P3-linear chromaticity-derived NCL.
assert 'baseNclx, heif_matrix_coefficients_ITU_R_BT_601_6' in native
assert 'alternateNclx, heif_matrix_coefficients_chromaticity_derived_non_constant_luminance' in native
# Permanent generated/runtime-scope regressions are handled by authority-seeded manifests; prove changed paths are only intended actual app source/build config.
changed=[x for x in (Path(__file__).resolve().parent/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert not any('/build/' in p or '/.cxx/' in p for p in changed)
print('PASS 26636 regressions: routing isolation; hardware-only HEVC; generated libheif + full libultrahdr/libjpeg header closure; exact pinned static plugin registry ownership; startcode-free NAL contract; writer ABI; rational EXIF; patch provenance; P3/tmap signaling')
