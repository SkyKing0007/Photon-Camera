#pragma once
// IRIS_26864_VULKAN_KERNEL_RECORDER_INCOMPLETE_NOT_RUNTIME
// Candidate for the B-only RAWR backend. This is real Vulkan compute pipeline /
// descriptor / command recording code, but does NOT implement HDR+ or Wronski.
// No Android integration, CMake source addition or source replacement is allowed
// before complete shaders, resource arena, JNI handoff and 17-stage verification.
#include <vulkan/vulkan.h>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace iris26864 {

struct ComputeBinding {
    uint32_t binding = 0;
    VkDescriptorType type = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
};
struct BoundResource {
    uint32_t binding = 0;
    VkDescriptorType type = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
    VkImageView imageView = VK_NULL_HANDLE;
    VkSampler sampler = VK_NULL_HANDLE;
    VkBuffer buffer = VK_NULL_HANDLE;
    VkDeviceSize bufferOffset = 0;
    VkDeviceSize bufferRange = 0;
};
struct ShaderBinary {
    const uint32_t* words = nullptr;
    size_t wordCount = 0;
    uint32_t workgroupX = 1, workgroupY = 1, workgroupZ = 1;
};
// Pipeline and descriptor lifetime is owned by this object. Source image /
// buffer memory remains owned by the outer Vulkan arena and the recorder's
// submission fence. No GL access can occur while that submission is in flight.
// A distinct descriptor set is allocated for EVERY recorded invocation. Vulkan
// would otherwise apply later vkUpdateDescriptorSets to earlier queued passes.
// All sets remain alive until the caller has finished this command submission.
class VulkanKernelExecutor final {
public:
    VulkanKernelExecutor(VkDevice device, ShaderBinary shader,
                         const std::vector<ComputeBinding>& bindings,
                         uint32_t pushConstantSize, uint32_t maxDispatches);
    ~VulkanKernelExecutor();
    VulkanKernelExecutor(const VulkanKernelExecutor&) = delete;
    VulkanKernelExecutor& operator=(const VulkanKernelExecutor&) = delete;
    // Record only; the existing B-owned CommandSubmissionOwner submits and
    // waits for completion. Never use vkQueueSubmit or vkQueueWaitIdle here.
    // Caller must provide one descriptor of the declared type per binding;
    // an instance is single-recording-thread only and must outlive GPU completion.
    // all image layouts are externally transitioned to GENERAL on this queue.
    // Strict CPU-only preflight: NO descriptor allocations, Vulkan commands,
    // or GPU mutations. additionalReserved counts earlier jobs in the SAME
    // upcoming recording batch using this same kernel (per-kernel pool cap).
    void preflight(const std::vector<BoundResource>& resources,
                   size_t pushByteCount,uint32_t width,uint32_t height,
                   uint32_t depth=1,uint32_t additionalReserved=0) const;
    void record(VkCommandBuffer commandBuffer,
                const std::vector<BoundResource>& resources,
                const void* pushConstants, size_t pushByteCount,
                uint32_t width, uint32_t height, uint32_t depth = 1,
                bool previousComputeWrites = true) const;
private:
    void cleanup() noexcept;
    VkDevice device_ = VK_NULL_HANDLE;
    VkShaderModule shaderModule_ = VK_NULL_HANDLE;
    VkDescriptorSetLayout setLayout_ = VK_NULL_HANDLE;
    VkDescriptorPool descriptorPool_ = VK_NULL_HANDLE;
    VkPipelineLayout pipelineLayout_ = VK_NULL_HANDLE;
    VkPipeline pipeline_ = VK_NULL_HANDLE;
    std::vector<ComputeBinding> bindings_;
    uint32_t pushConstantSize_ = 0;
    uint32_t groupX_ = 1, groupY_ = 1, groupZ_ = 1;
    uint32_t maxDispatches_ = 0;
    mutable uint32_t recordedDispatches_ = 0;
};
} // namespace iris26864
