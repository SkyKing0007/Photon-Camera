#!/usr/bin/env python3
from __future__ import annotations
import argparse
import difflib
import hashlib
from pathlib import Path

DNG_JAVA = "app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java"
IMAGE_SAVER = "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
DNG_CPP = "app/src/main/cpp/dngCreator.cpp"
CMAKE = "app/src/main/cpp/CMakeLists.txt"
ALLOWED = {DNG_JAVA, IMAGE_SAVER, DNG_CPP, CMAKE}

TINYDNG_COMMIT = "857590b3997818a4ccfbb8a42dd21c76273d6837"
TINYDNG_BLOB = "624d614bf3e3bccb394ec54d1bca5bbb350859be"

def norm(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def one(s: str, old: str, new: str, label: str) -> str:
    n = s.count(old)
    if n != 1:
        raise AssertionError(f"{label} anchor count={n} expected=1")
    return s.replace(old, new, 1)

def read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.is_file():
        raise AssertionError(f"missing required runtime file: {rel}")
    return norm(p.read_text(encoding="utf-8"))

def dng_java_expected(text: str) -> str:
    s = norm(text)
    if "IRIS_26523_DNG_SINGLE_METADATA_OWNERSHIP" not in s:
        raise AssertionError("successful-26524 DngCreator missing inherited 26523 metadata owner")
    if "IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY" in s:
        raise AssertionError("26525 DngCreator transform already present")

    native_anchor = "    private native void setBinning(long nativePtr, boolean binning);\n"
    native_repl = native_anchor + (
        "    /* IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY */\n"
        "    private native void setDefaultCropZoom(long nativePtr, double zoom);\n"
    )
    s = one(s, native_anchor, native_repl, "DngCreator native crop setter")

    public_anchor = '''    public void setBinning(boolean binning) {
        setBinning(nativePtr, binning);
    }
'''
    public_repl = public_anchor + '''
    /**
     * IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY
     * Sets the intended centered default DNG composition while retaining the full Bayer payload.
     */
    public void setDefaultCropZoom(double zoom) {
        if (!Double.isFinite(zoom) || zoom < 1.0) {
            zoom = 1.0;
        }
        setDefaultCropZoom(nativePtr, zoom);
    }
'''
    s = one(s, public_anchor, public_repl, "DngCreator public crop setter")
    return s

def image_saver_expected(text: str) -> str:
    s = norm(text)
    marker = "IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER"
    start = s.find(marker)
    if start < 0:
        raise AssertionError("normalized16 stacked DNG writer missing")
    end = s.find("        public static boolean saveSingleRaw(", start)
    if end < 0:
        raise AssertionError("saveSingleRaw boundary after stacked DNG writer missing")
    block = s[start:end]

    for required in (
        "IRIS_26523_SINGLE_METADATA=true",
        "dngCreator.setParameters(parameters, false, false);",
        "dngCreator.setBitsPerSample(16);",
        "dngCreator.setBlackLevel(new short[]{0, 0, 0, 0});",
        "dngCreator.setWhiteLevel(65535.0);",
    ):
        if required not in block:
            raise AssertionError("successful-26524 stacked DNG writer missing " + required)
    if "setDefaultCropZoom(" in block:
        raise AssertionError("26525 stacked DNG crop call already present")

    anchor = "                dngCreator.setParameters(parameters, false, false);\n"
    repl = anchor + (
        "                /* IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY */\n"
        "                dngCreator.setDefaultCropZoom(parameters.iris26524OutputLocalZoom);\n"
    )
    block = one(block, anchor, repl, "stacked DNG frozen zoom crop handoff")
    s = s[:start] + block + s[end:]
    if s.count("dngCreator.setDefaultCropZoom(") != 1:
        raise AssertionError("DefaultCropZoom call must exist exactly once, in normalized16 stacked DNG writer")
    return s

def dng_cpp_expected(text: str) -> str:
    s = norm(text)
    if "IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY" in s:
        raise AssertionError("26525 native DNG transform already present")

    field_anchor = '''    DngMetadata metadata;
    DngCreator() {
'''
    field_repl = '''    DngMetadata metadata;
    /* IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY
     * Frozen Motion local zoom is metadata-only here: the Bayer payload remains full-size.
     */
    double default_crop_zoom = 1.0;
    DngCreator() {
'''
    s = one(s, field_anchor, field_repl, "native DNG crop field")

    setter_anchor = '''    void setBinning(bool binning) {
        metadata.binning = binning;
    }
'''
    setter_repl = setter_anchor + '''
    void setDefaultCropZoom(double zoom) {
        default_crop_zoom = (std::isfinite(zoom) && zoom >= 1.0) ? zoom : 1.0;
    }
'''
    s = one(s, setter_anchor, setter_repl, "native DNG crop setter")

    active_anchor = '''        dng_image0->SetActiveArea(new unsigned int[4]{0, 0, static_cast<unsigned int>(actualHeight), static_cast<unsigned int>(actualWidth)});
'''
    crop_code = active_anchor + '''        /* IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY
         * DNG DefaultCropOrigin/DefaultCropSize describe the same centered local zoom that
         * 26524 freezes at shutter for the Motion JPEG/UHDR output. Do not physically crop
         * or resample the stacked Bayer image. For zoomed crops, keep origin and size even
         * so the 2x2 CFA phase is unchanged.
         */
        unsigned int defaultCropOrigin[2] = {0u, 0u}; // H,V = X,Y
        unsigned int defaultCropSize[2] = {
                static_cast<unsigned int>(actualWidth),
                static_cast<unsigned int>(actualHeight)
        };
        const double cropZoom = (std::isfinite(default_crop_zoom) && default_crop_zoom >= 1.0)
                ? default_crop_zoom : 1.0;
        if (cropZoom > 1.00001 && actualWidth >= 2 && actualHeight >= 2) {
            int cropWidth = static_cast<int>(std::floor(static_cast<double>(actualWidth) / cropZoom));
            int cropHeight = static_cast<int>(std::floor(static_cast<double>(actualHeight) / cropZoom));

            const int maxEvenWidth = actualWidth & ~1;
            const int maxEvenHeight = actualHeight & ~1;
            cropWidth = std::max(2, std::min(maxEvenWidth, cropWidth & ~1));
            cropHeight = std::max(2, std::min(maxEvenHeight, cropHeight & ~1));

            int originX = ((actualWidth - cropWidth) / 2) & ~1;
            int originY = ((actualHeight - cropHeight) / 2) & ~1;
            originX = std::max(0, std::min(originX, actualWidth - cropWidth));
            originY = std::max(0, std::min(originY, actualHeight - cropHeight));

            defaultCropOrigin[0] = static_cast<unsigned int>(originX);
            defaultCropOrigin[1] = static_cast<unsigned int>(originY);
            defaultCropSize[0] = static_cast<unsigned int>(cropWidth);
            defaultCropSize[1] = static_cast<unsigned int>(cropHeight);
        }
        if (!dng_image0->SetDefaultCrop(defaultCropOrigin, defaultCropSize)) {
            LOGE("IRIS_26525_DNG_DEFAULT_CROP failed zoom=%.6f full=%dx%d", cropZoom, actualWidth, actualHeight);
            if (binnedData) {
                delete[] binnedData;
            }
            return nullptr;
        }
        LOGD("IRIS_26525_DNG_DEFAULT_CROP zoom=%.6f full=%dx%d origin=%u,%u size=%u,%u payloadResampled=false",
             cropZoom, actualWidth, actualHeight,
             defaultCropOrigin[0], defaultCropOrigin[1],
             defaultCropSize[0], defaultCropSize[1]);
'''
    s = one(s, active_anchor, crop_code, "native centered DefaultCrop")

    jni_anchor = '''    JNIEXPORT void JNICALL Java_com_particlesdevs_photoncamera_processing_DngCreator_setBinning(JNIEnv *env, jobject obj, jlong creatorPtr, jboolean binning) {
        DngCreator* creator = reinterpret_cast<DngCreator*>(creatorPtr);
        if (creator) {
            creator->setBinning(binning);
        }
    }
'''
    jni_repl = jni_anchor + '''
    JNIEXPORT void JNICALL Java_com_particlesdevs_photoncamera_processing_DngCreator_setDefaultCropZoom(JNIEnv *env, jobject obj, jlong creatorPtr, jdouble zoom) {
        DngCreator* creator = reinterpret_cast<DngCreator*>(creatorPtr);
        if (creator) {
            creator->setDefaultCropZoom(static_cast<double>(zoom));
        }
    }
'''
    s = one(s, jni_anchor, jni_repl, "native DefaultCrop JNI")
    return s

def cmake_expected(text: str) -> str:
    s = norm(text)
    if "IRIS_26525_PINNED_TINYDNG_DEFAULT_CROP" in s:
        raise AssertionError("26525 TinyDNG CMake transform already present")

    old = '''file(DOWNLOAD
        https://raw.githubusercontent.com/ParticlesDevs/tinydng/refs/heads/master/tiny_dng_writer.h
        ${CMAKE_CURRENT_SOURCE_DIR}/deps/tiny_dng_writer.h)
'''
    new = f'''# IRIS_26525_PINNED_TINYDNG_DEFAULT_CROP
set(IRIS_26525_TINYDNG_COMMIT "{TINYDNG_COMMIT}")
set(IRIS_26525_TINYDNG_BLOB_SHA "{TINYDNG_BLOB}")
set(IRIS_26525_TINYDNG_HEADER "${{CMAKE_CURRENT_SOURCE_DIR}}/deps/tiny_dng_writer.h")
file(DOWNLOAD
        "https://raw.githubusercontent.com/ParticlesDevs/tinydng/${{IRIS_26525_TINYDNG_COMMIT}}/tiny_dng_writer.h"
        "${{IRIS_26525_TINYDNG_HEADER}}"
        STATUS IRIS_26525_TINYDNG_DOWNLOAD_STATUS
        TLS_VERIFY ON)
list(GET IRIS_26525_TINYDNG_DOWNLOAD_STATUS 0 IRIS_26525_TINYDNG_STATUS_CODE)
list(GET IRIS_26525_TINYDNG_DOWNLOAD_STATUS 1 IRIS_26525_TINYDNG_STATUS_MESSAGE)
if(NOT IRIS_26525_TINYDNG_STATUS_CODE EQUAL 0)
    message(FATAL_ERROR "Pinned TinyDNG download failed: ${{IRIS_26525_TINYDNG_STATUS_MESSAGE}}")
endif()

execute_process(
        COMMAND git hash-object "${{IRIS_26525_TINYDNG_HEADER}}"
        RESULT_VARIABLE IRIS_26525_TINYDNG_HASH_RESULT
        OUTPUT_VARIABLE IRIS_26525_TINYDNG_ACTUAL_BLOB
        OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT IRIS_26525_TINYDNG_HASH_RESULT EQUAL 0)
    message(FATAL_ERROR "git hash-object failed for pinned TinyDNG header")
endif()
if(NOT IRIS_26525_TINYDNG_ACTUAL_BLOB STREQUAL IRIS_26525_TINYDNG_BLOB_SHA)
    message(FATAL_ERROR
            "Pinned TinyDNG blob mismatch: ${{IRIS_26525_TINYDNG_ACTUAL_BLOB}} != ${{IRIS_26525_TINYDNG_BLOB_SHA}}")
endif()
message(STATUS "IRIS_26525 TinyDNG exact upstream blob verified: ${{IRIS_26525_TINYDNG_ACTUAL_BLOB}}")

file(READ "${{IRIS_26525_TINYDNG_HEADER}}" IRIS_26525_TINYDNG_TEXT)

set(IRIS_26525_ENUM_OLD [=[  TIFFTAG_ACTIVE_AREA = 50829,
]=])
set(IRIS_26525_ENUM_NEW [=[  // IRIS_26525_TINYDNG_DEFAULT_CROP_TAGS
  TIFFTAG_DEFAULT_CROP_ORIGIN = 50719,
  TIFFTAG_DEFAULT_CROP_SIZE = 50720,
  TIFFTAG_ACTIVE_AREA = 50829,
]=])
string(FIND "${{IRIS_26525_TINYDNG_TEXT}}" "${{IRIS_26525_ENUM_OLD}}" IRIS_26525_ENUM_INDEX)
if(IRIS_26525_ENUM_INDEX EQUAL -1)
    message(FATAL_ERROR "TinyDNG DefaultCrop enum anchor missing")
endif()
string(REPLACE "${{IRIS_26525_ENUM_OLD}}" "${{IRIS_26525_ENUM_NEW}}"
       IRIS_26525_TINYDNG_TEXT "${{IRIS_26525_TINYDNG_TEXT}}")

set(IRIS_26525_DECL_OLD [=[  bool SetActiveArea(const unsigned int values[4]);
]=])
set(IRIS_26525_DECL_NEW [=[  bool SetActiveArea(const unsigned int values[4]);
  // IRIS_26525_TINYDNG_DEFAULT_CROP_API
  bool SetDefaultCrop(const unsigned int origin[2],
                      const unsigned int size[2]);
]=])
string(FIND "${{IRIS_26525_TINYDNG_TEXT}}" "${{IRIS_26525_DECL_OLD}}" IRIS_26525_DECL_INDEX)
if(IRIS_26525_DECL_INDEX EQUAL -1)
    message(FATAL_ERROR "TinyDNG DefaultCrop declaration anchor missing")
endif()
string(REPLACE "${{IRIS_26525_DECL_OLD}}" "${{IRIS_26525_DECL_NEW}}"
       IRIS_26525_TINYDNG_TEXT "${{IRIS_26525_TINYDNG_TEXT}}")

set(IRIS_26525_IMPL_OLD [=[bool DNGImage::SetActiveArea(const unsigned int values[4]) {{
  unsigned int count = 4;

  const unsigned int *data = values;
  bool ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_ACTIVE_AREA), TIFF_LONG, count,
      reinterpret_cast<const unsigned char *>(data), &ifd_tags_, &data_os_);

  if (!ret) {{
    return false;
  }}

  num_fields_++;
  return true;
}}
]=])
set(IRIS_26525_IMPL_NEW [=[bool DNGImage::SetActiveArea(const unsigned int values[4]) {{
  unsigned int count = 4;

  const unsigned int *data = values;
  bool ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_ACTIVE_AREA), TIFF_LONG, count,
      reinterpret_cast<const unsigned char *>(data), &ifd_tags_, &data_os_);

  if (!ret) {{
    return false;
  }}

  num_fields_++;
  return true;
}}

// IRIS_26525_TINYDNG_DEFAULT_CROP_IMPL
bool DNGImage::SetDefaultCrop(const unsigned int origin[2],
                              const unsigned int size[2]) {{
  if ((size[0] == 0) || (size[1] == 0)) {{
    err_ += "DefaultCrop size must be non-zero.\\n";
    return false;
  }}

  bool origin_ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_DEFAULT_CROP_ORIGIN), TIFF_LONG, 2,
      reinterpret_cast<const unsigned char *>(origin), &ifd_tags_, &data_os_);
  if (!origin_ret) {{
    err_ += "Failed to write DefaultCropOrigin.\\n";
    return false;
  }}
  num_fields_++;

  bool size_ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_DEFAULT_CROP_SIZE), TIFF_LONG, 2,
      reinterpret_cast<const unsigned char *>(size), &ifd_tags_, &data_os_);
  if (!size_ret) {{
    err_ += "Failed to write DefaultCropSize.\\n";
    return false;
  }}
  num_fields_++;
  return true;
}}
]=])
string(FIND "${{IRIS_26525_TINYDNG_TEXT}}" "${{IRIS_26525_IMPL_OLD}}" IRIS_26525_IMPL_INDEX)
if(IRIS_26525_IMPL_INDEX EQUAL -1)
    message(FATAL_ERROR "TinyDNG DefaultCrop implementation anchor missing")
endif()
string(REPLACE "${{IRIS_26525_IMPL_OLD}}" "${{IRIS_26525_IMPL_NEW}}"
       IRIS_26525_TINYDNG_TEXT "${{IRIS_26525_TINYDNG_TEXT}}")

file(WRITE "${{IRIS_26525_TINYDNG_HEADER}}" "${{IRIS_26525_TINYDNG_TEXT}}")
'''
    return one(s, old, new, "CMake pinned TinyDNG DefaultCrop extension")

def transformed(root: Path) -> dict[str, str]:
    return {
        DNG_JAVA: dng_java_expected(read(root, DNG_JAVA)),
        IMAGE_SAVER: image_saver_expected(read(root, IMAGE_SAVER)),
        DNG_CPP: dng_cpp_expected(read(root, DNG_CPP)),
        CMAKE: cmake_expected(read(root, CMAKE)),
    }

def tree_files(root: Path) -> dict[str, str]:
    out = {}
    main = root / "app/src/main"
    if main.is_dir():
        for p in main.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(root)).replace("\\", "/")
                out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    v = root / "app/version.properties"
    if v.is_file():
        out["app/version.properties"] = hashlib.sha256(v.read_bytes()).hexdigest()
    return out

def write_patch(root: Path, outputs: dict[str, str], patch_path: Path) -> None:
    chunks = []
    for rel in sorted(outputs):
        old = read(root, rel).splitlines(True)
        new = outputs[rel].splitlines(True)
        chunks.extend(difflib.unified_diff(old, new, fromfile="a/" + rel, tofile="b/" + rel))
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text("".join(chunks), encoding="utf-8")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--patch-out", type=Path)
    ap.add_argument("--patch-sha-out", type=Path)
    args = ap.parse_args()

    outputs = transformed(args.root)
    if set(outputs) != ALLOWED:
        raise AssertionError("transform output allowlist mismatch")

    before = tree_files(args.root)
    simulated = dict(before)
    for rel, text in outputs.items():
        simulated[rel] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = {p for p in set(before) | set(simulated) if before.get(p) != simulated.get(p)}
    if changed != ALLOWED:
        raise AssertionError("in-memory changed-file scope mismatch: " + repr(sorted(changed)))

    if args.patch_out:
        write_patch(args.root, outputs, args.patch_out)
        if args.patch_sha_out:
            digest = hashlib.sha256(args.patch_out.read_bytes()).hexdigest()
            args.patch_sha_out.parent.mkdir(parents=True, exist_ok=True)
            args.patch_sha_out.write_text(f"{digest}  {args.patch_out.name}\n", encoding="utf-8")

    print("PASS: 26525 complete DNG zoom-parity transform resolved in memory")
    print("changed_files=4")
    for rel in sorted(ALLOWED):
        print(rel)

    if args.check_only:
        return

    for rel, text in outputs.items():
        (args.root / rel).write_text(text, encoding="utf-8")
    print("PASS: 26525 DNG zoom-parity transform applied")

if __name__ == "__main__":
    main()
