#pragma once
// IRIS_26864_B_REAL_PINNED_CFA_BRIDGE_KERNELS
// The ONLY Iris-authored GLSL stages between pinned RAWR GPU reconstruction
// and successful 26863 AMaZE. Both compile with the real pinned Vulkan GLSL
// toolchain into CMake-generated SPIR-V headers, never placeholders/assets.
#include "Iris26864VulkanKernelExecutor.hpp"
#include <memory>
namespace iris26864 {
std::unique_ptr<VulkanKernelExecutor> makeRealHdrqCfaBridge(VkDevice device);
std::unique_ptr<VulkanKernelExecutor> makeRealWronskiCfaBridge(VkDevice device);
std::unique_ptr<VulkanKernelExecutor> makeRealWronskiChromaGuide(VkDevice device);
std::unique_ptr<VulkanKernelExecutor> makeRealSensorClipToGlBridge(VkDevice device);
// B OFF pixel-local ORIGINAL-RAW color witness, developer integration stage.
std::unique_ptr<VulkanKernelExecutor> makeRealBOffRawTileRefine(VkDevice device);
std::unique_ptr<VulkanKernelExecutor> makeRealBOffRawAccumulate(VkDevice device);
std::unique_ptr<VulkanKernelExecutor> makeRealBOffRawFinalize(VkDevice device);
std::unique_ptr<VulkanKernelExecutor> makeRealBOffStrictWitnessReconcile(VkDevice device);
}
