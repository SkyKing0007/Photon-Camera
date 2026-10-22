#pragma once
// IRIS_26864_HDRQ_VK_SCRATCH_RESOURCE_OWNER_PROOF_NOT_RUNTIME
// No RAWR shader is substituted and no Android capture path calls this yet.
#include "Iris26864HdrqScratchLayout.hpp"
#include "Iris26864VulkanImageArena.hpp"
#include "Iris26864VulkanBufferArena.hpp"
#include <memory>
#include <string>
#include <unordered_map>

namespace iris26864 {
class VulkanHdrqScratchOwner final {
public:
    VulkanHdrqScratchOwner(VkPhysicalDevice physical,VkDevice device,
                           VkDeviceSize hardBudget,const Plan& plan,
                           const std::vector<HdrqAlignmentLevel>& validatedPyramid);
    VulkanHdrqScratchOwner(const VulkanHdrqScratchOwner&)=delete;
    VulkanHdrqScratchOwner& operator=(const VulkanHdrqScratchOwner&)=delete;
    TransientImageView image(const std::string& name) const;
    TransientBuffer buffer(const std::string& name) const;
    void recordImageTransitions(VkCommandBuffer commandBuffer);
    VkDeviceSize usedBytes() const noexcept;
    size_t imageCount() const noexcept {return imageIndex_.size();}
    size_t bufferCount() const noexcept {return bufferIndex_.size();}
private:
    // Declared before arenas to guarantee referenced images/buffers die first.
    HdrqScratchLayout layout_;
    VulkanImageArena images_;
    std::unique_ptr<VulkanBufferArena> buffers_;
    std::unordered_map<std::string,size_t> imageIndex_,bufferIndex_;
};
} // namespace iris26864
