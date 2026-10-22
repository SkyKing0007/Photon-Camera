#pragma once
// IRIS_26864_PINNED_HDRQ_VULKAN_PIPELINE_OWNER_DEV_ONLY_NOT_RUNTIME
// Own all 23 RAWR HDR+ pipelines, one immutable descriptor-set budget per
// kernel. No Camera2/Photon/A fallback, no partial kernel registration.
// The caller must retain this owner and the scratch arena until its Vulkan
// submission fence signals. No GL access is authorized by this component.
#include "Iris26864HdrqPinnedSpirvRegistry.hpp"
#include "Iris26864VulkanKernelExecutor.hpp"
#include <map>
#include <memory>
#include <string>
#include <vector>
namespace iris26864 {
class HdrqPinnedPipelineOwner final {
public:
    // `maxUses` is the exact precomputed per-kernel dispatch budget for one
    // burst and must name each of the 23 source-locked kernels exactly once.
    // The provider is called for *every* kernel and all SPIR-V ABI validation
    // finishes BEFORE the first Vulkan call. Any Vulkan failure thereafter
    // rolls back every previously constructed pipeline via RAII.
    HdrqPinnedPipelineOwner(VkDevice device,
                            const PinnedSpirvBytesProvider& provider,
                            const std::map<std::string,uint32_t>& maxUses);
    HdrqPinnedPipelineOwner(const HdrqPinnedPipelineOwner&)=delete;
    HdrqPinnedPipelineOwner& operator=(const HdrqPinnedPipelineOwner&)=delete;
    VulkanKernelExecutor& require(const std::string& exactKernel) const;
    size_t size() const noexcept {return kernels_.size();}
    bool owns(const VulkanKernelExecutor* kernel) const noexcept;
private:
    // Must be destroyed after GPU completion; do not move to a shorter scope.
    std::map<std::string,std::unique_ptr<VulkanKernelExecutor>> kernels_;
};
}
