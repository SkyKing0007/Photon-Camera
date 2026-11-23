# 26975 C-only original pinned native shim. This must be included in the guarded
# GitHub Actions CMake only after original JNI registration and class closure checks.
if(ANDROID_ABI STREQUAL "arm64-v8a")
add_library(iris26975c_original129_jni SHARED
    "${CMAKE_CURRENT_SOURCE_DIR}/iris26975c/Iris26975Original129JniTrampolines.cpp")
target_link_libraries(iris26975c_original129_jni PRIVATE dl log)
endif() # original donor ARM64 only; never alters 32-bit A/B targets
