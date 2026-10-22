// IRIS_26864_B_VK_IMAGE_ARENA_REAL_API_SOURCE_NOT_FULL_EXECUTOR
#include "Iris26864VulkanImageArena.hpp"
#include <limits>
#include <stdexcept>
#include <string>
namespace iris26864 {
namespace {
void vkOk(VkResult result, const char* what) {
    if (result != VK_SUCCESS) throw std::runtime_error(
        std::string("26864 transient Vulkan image ") + what + ": " + std::to_string(int(result)));
}
}
VulkanImageArena::VulkanImageArena(VkPhysicalDevice physical,VkDevice device,VkDeviceSize budget)
    : physical_(physical),device_(device),budgetBytes_(budget) {
    if (physical == VK_NULL_HANDLE || device == VK_NULL_HANDLE || budget == 0)
        throw std::invalid_argument("26864 transient GPU arena missing owner/budget");
    VkPhysicalDeviceProperties props{};
    vkGetPhysicalDeviceProperties(physical_, &props);
    maxImageDimension2D_=props.limits.maxImageDimension2D;
    if (maxImageDimension2D_ < 32u)
        throw std::runtime_error("26864 invalid hardware Vulkan image extent");
    vkGetPhysicalDeviceMemoryProperties(physical_, &memoryProperties_);
    if (!memoryProperties_.memoryTypeCount ||
        memoryProperties_.memoryTypeCount > VK_MAX_MEMORY_TYPES)
        throw std::runtime_error("26864 invalid GPU Vulkan memory properties");
}
void VulkanImageArena::release(Entry& e) noexcept {
    if (e.view != VK_NULL_HANDLE) vkDestroyImageView(device_,e.view,nullptr);
    if (e.image != VK_NULL_HANDLE) vkDestroyImage(device_,e.image,nullptr);
    if (e.memory != VK_NULL_HANDLE) vkFreeMemory(device_,e.memory,nullptr);
    e=Entry{};
}
VulkanImageArena::~VulkanImageArena() {
    // Owning GL/foreign-fence submission must be complete before destruction.
    for (auto& e:entries_) release(e);
}
size_t VulkanImageArena::allocate(uint32_t width,uint32_t height,VkFormat format,
                                   VkImageUsageFlags usage) {
    if (width<1u||height<1u||width>maxImageDimension2D_||height>maxImageDimension2D_||
        format==VK_FORMAT_UNDEFINED || entries_.size()>=256 ||
        !(usage & VK_IMAGE_USAGE_STORAGE_BIT) ||
        (usage & ~(VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT |
                   VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT)))
        throw std::invalid_argument("26864 invalid transient Vulkan image contract");
    VkFormatProperties fp{};
    vkGetPhysicalDeviceFormatProperties(physical_,format,&fp);
    if (!(fp.optimalTilingFeatures & VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT) ||
        ((usage & VK_IMAGE_USAGE_SAMPLED_BIT) &&
         !(fp.optimalTilingFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT)))
        throw std::runtime_error("26864 GPU does not support required exact image format");
    Entry e{};
    e.width=width;e.height=height;e.format=format;
    try {
        VkImageCreateInfo create{};
        create.sType=VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        create.imageType=VK_IMAGE_TYPE_2D;
        create.format=format;
        create.extent={width,height,1u};
        create.mipLevels=1u;create.arrayLayers=1u;
        create.samples=VK_SAMPLE_COUNT_1_BIT;
        create.tiling=VK_IMAGE_TILING_OPTIMAL;
        create.usage=usage;
        create.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        create.initialLayout=VK_IMAGE_LAYOUT_UNDEFINED;
        vkOk(vkCreateImage(device_,&create,nullptr,&e.image),"create image");
        VkMemoryRequirements needs{};
        vkGetImageMemoryRequirements(device_,e.image,&needs);
        if (!needs.size || needs.size>budgetBytes_-usedBytes_)
            throw std::runtime_error("26864 B GPU transient image memory budget exceeded");
        uint32_t chosen=UINT32_MAX;
        for(uint32_t i=0;i<memoryProperties_.memoryTypeCount;++i) {
            if ((needs.memoryTypeBits & (1u<<i)) &&
                (memoryProperties_.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)) {
                chosen=i;break;
            }
        }
        if(chosen==UINT32_MAX)
            throw std::runtime_error("26864 no device-local transient image memory type");
        VkMemoryAllocateInfo allocation{};
        allocation.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        allocation.allocationSize=needs.size;
        allocation.memoryTypeIndex=chosen;
        vkOk(vkAllocateMemory(device_,&allocation,nullptr,&e.memory),"allocate device-local");
        vkOk(vkBindImageMemory(device_,e.image,e.memory,0),"bind image memory");
        VkImageViewCreateInfo viewInfo{};
        viewInfo.sType=VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        viewInfo.image=e.image;
        viewInfo.viewType=VK_IMAGE_VIEW_TYPE_2D;
        viewInfo.format=format;
        viewInfo.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u};
        vkOk(vkCreateImageView(device_,&viewInfo,nullptr,&e.view),"create image view");
        e.bytes=needs.size;
        entries_.push_back(e);
        usedBytes_+=e.bytes;
        return entries_.size()-1;
    }catch(...){release(e);throw;}
}
TransientImageView VulkanImageArena::at(size_t index) const {
    if(index>=entries_.size()) throw std::out_of_range("26864 GPU transient view index");
    const auto& e=entries_[index];
    return {e.image,e.view,e.format,e.width,e.height};
}
void VulkanImageArena::recordInitialGeneralTransitions(VkCommandBuffer cmd) {
    if(cmd==VK_NULL_HANDLE) throw std::invalid_argument("26864 absent Vulkan command buffer");
    for(auto& e:entries_) {
        if(e.initialized)continue;
        VkImageMemoryBarrier barrier{};
        barrier.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        barrier.oldLayout=VK_IMAGE_LAYOUT_UNDEFINED;
        barrier.newLayout=VK_IMAGE_LAYOUT_GENERAL;
        barrier.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        barrier.image=e.image;
        barrier.srcAccessMask=0;
        barrier.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
        barrier.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,0,nullptr,0,nullptr,1,&barrier);
        e.initialized=true;
    }
}
} // namespace iris26864
