#pragma once
// IRIS_26864_HDRQ_STORAGE_BUFFER_ALLOCATION_NOT_RUNTIME
// Device-local scratch SSBOs and transfer-copy-ready alignment stores.
// Queue submissions must complete before owner destruction.
#include <vulkan/vulkan.h>
#include <cstddef>
#include <cstdint>
#include <vector>
namespace iris26864 {
struct TransientBuffer {
    VkBuffer buffer=VK_NULL_HANDLE;
    VkDeviceSize size=0;
};
class VulkanBufferArena final {
public:
    VulkanBufferArena(VkPhysicalDevice physical,VkDevice device,VkDeviceSize budgetBytes);
    ~VulkanBufferArena();
    VulkanBufferArena(const VulkanBufferArena&)=delete;
    VulkanBufferArena& operator=(const VulkanBufferArena&)=delete;
    size_t allocate(VkDeviceSize bytes, VkBufferUsageFlags usage=
                VK_BUFFER_USAGE_STORAGE_BUFFER_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT|
                VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    TransientBuffer at(size_t index) const;
    VkDeviceSize allocatedBytes() const noexcept {return allocatedBytes_;}
private:
    struct Entry {VkBuffer buffer=VK_NULL_HANDLE;VkDeviceMemory memory=VK_NULL_HANDLE;VkDeviceSize size=0,bytes=0;};
    void release(Entry& e) noexcept;
    VkDevice device_=VK_NULL_HANDLE;
    VkDeviceSize budgetBytes_=0,allocatedBytes_=0;
    VkPhysicalDeviceMemoryProperties memoryProperties_{};
    std::vector<Entry> entries_;
};
} // namespace iris26864
