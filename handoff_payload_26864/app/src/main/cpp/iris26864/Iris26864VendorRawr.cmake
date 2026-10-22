# IRIS_26864_PINNED_ORIGINAL_RAWR_NATIVE_PIPELINE
# This is the authentic upstream AndroidBurstCoordinator + embedded Vulkan
# kernels, not the development-only private Iris HDRq recorder. The immutable
# upstream source must be present from pinned Git blob acquisition BEFORE
# candidate-first source freeze. Never download sources during NDK compilation.
set(IRIS26864_VENDOR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/vendor/rawr/native")
set(IRIS26864_VENDOR_PIPELINE "${IRIS26864_VENDOR_ROOT}/multiframe/pipeline")
set(IRIS26864_VENDOR_INCLUDE "${IRIS26864_VENDOR_ROOT}/shader_common/shaders")
foreach(REL
    "multiframe/pipeline/src/AndroidBurstCoordinator.cpp"
    "multiframe/pipeline/src/HdrPlusRecorder.cpp"
    "multiframe/pipeline/src/VulkanExecutor.cpp"
    "multiframe/merge_wronski/shaders/a11_finalize.comp"
    "multiframe/merge_hdrplus/shaders/hdrq_merge.comp"
    "shader_common/shaders/cfa_common.glsl"
    "shader_common/shaders/lens_shading.glsl")
  if(NOT EXISTS "${IRIS26864_VENDOR_ROOT}/${REL}")
    message(FATAL_ERROR "26864 missing pinned RAWR runtime source: ${REL}")
  endif()
endforeach()
# Reuse pinned real GLSL 16.5.0 discovered by existing successful CMake
# mechanics. Missing SPIR-V tools must fail closed, never become mock PASS.
find_program(IRIS26864_SPIRV_VAL NAMES spirv-val REQUIRED)
find_program(IRIS26864_SPIRV_OPT NAMES spirv-opt REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(GLSLC "${Python3_EXECUTABLE};${CMAKE_CURRENT_SOURCE_DIR}/iris26864/compile_locked_rawr_glslc.py;--validator=${IRIS26681_GLSLANG};--spirv-val=${IRIS26864_SPIRV_VAL};--spirv-opt=${IRIS26864_SPIRV_OPT}")
# Unmodified upstream target, shader registry, descriptor layouts, source
# order, 2-slot coordinator and burst noise logic. No competing owner.
add_subdirectory("${IRIS26864_VENDOR_PIPELINE}"
                 "${CMAKE_CURRENT_BINARY_DIR}/iris26864_vendor_pipeline")
set_target_properties(raw_gpu_pipeline PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_libraries(iris26856amaze PRIVATE raw_gpu_pipeline)

# Real SPIR-V codegen for the TWO Iris-only packed CFA/physical-LSC
# compatibility bridges. Generated binary is embedded and linked into the
# SAME JNI library; no runtime missing-asset fallback or synthetic .spv.
set(IRIS26864_BRIDGE_SPV_DIR "${CMAKE_CURRENT_BINARY_DIR}/iris26864_bridge_spv")
file(MAKE_DIRECTORY "${IRIS26864_BRIDGE_SPV_DIR}")
set(IRIS26864_BRIDGE_EMBED "${IRIS26864_VENDOR_ROOT}/vk_common/cmake/EmbedBinary.cmake")
foreach(BRIDGE_NAME IN ITEMS hdrq_cfa_bridge wronski_cfa_bridge clip_to_gl_bridge)
  if(BRIDGE_NAME STREQUAL "hdrq_cfa_bridge")
    set(BRIDGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/bridge/Iris26864HdrqCfaToAmaze.comp")
  elseif(BRIDGE_NAME STREQUAL "wronski_cfa_bridge")
    set(BRIDGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/Iris26864WronskiPackedCfa2x.comp")
  else()
    set(BRIDGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/iris26864/Iris26864PackedSensorClipToGl.comp")
  endif()
  set(BRIDGE_SPV "${IRIS26864_BRIDGE_SPV_DIR}/iris26864_${BRIDGE_NAME}.spv")
  set(BRIDGE_HDR "${IRIS26864_BRIDGE_SPV_DIR}/iris26864_${BRIDGE_NAME}.h")
  add_custom_command(OUTPUT "${BRIDGE_SPV}" "${BRIDGE_HDR}"
    COMMAND ${GLSLC} --target-env=vulkan1.1 -O
            "-I${IRIS26864_VENDOR_INCLUDE}"
            "${BRIDGE_SRC}" -o "${BRIDGE_SPV}"
    COMMAND ${CMAKE_COMMAND} "-DINPUT=${BRIDGE_SPV}" "-DOUTPUT=${BRIDGE_HDR}"
            "-DSYMBOL=iris26864_${BRIDGE_NAME}_spv" -P "${IRIS26864_BRIDGE_EMBED}"
    DEPENDS "${BRIDGE_SRC}"
            "${IRIS26864_VENDOR_INCLUDE}/cfa_common.glsl"
            "${IRIS26864_VENDOR_INCLUDE}/lens_shading.glsl"
            "${IRIS26864_BRIDGE_EMBED}"
    VERBATIM)
  list(APPEND IRIS26864_BRIDGE_HEADERS "${BRIDGE_HDR}")
endforeach()
add_custom_target(iris26864_real_bridge_spirv ALL DEPENDS ${IRIS26864_BRIDGE_HEADERS})
add_dependencies(iris26864-native iris26864_real_bridge_spirv)
target_include_directories(iris26864-native PRIVATE "${IRIS26864_BRIDGE_SPV_DIR}")
