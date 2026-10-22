#pragma once
// IRIS_26864_B_HDRQ_VK_SCHEDULE_RECORDER_NOT_COMPLETE_ENGINE
// Actual command recording for the pinned 4-pass, B-only uniform HDR+ chain.
// Shaders/arena bindings supplied by a future ownership-verified stage binder.
#include "Iris26864VulkanKernelExecutor.hpp"
#include "../Iris26864HdrqSchedule.hpp"
#include <functional>
#include <vector>
namespace iris26864 {
enum class HdrqRecordedKind { Kernel, ClearTileMismatch, FillAlignmentZero, CopyAlignmentSlot };
struct HdrqKernelInvocation {
    HdrqRecordedKind kind = HdrqRecordedKind::Kernel;
    VkImage clearImage = VK_NULL_HANDLE;  // ONLY pinned pass-total mismatch clear
    // Source/destination transfer contract for align-once, not a shader.
    VkBuffer transferSrc = VK_NULL_HANDLE, transferDst = VK_NULL_HANDLE;
    VkDeviceSize transferSrcOffset = 0, transferDstOffset = 0, transferBytes = 0;
    HdrqDispatch ownership;
    VulkanKernelExecutor* kernel = nullptr;
    std::vector<BoundResource> resources;
    std::vector<uint32_t> pushWords; // Vulkan push constants: 4-byte aligned
    uint32_t width = 0, height = 0, depth = 1;
};
using HdrqBindingProvider=std::function<HdrqKernelInvocation(const HdrqDispatch&)>;
using HdrqExpandedBindingProvider=std::function<std::vector<HdrqKernelInvocation>(const HdrqDispatch&)>;
// Expands source composite stages (reference preparation, alignment pyramid,
// coarse/fine correction, align-once SSBO save). Validates the ENTIRE burst
// before recording any command. No frame substitution or merge fallback.
void recordHdrqVulkanExpandedSchedule(const Plan& plan,VkCommandBuffer commandBuffer,
                                      const HdrqExpandedBindingProvider& bind);
// This is not an inference/fallback router. It requires the already validated
// frequency plan and exactly one genuine Vulkan kernel for every source stage.
void recordHdrqVulkanSchedule(const Plan& plan, VkCommandBuffer commandBuffer,
                              const HdrqBindingProvider& bind);
} // namespace iris26864
