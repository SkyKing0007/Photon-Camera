#include "Iris26864HdrqScratchOwner.hpp"
#include <stdexcept>
#include <utility>
namespace iris26864 {
VulkanHdrqScratchOwner::VulkanHdrqScratchOwner(VkPhysicalDevice physical,VkDevice device,
        VkDeviceSize budget,const Plan& plan,const std::vector<HdrqAlignmentLevel>& levels)
    : layout_(makeHdrqScratchLayout(plan,levels)),images_(physical,device,budget) {
    if(!budget || layout_.logicalBytes>budget)
        throw std::runtime_error("26864 HDRq scratch exceeds budget before driver allocation");
    for(const auto& desc:layout_.images) {
        // Zero total-mismatch by vkCmdClearColorImage, on the existing Vulkan
        // recording owner. Do not use CPU maps or GLSL zero substitute.
        VkImageUsageFlags usage=VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT;
        if(desc.name=="hdrq_total_mismatch" || desc.name=="hdrq_weight_sum")
            usage|=VK_IMAGE_USAGE_TRANSFER_DST_BIT;
        const size_t id=images_.allocate(desc.width,desc.height,desc.format,usage);
        if(!imageIndex_.emplace(desc.name,id).second)
            throw std::logic_error("26864 duplicate HDRq image owner");
    }
    if(images_.allocatedBytes()>=budget)
        throw std::runtime_error("26864 HDRq image driver allocation consumes buffer budget");
    // Shared hard budget covers BOTH Vulkan image and SSBO allocations; the
    // real driver memory requirements may exceed logical format bytes.
    buffers_=std::make_unique<VulkanBufferArena>(physical,device,
                                                 budget-images_.allocatedBytes());
    for(const auto& desc:layout_.buffers) {
        const size_t id=buffers_->allocate(desc.bytes);
        if(!bufferIndex_.emplace(desc.name,id).second)
            throw std::logic_error("26864 duplicate HDRq buffer owner");
    }
}
TransientImageView VulkanHdrqScratchOwner::image(const std::string& name) const {
    auto it=imageIndex_.find(name);
    if(it==imageIndex_.end())throw std::out_of_range("26864 undeclared HDRq image binding: "+name);
    return images_.at(it->second);
}
TransientBuffer VulkanHdrqScratchOwner::buffer(const std::string& name) const {
    auto it=bufferIndex_.find(name);
    if(it==bufferIndex_.end()||!buffers_)
        throw std::out_of_range("26864 undeclared HDRq SSBO binding: "+name);
    return buffers_->at(it->second);
}
void VulkanHdrqScratchOwner::recordImageTransitions(VkCommandBuffer commandBuffer) {
    images_.recordInitialGeneralTransitions(commandBuffer);
}
VkDeviceSize VulkanHdrqScratchOwner::usedBytes() const noexcept {
    return images_.allocatedBytes()+(buffers_?buffers_->allocatedBytes():0u);
}
} // namespace iris26864
