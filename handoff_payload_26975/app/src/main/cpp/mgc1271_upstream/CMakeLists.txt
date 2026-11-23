# IRIS_26512_MGC1271_SPATIAL_NATIVE_PARITY_OWNER
# Populated at build time from bjzhou/PhotonCamera 1.27.1 commit 09c76e57...
cmake_minimum_required(VERSION 3.6)
project(motionv2_mgc1271 LANGUAGES C CXX ASM)

if(NOT ANDROID_ABI STREQUAL "arm64-v8a")
    # Upstream 1.27.1 is arm64-only. Keep Photon's existing multi-ABI packaging buildable without
    # pretending the lifted arm64 AOT kernels are portable. Runtime parity rejects non-arm64 first.
    add_library(my-native-lib SHARED mgc1271_non_arm64_stub.cpp)
    target_link_libraries(my-native-lib PRIVATE log)
    return()
endif()

find_package(OpenMP REQUIRED)
set(MGC_DENOISE_CAPSULE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_full_resolution_denoise_capsule.bin")
set(MGC_DENOISE_CAPSULE_SHA256
    "3ee5c92d2b830448de6270ec0c71ac64a484885a6bd7440d1c53f8695afc55ec")
file(SHA256 "${MGC_DENOISE_CAPSULE}" MGC_DENOISE_CAPSULE_ACTUAL_SHA256)
if(NOT MGC_DENOISE_CAPSULE_ACTUAL_SHA256 STREQUAL MGC_DENOISE_CAPSULE_SHA256)
    message(FATAL_ERROR "MGC 1.27.1 denoise capsule hash mismatch")
endif()
set(MGC_DENOISE_ASM "${CMAKE_CURRENT_BINARY_DIR}/mgc_full_resolution_denoise_static.S")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_full_resolution_denoise_static.S.in"
    "${MGC_DENOISE_ASM}" @ONLY)
set_source_files_properties("${MGC_DENOISE_ASM}" PROPERTIES GENERATED TRUE
    OBJECT_DEPENDS "${MGC_DENOISE_CAPSULE}")

set(MGC_DEMOIRE_CAPSULE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_demoire_capsule.bin")
set(MGC_DEMOIRE_CAPSULE_SHA256
    "769d656725b445c356b9f3e44341e101806bb201fcd2e5681c0ab92173a68c9a")
file(SHA256 "${MGC_DEMOIRE_CAPSULE}" MGC_DEMOIRE_CAPSULE_ACTUAL_SHA256)
if(NOT MGC_DEMOIRE_CAPSULE_ACTUAL_SHA256 STREQUAL MGC_DEMOIRE_CAPSULE_SHA256)
    message(FATAL_ERROR "MGC 1.27.1 demoire capsule hash mismatch")
endif()
set(MGC_DEMOIRE_ASM "${CMAKE_CURRENT_BINARY_DIR}/mgc_demoire_static.S")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_demoire_static.S.in"
    "${MGC_DEMOIRE_ASM}" @ONLY)
set_source_files_properties("${MGC_DEMOIRE_ASM}" PROPERTIES GENERATED TRUE
    OBJECT_DEPENDS "${MGC_DEMOIRE_CAPSULE}")

# IRIS_26512_MGC1271_COMPLETE_PINNED_NATIVE_CLOSURE
set(MGC_SABRE_CAPSULE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sabre_resolve_capsule.bin")
set(MGC_SABRE_CAPSULE_SHA256
    "725c5ac2c2de63e7f17c8fb3516fe176d2387c6eed579da25e35df12588e0e69")
file(SHA256 "${MGC_SABRE_CAPSULE}" MGC_SABRE_CAPSULE_ACTUAL_SHA256)
if(NOT MGC_SABRE_CAPSULE_ACTUAL_SHA256 STREQUAL MGC_SABRE_CAPSULE_SHA256)
    message(FATAL_ERROR "MGC 1.27.1 Sabre Resolve capsule hash mismatch")
endif()
set(MGC_SABRE_ASM "${CMAKE_CURRENT_BINARY_DIR}/mgc_sabre_resolve_static.S")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sabre_resolve_static.S.in"
    "${MGC_SABRE_ASM}" @ONLY)
set_source_files_properties("${MGC_SABRE_ASM}" PROPERTIES GENERATED TRUE
    OBJECT_DEPENDS "${MGC_SABRE_CAPSULE}")

set(MGC_SHARPEN_CAPSULE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sharpen_capsule.bin")
set(MGC_SHARPEN_CAPSULE_SHA256
    "733065cfec32ac752cc2088ea284b44a55b24a6171e5829f6971dcb098b1d7ce")
file(SHA256 "${MGC_SHARPEN_CAPSULE}" MGC_SHARPEN_CAPSULE_ACTUAL_SHA256)
if(NOT MGC_SHARPEN_CAPSULE_ACTUAL_SHA256 STREQUAL MGC_SHARPEN_CAPSULE_SHA256)
    message(FATAL_ERROR "MGC 1.27.1 SharpenTo16Bit capsule hash mismatch")
endif()
set(MGC_SHARPEN_ASM "${CMAKE_CURRENT_BINARY_DIR}/mgc_sharpen_static.S")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static/mgc_sharpen_static.S.in"
    "${MGC_SHARPEN_ASM}" @ONLY)
set_source_files_properties("${MGC_SHARPEN_ASM}" PROPERTIES GENERATED TRUE
    OBJECT_DEPENDS "${MGC_SHARPEN_CAPSULE}")

add_library(my-native-lib SHARED
    mgc_strength_map_scaler.cpp
    mgc_denoise_static/mgc_denoise_static.cpp
    mgc_denoise_static/mgc_full_resolution_denoise_jni.cpp
    experiment_c_26975/iris26975_c_full_resolution_denoise_jni.cpp
    experiment_c_26975/iris26975_c_low_frequency_chroma.cpp
    experiment_c_26975/iris26975_c_donor_chroma_noise.cpp
    mgc_denoise_static/mgc_sabre_resolve_jni.cpp
    mgc_denoise_static/mgc_sharpen_jni.cpp
    mgc_denoise_static/mgc_spatial_strength_jni.cpp
    "${MGC_DENOISE_ASM}"
    "${MGC_DEMOIRE_ASM}"
    "${MGC_SABRE_ASM}"
    "${MGC_SHARPEN_ASM}")
set_target_properties(my-native-lib PROPERTIES
    CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON CXX_EXTENSIONS OFF)
target_include_directories(my-native-lib PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/mgc_denoise_static")
set_source_files_properties(mgc_strength_map_scaler.cpp PROPERTIES
    COMPILE_OPTIONS "-fno-fast-math;-ffp-contract=off")
set_source_files_properties(mgc_denoise_static/mgc_denoise_static.cpp PROPERTIES
    COMPILE_OPTIONS "-fno-fast-math;-ffp-contract=off")
set_source_files_properties(mgc_denoise_static/mgc_sharpen_jni.cpp PROPERTIES
    COMPILE_OPTIONS "-fno-fast-math;-ffp-contract=off")
target_compile_options(my-native-lib PRIVATE -O3 -w ${OpenMP_CXX_FLAGS})
target_link_libraries(my-native-lib PRIVATE OpenMP::OpenMP_CXX log)
