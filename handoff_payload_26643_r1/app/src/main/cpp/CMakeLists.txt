cmake_minimum_required(VERSION 3.6)

project(dngCreator)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_link_options("-Wl,-z,max-page-size=16384")

file(READ ${CMAKE_CURRENT_SOURCE_DIR}/../../../version.properties ver)
string(REGEX MATCH "VERSION_BUILD=([0-9]*)" _ ${ver})
set(VERSION_BUILD ${CMAKE_MATCH_1})
string(REGEX MATCH "VERSION_NAME=([0-9,.]*)" _ ${ver})
set(VERSION_NAME ${CMAKE_MATCH_1})

# IRIS_26525_PINNED_TINYDNG_DEFAULT_CROP
set(IRIS_26525_TINYDNG_COMMIT "857590b3997818a4ccfbb8a42dd21c76273d6837")
set(IRIS_26525_TINYDNG_BLOB_SHA "624d614bf3e3bccb394ec54d1bca5bbb350859be")
set(IRIS_26525_TINYDNG_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/deps/tiny_dng_writer.h")
file(DOWNLOAD
        "https://raw.githubusercontent.com/ParticlesDevs/tinydng/${IRIS_26525_TINYDNG_COMMIT}/tiny_dng_writer.h"
        "${IRIS_26525_TINYDNG_HEADER}"
        STATUS IRIS_26525_TINYDNG_DOWNLOAD_STATUS
        TLS_VERIFY ON)
list(GET IRIS_26525_TINYDNG_DOWNLOAD_STATUS 0 IRIS_26525_TINYDNG_STATUS_CODE)
list(GET IRIS_26525_TINYDNG_DOWNLOAD_STATUS 1 IRIS_26525_TINYDNG_STATUS_MESSAGE)
if(NOT IRIS_26525_TINYDNG_STATUS_CODE EQUAL 0)
    message(FATAL_ERROR "Pinned TinyDNG download failed: ${IRIS_26525_TINYDNG_STATUS_MESSAGE}")
endif()

execute_process(
        COMMAND git hash-object "${IRIS_26525_TINYDNG_HEADER}"
        RESULT_VARIABLE IRIS_26525_TINYDNG_HASH_RESULT
        OUTPUT_VARIABLE IRIS_26525_TINYDNG_ACTUAL_BLOB
        OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT IRIS_26525_TINYDNG_HASH_RESULT EQUAL 0)
    message(FATAL_ERROR "git hash-object failed for pinned TinyDNG header")
endif()
if(NOT IRIS_26525_TINYDNG_ACTUAL_BLOB STREQUAL IRIS_26525_TINYDNG_BLOB_SHA)
    message(FATAL_ERROR
            "Pinned TinyDNG blob mismatch: ${IRIS_26525_TINYDNG_ACTUAL_BLOB} != ${IRIS_26525_TINYDNG_BLOB_SHA}")
endif()
message(STATUS "IRIS_26525 TinyDNG exact upstream blob verified: ${IRIS_26525_TINYDNG_ACTUAL_BLOB}")

file(READ "${IRIS_26525_TINYDNG_HEADER}" IRIS_26525_TINYDNG_TEXT)

set(IRIS_26525_ENUM_OLD [=[  TIFFTAG_ACTIVE_AREA = 50829,
]=])
set(IRIS_26525_ENUM_NEW [=[  // IRIS_26525_TINYDNG_DEFAULT_CROP_TAGS
  TIFFTAG_DEFAULT_CROP_ORIGIN = 50719,
  TIFFTAG_DEFAULT_CROP_SIZE = 50720,
  TIFFTAG_ACTIVE_AREA = 50829,
]=])
string(FIND "${IRIS_26525_TINYDNG_TEXT}" "${IRIS_26525_ENUM_OLD}" IRIS_26525_ENUM_INDEX)
if(IRIS_26525_ENUM_INDEX EQUAL -1)
    message(FATAL_ERROR "TinyDNG DefaultCrop enum anchor missing")
endif()
string(REPLACE "${IRIS_26525_ENUM_OLD}" "${IRIS_26525_ENUM_NEW}"
       IRIS_26525_TINYDNG_TEXT "${IRIS_26525_TINYDNG_TEXT}")

set(IRIS_26525_DECL_OLD [=[  bool SetActiveArea(const unsigned int values[4]);
]=])
set(IRIS_26525_DECL_NEW [=[  bool SetActiveArea(const unsigned int values[4]);
  // IRIS_26525_TINYDNG_DEFAULT_CROP_API
  bool SetDefaultCrop(const unsigned int origin[2],
                      const unsigned int size[2]);
]=])
string(FIND "${IRIS_26525_TINYDNG_TEXT}" "${IRIS_26525_DECL_OLD}" IRIS_26525_DECL_INDEX)
if(IRIS_26525_DECL_INDEX EQUAL -1)
    message(FATAL_ERROR "TinyDNG DefaultCrop declaration anchor missing")
endif()
string(REPLACE "${IRIS_26525_DECL_OLD}" "${IRIS_26525_DECL_NEW}"
       IRIS_26525_TINYDNG_TEXT "${IRIS_26525_TINYDNG_TEXT}")

set(IRIS_26525_IMPL_OLD [=[bool DNGImage::SetActiveArea(const unsigned int values[4]) {
  unsigned int count = 4;

  const unsigned int *data = values;
  bool ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_ACTIVE_AREA), TIFF_LONG, count,
      reinterpret_cast<const unsigned char *>(data), &ifd_tags_, &data_os_);

  if (!ret) {
    return false;
  }

  num_fields_++;
  return true;
}
]=])
set(IRIS_26525_IMPL_NEW [=[bool DNGImage::SetActiveArea(const unsigned int values[4]) {
  unsigned int count = 4;

  const unsigned int *data = values;
  bool ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_ACTIVE_AREA), TIFF_LONG, count,
      reinterpret_cast<const unsigned char *>(data), &ifd_tags_, &data_os_);

  if (!ret) {
    return false;
  }

  num_fields_++;
  return true;
}

// IRIS_26525_TINYDNG_DEFAULT_CROP_IMPL
bool DNGImage::SetDefaultCrop(const unsigned int origin[2],
                              const unsigned int size[2]) {
  if ((size[0] == 0) || (size[1] == 0)) {
    err_ += "DefaultCrop size must be non-zero.\n";
    return false;
  }

  bool origin_ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_DEFAULT_CROP_ORIGIN), TIFF_LONG, 2,
      reinterpret_cast<const unsigned char *>(origin), &ifd_tags_, &data_os_);
  if (!origin_ret) {
    err_ += "Failed to write DefaultCropOrigin.\n";
    return false;
  }
  num_fields_++;

  bool size_ret = WriteTIFFTag(
      static_cast<unsigned short>(TIFFTAG_DEFAULT_CROP_SIZE), TIFF_LONG, 2,
      reinterpret_cast<const unsigned char *>(size), &ifd_tags_, &data_os_);
  if (!size_ret) {
    err_ += "Failed to write DefaultCropSize.\n";
    return false;
  }
  num_fields_++;
  return true;
}
]=])
string(FIND "${IRIS_26525_TINYDNG_TEXT}" "${IRIS_26525_IMPL_OLD}" IRIS_26525_IMPL_INDEX)
if(IRIS_26525_IMPL_INDEX EQUAL -1)
    message(FATAL_ERROR "TinyDNG DefaultCrop implementation anchor missing")
endif()
string(REPLACE "${IRIS_26525_IMPL_OLD}" "${IRIS_26525_IMPL_NEW}"
       IRIS_26525_TINYDNG_TEXT "${IRIS_26525_TINYDNG_TEXT}")

file(WRITE "${IRIS_26525_TINYDNG_HEADER}" "${IRIS_26525_TINYDNG_TEXT}")

set(TECHNICALLYFLAC_HEADER ${CMAKE_CURRENT_SOURCE_DIR}/deps/technicallyflac.h)

if(NOT EXISTS ${TECHNICALLYFLAC_HEADER})
    file(DOWNLOAD
            https://raw.githubusercontent.com/Aritile/technicallyflac/main/technicallyflac.h
            ${TECHNICALLYFLAC_HEADER}
            STATUS TECHNICALLYFLAC_DOWNLOAD_STATUS
            TLS_VERIFY ON)
    list(GET TECHNICALLYFLAC_DOWNLOAD_STATUS 0 TECHNICALLYFLAC_STATUS_CODE)
    list(GET TECHNICALLYFLAC_DOWNLOAD_STATUS 1 TECHNICALLYFLAC_STATUS_MESSAGE)
    if(NOT TECHNICALLYFLAC_STATUS_CODE EQUAL 0)
        message(FATAL_ERROR
                "technicallyflac download failed: ${TECHNICALLYFLAC_STATUS_MESSAGE}")
    endif()
endif()

file(SIZE ${TECHNICALLYFLAC_HEADER} TECHNICALLYFLAC_HEADER_SIZE)
if(TECHNICALLYFLAC_HEADER_SIZE EQUAL 0)
    message(FATAL_ERROR "technicallyflac header is empty")
endif()

if(NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/deps/archive.h)
    file(DOWNLOAD
            https://raw.githubusercontent.com/libarchive/libarchive/master/libarchive/archive.h
            ${CMAKE_CURRENT_SOURCE_DIR}/deps/archive.h)
endif()

if(NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/deps/archive_entry.h)
    file(DOWNLOAD
            https://raw.githubusercontent.com/libarchive/libarchive/master/libarchive/archive_entry.h
            ${CMAKE_CURRENT_SOURCE_DIR}/deps/archive_entry.h)
endif()

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/deps)

set(SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR})
add_library(${CMAKE_PROJECT_NAME} SHARED
    ${SRC_DIR}/dngCreator.cpp
)
add_library(allocator SHARED
    ${SRC_DIR}/allocator.cpp
)
add_library(flacRecorder SHARED
    ${SRC_DIR}/flacRecorder.cpp
)
add_library(
        camera2native SHARED ${SRC_DIR}/native-engine.cpp
)

target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
        VERSION_BUILD="${VERSION_BUILD}"
        VERSION_NAME="${VERSION_NAME}"
)

target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE
        log
        dl
)

target_link_libraries(allocator PRIVATE
        log
)

target_link_libraries(flacRecorder PRIVATE
        log
)

target_link_libraries(
        camera2native
        log
)

# IRIS_26507_TRUE_JPEG444_JPEGR
set(IRIS26507_THIRD_PARTY ${CMAKE_CURRENT_SOURCE_DIR}/third_party_26507)
set(IRIS26507_JPEG ${IRIS26507_THIRD_PARTY}/libjpeg-turbo)
set(IRIS26507_UHDR ${IRIS26507_THIRD_PARTY}/libultrahdr)
if(NOT EXISTS ${IRIS26507_JPEG}/CMakeLists.txt)
    message(FATAL_ERROR "26507 pinned libjpeg-turbo source missing")
endif()
# IRIS_26507_V3_NATIVE_DEPENDENCY_LAYOUT_PROOF
# libultrahdr exposes ultrahdr_api.h from its source root; lib/include contains
# the internal ultrahdr/* headers. Match the pinned bjzhou build contract exactly.
if(NOT EXISTS ${IRIS26507_UHDR}/ultrahdr_api.h)
    message(FATAL_ERROR "26507 pinned libultrahdr root ultrahdr_api.h missing")
endif()
if(NOT EXISTS ${IRIS26507_UHDR}/lib/src/ultrahdr_api.cpp)
    message(FATAL_ERROR "26507 pinned libultrahdr core source missing")
endif()
set(ENABLE_SHARED OFF CACHE BOOL "" FORCE)
set(ENABLE_STATIC ON CACHE BOOL "" FORCE)
set(WITH_TURBOJPEG ON CACHE BOOL "" FORCE)
set(WITH_TESTS OFF CACHE BOOL "" FORCE)
set(WITH_TOOLS OFF CACHE BOOL "" FORCE)
set(WITH_JAVA OFF CACHE BOOL "" FORCE)
set(REQUIRE_SIMD ON CACHE BOOL "" FORCE)
set(WITH_SIMD ON CACHE BOOL "" FORCE)
add_subdirectory(${IRIS26507_JPEG} ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo)
find_package(Threads REQUIRED)
file(GLOB IRIS26507_UHDR_CORE "${IRIS26507_UHDR}/lib/src/*.cpp")
file(GLOB IRIS26507_UHDR_NEON "${IRIS26507_UHDR}/lib/src/dsp/arm/*.cpp")
file(GLOB_RECURSE IRIS26507_UHDR_IMAGE_IO "${IRIS26507_UHDR}/third_party/image_io/src/*.cc")
add_library(iris26507-ultrahdr STATIC ${IRIS26507_UHDR_CORE} ${IRIS26507_UHDR_NEON} ${IRIS26507_UHDR_IMAGE_IO})
set_target_properties(iris26507-ultrahdr PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_include_directories(iris26507-ultrahdr PRIVATE
    ${IRIS26507_UHDR}/lib/include
    ${IRIS26507_UHDR}/third_party/image_io/includes
    ${IRIS26507_UHDR}/third_party/image_io/src/modp_b64
    ${IRIS26507_UHDR}/third_party/image_io/src/modp_b64/modp_b64
    ${IRIS26507_JPEG}/src
    ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo
    PUBLIC ${IRIS26507_UHDR})
target_compile_definitions(iris26507-ultrahdr PRIVATE UHDR_ENABLE_INTRINSICS UHDR_WRITE_ISO UHDR_WRITE_XMP)
target_compile_options(iris26507-ultrahdr PRIVATE -O3 -fno-lax-vector-conversions)
target_link_libraries(iris26507-ultrahdr PRIVATE jpeg-static Threads::Threads log z)
add_library(motionv2jpeg SHARED motionv2_jpeg444_jni.cpp motionv2_jpeg_r_encoder.cpp)
set_target_properties(motionv2jpeg PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_include_directories(motionv2jpeg PRIVATE
    ${IRIS26507_JPEG}/src
    ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo
    ${IRIS26507_UHDR}
    ${IRIS26507_UHDR}/lib/include
    ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(motionv2jpeg PRIVATE turbojpeg-static jpeg-static iris26507-ultrahdr log jnigraphics android z EGL GLESv3)

# IRIS_26512_MGC1271_ISOLATED_NATIVE_OWNER
add_subdirectory(mgc1271_upstream)

# IRIS_26636_ISOLATED_HEIC_ULTRA_HDR_NATIVE_OWNER
# Keep the proven iris26507 libultrahdr/JPEG-R publisher byte-for-byte independent. HEIC uses a
# sibling gain-map-capable HEIF container pinned to the exact libultrahdr-2.0.0 libheif authority,
# while an Iris encoder plugin delegates HEVC compression to Android hardware MediaCodec.
include(FetchContent)
find_package(Git REQUIRED)
set(IRIS26636_LIBHEIF_COMMIT "4a3f74bc593ebfc29becc1ed5dd0a61cc66d40e1")
set(IRIS26636_LIBHEIF_PATCH_BLOB "da5494f223f369781bbabcdaf6dbe192e0d74ca1")
set(IRIS26636_LIBHEIF_PATCH "${CMAKE_CURRENT_BINARY_DIR}/iris26636_libheif_pr1503.patch")
# IRIS_26643_AOSP_ANDROID16_HEIC_CONTAINER_OWNER: one deterministic correction applied only
# after the exact pinned Google/libultrahdr patch. Android 16 HeicCompositeStream/MPEG4Writer
# is the sole publication authority: 8-bit tmap PIXI, visible gain item, essential IPMA,
# and HEIC brands mif1/heic/tmap (no standalone-libheif miaf hybrid).
set(IRIS26643_LIBHEIF_AOSP_PATCH "${CMAKE_CURRENT_SOURCE_DIR}/iris26643_libheif_aosp_contract.patch")
set(IRIS26643_LIBHEIF_AOSP_PATCH_SHA256 "e1fbbfcb926fe1879e1416b11f4f35bd586e480659d1ca6daa45798b666d856a")
file(SHA256 "${IRIS26643_LIBHEIF_AOSP_PATCH}" IRIS26643_LIBHEIF_AOSP_PATCH_ACTUAL_SHA256)
if(NOT IRIS26643_LIBHEIF_AOSP_PATCH_ACTUAL_SHA256 STREQUAL IRIS26643_LIBHEIF_AOSP_PATCH_SHA256)
    message(FATAL_ERROR
        "IRIS_26643 local libheif AOSP contract patch mismatch: ${IRIS26643_LIBHEIF_AOSP_PATCH_ACTUAL_SHA256} != ${IRIS26643_LIBHEIF_AOSP_PATCH_SHA256}")
endif()
file(DOWNLOAD
    "https://raw.githubusercontent.com/google/libultrahdr/v2.0.0/cmake/patches/libheif_pr1503.patch"
    "${IRIS26636_LIBHEIF_PATCH}"
    STATUS IRIS26636_PATCH_STATUS
    TLS_VERIFY ON)
list(GET IRIS26636_PATCH_STATUS 0 IRIS26636_PATCH_STATUS_CODE)
list(GET IRIS26636_PATCH_STATUS 1 IRIS26636_PATCH_STATUS_MESSAGE)
if(NOT IRIS26636_PATCH_STATUS_CODE EQUAL 0)
    message(FATAL_ERROR "IRIS_26636 pinned libheif gain-map patch download failed: ${IRIS26636_PATCH_STATUS_MESSAGE}")
endif()
execute_process(
    COMMAND ${GIT_EXECUTABLE} hash-object "${IRIS26636_LIBHEIF_PATCH}"
    RESULT_VARIABLE IRIS26636_PATCH_HASH_RESULT
    OUTPUT_VARIABLE IRIS26636_PATCH_ACTUAL_BLOB
    OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT IRIS26636_PATCH_HASH_RESULT EQUAL 0 OR
   NOT IRIS26636_PATCH_ACTUAL_BLOB STREQUAL IRIS26636_LIBHEIF_PATCH_BLOB)
    message(FATAL_ERROR
        "IRIS_26636 libheif patch authority mismatch: ${IRIS26636_PATCH_ACTUAL_BLOB} != ${IRIS26636_LIBHEIF_PATCH_BLOB}")
endif()

# No software image/video codec is allowed into the HEIC publication branch.
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(WITH_EXAMPLES OFF CACHE BOOL "" FORCE)
set(WITH_DOCS OFF CACHE BOOL "" FORCE)
set(ENABLE_PLUGIN_LOADING OFF CACHE BOOL "" FORCE)
set(WITH_LIBDE265 OFF CACHE BOOL "" FORCE)
set(WITH_X265 OFF CACHE BOOL "" FORCE)
set(WITH_X265_PLUGIN OFF CACHE BOOL "" FORCE)
set(WITH_KVAZAAR OFF CACHE BOOL "" FORCE)
set(WITH_KVAZAAR_PLUGIN OFF CACHE BOOL "" FORCE)
set(WITH_UVG266 OFF CACHE BOOL "" FORCE)
set(WITH_VVDEC OFF CACHE BOOL "" FORCE)
set(WITH_VVENC OFF CACHE BOOL "" FORCE)
set(WITH_OpenH264_DECODER OFF CACHE BOOL "" FORCE)
set(WITH_AOM_DECODER OFF CACHE BOOL "" FORCE)
set(WITH_AOM_ENCODER OFF CACHE BOOL "" FORCE)
set(WITH_DAV1D OFF CACHE BOOL "" FORCE)
set(WITH_SvtEnc OFF CACHE BOOL "" FORCE)
set(WITH_RAV1E OFF CACHE BOOL "" FORCE)
set(WITH_JPEG_DECODER OFF CACHE BOOL "" FORCE)
set(WITH_JPEG_ENCODER OFF CACHE BOOL "" FORCE)
set(WITH_OpenJPEG_ENCODER OFF CACHE BOOL "" FORCE)
set(WITH_OpenJPEG_DECODER OFF CACHE BOOL "" FORCE)
set(WITH_OPENJPH_ENCODER OFF CACHE BOOL "" FORCE)
set(WITH_FFMPEG_DECODER OFF CACHE BOOL "" FORCE)
set(WITH_UNCOMPRESSED_CODEC OFF CACHE BOOL "" FORCE)
set(WITH_EXPERIMENTAL_GAIN_MAP ON CACHE BOOL "" FORCE)

FetchContent_Declare(iris26636_libheif
    GIT_REPOSITORY https://github.com/strukturag/libheif.git
    GIT_TAG ${IRIS26636_LIBHEIF_COMMIT}
    GIT_SHALLOW FALSE
    GIT_PROGRESS FALSE
    PATCH_COMMAND ${GIT_EXECUTABLE} apply --ignore-space-change --whitespace=nowarn "${IRIS26636_LIBHEIF_PATCH}"
    # IRIS_26643_PINNED_V2_LIBHEIF_PATCH_REPLAY: permanent regression for Actions run 34987275178.
    # Check the 26643 correction against the exact post-v2.0.0-PR1503 tree before mutating it.
    COMMAND ${GIT_EXECUTABLE} apply --check --ignore-space-change --whitespace=nowarn "${IRIS26643_LIBHEIF_AOSP_PATCH}"
    COMMAND ${GIT_EXECUTABLE} apply --ignore-space-change --whitespace=nowarn "${IRIS26643_LIBHEIF_AOSP_PATCH}")
FetchContent_MakeAvailable(iris26636_libheif)
execute_process(
    COMMAND ${GIT_EXECUTABLE} rev-parse HEAD
    WORKING_DIRECTORY "${iris26636_libheif_SOURCE_DIR}"
    RESULT_VARIABLE IRIS26636_LIBHEIF_HEAD_RESULT
    OUTPUT_VARIABLE IRIS26636_LIBHEIF_HEAD
    OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT IRIS26636_LIBHEIF_HEAD_RESULT EQUAL 0 OR
   NOT IRIS26636_LIBHEIF_HEAD STREQUAL IRIS26636_LIBHEIF_COMMIT)
    message(FATAL_ERROR
        "IRIS_26636 libheif source authority mismatch: ${IRIS26636_LIBHEIF_HEAD} != ${IRIS26636_LIBHEIF_COMMIT}")
endif()
message(STATUS "IRIS_26636 exact gain-map HEIF authority verified: ${IRIS26636_LIBHEIF_HEAD}")
message(STATUS "IRIS_26643 AOSP Android16 HEIC contract patch verified: ${IRIS26643_LIBHEIF_AOSP_PATCH_ACTUAL_SHA256}")

add_library(irisheic SHARED iris_heic_jni.cpp)
set_target_properties(irisheic PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_include_directories(irisheic PRIVATE
    # IRIS_26636_LIBHEIF_GENERATED_HEADER_INCLUDE
    # Pinned libheif generates libheif/heif_version.h under libheif_BINARY_DIR.
    "${libheif_BINARY_DIR}"
    # IRIS_26636_LIBHEIF_PINNED_REGISTRY_INCLUDE
    # Pinned libheif 4a3f74bc... exposes static encoder registration in plugin_registry.h.
    "${iris26636_libheif_SOURCE_DIR}/libheif"
    "${iris26636_libheif_SOURCE_DIR}/libheif/api"
    "${iris26636_libheif_SOURCE_DIR}/libheif/api/libheif"
    # IRIS_26636_LIBULTRAHDR_JPEG_HEADER_CLOSURE
    # ultrahdr/icc.h -> jpegr.h -> jpeg{decoder,encoder}helper.h requires libjpeg-turbo
    # source headers (jerror.h/jpeglib.h) plus its generated build headers (jconfig.h).
    ${IRIS26507_JPEG}/src
    ${CMAKE_CURRENT_BINARY_DIR}/iris26507-libjpeg-turbo
    ${IRIS26507_UHDR}
    ${IRIS26507_UHDR}/lib/include
    ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(irisheic PRIVATE WITH_EXPERIMENTAL_GAIN_MAP=1)
target_compile_options(irisheic PRIVATE -O2 -fno-lax-vector-conversions)
target_link_libraries(irisheic PRIVATE heif iris26507-ultrahdr log jnigraphics android z)


