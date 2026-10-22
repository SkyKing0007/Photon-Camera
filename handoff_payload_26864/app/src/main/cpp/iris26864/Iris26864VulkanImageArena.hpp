#pragma once
// IRIS_26864_VK_TRANSIENT_IMAGE_ARENA_INCOMPLETE_NOT_RUNTIME
// One-frame Vulkan-owned intermediate images only. External GL AHB and Android
// reference RAW ownership are handled by Iris's existing separate owner.
#include <vulkan/vulkan.h>
#include <cstddef>
#include <cstdint>
#include <vector>
namespace iris26864 {
struct TransientImageView {
    VkImage image = VK_NULL_HANDLE;
    VkImageView view = VK_NULL_HANDLE;
    VkFormat format = VK_FORMAT_UNDEFINED;
    uint32_t width = 0, height = 0;
};
class VulkanImageArena final {
public:
    VulkanImageArena(VkPhysicalDevice physical, VkDevice device, VkDeviceSize memoryBudgetBytes);
    ~VulkanImageArena();
    VulkanImageArena(const VulkanImageArena&) = delete;
    VulkanImageArena& operator=(const VulkanImageArena&) = delete;
    // No implicit scaling, reduced frame count, host memory mapping or alternate
    // format on device failure. Required shaders and RAW contracts fail closed.
    size_t allocate(uint32_t width, uint32_t height, VkFormat format,
                    VkImageUsageFlags usage = VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_SAMPLED_BIT);
    TransientImageView at(size_t index) const;
    // Called exactly once after transient allocation and before compute use.
    // Intermediate images must never be shared with GLES / foreign queues.
    void recordInitialGeneralTransitions(VkCommandBuffer commandBuffer);
    VkDeviceSize allocatedBytes() const noexcept { return usedBytes_; }
    size_t size() const noexcept { return entries_.size(); }
private:
    struct Entry {
        VkImage image = VK_NULL_HANDLE;
        VkDeviceMemory memory = VK_NULL_HANDLE;
        VkImageView view = VK_NULL_HANDLE;
        VkFormat format = VK_FORMAT_UNDEFINED;
        uint32_t width = 0,height = 0;
        VkDeviceSize bytes = 0;
        bool initialized = false;
    };
    void release(Entry& e) noexcept;
    VkPhysicalDevice physical_ = VK_NULL_HANDLE;
    VkDevice device_ = VK_NULL_HANDLE;
    VkDeviceSize budgetBytes_ = 0, usedBytes_ = 0;
    uint32_t maxImageDimension2D_ = 0;
    VkPhysicalDeviceMemoryProperties memoryProperties_{};
    std::vector<Entry> entries_;
};
} // namespace iris26864
