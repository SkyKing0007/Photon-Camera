#pragma once
// IRIS_26864_B_HDRQ_SINGLE_QUEUE_CFA_TO_AMAZE_NOT_ANDROID_ACTIVE
// Same Vulkan device, same command buffer, same 26863 submit/fence owner.
// HDRq writes R32F CFA. This recorder writes canonical packed RGBA16F then
// the unchanged 26863 AmazePipeline::record consumes that exact image view.
// Does NOT allocate its own queue, expose GL textures or publish JPEG.
#include "Iris26864CfaToAmazeContract.hpp"
#include "../Iris26864VulkanKernelExecutor.hpp"
#include <cstdint>
namespace iris26864 {
struct HdrqCanonicalGpuFrame {
    CfaBridgeConfig cfg{};
    uint32_t physicalSensorPattern=0;
    VkImage r32CfaImage=VK_NULL_HANDLE;
    VkImageView r32CfaView=VK_NULL_HANDLE;
    VkImageView rawReferenceR16uView=VK_NULL_HANDLE;
    VkImage packedRgba16fImage=VK_NULL_HANDLE;
    VkImageView packedRgba16fView=VK_NULL_HANDLE;
    VkImageView clipR16uView=VK_NULL_HANDLE;
    VkBuffer camera2LscBuffer=VK_NULL_HANDLE;
    VkDeviceSize camera2LscBytes=0;
    // All resources are caller-owned, in GENERAL layout, and must be kept
    // alive until the inherited 26863 submission fence has resolved.
};
// Strict format/binding/phase preflight runs BEFORE any Vk commands.
// The kernel must be the separately version-pinned Iris CFA bridge shader,
// not any of the 23 RAWR kernels or AMaZE's tile shader.
void preflightCanonicalCfaBridge(const VulkanKernelExecutor& bridge,
                                 const HdrqCanonicalGpuFrame& frame);
void recordCanonicalCfaForAmaze(VkCommandBuffer cmd,
                                const VulkanKernelExecutor& bridge,
                                const HdrqCanonicalGpuFrame& frame);
}
