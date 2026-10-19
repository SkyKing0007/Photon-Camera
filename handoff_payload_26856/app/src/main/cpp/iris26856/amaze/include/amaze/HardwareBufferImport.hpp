// IRIS_26856_PINNED_VULKAN_AHB_IMPORT_OWNER -- B-only native staging.
// The caller owns VkDevice/queue submission and must wait before destruction.
#pragma once
#include <android/hardware_buffer.h>
#include <vulkan/vulkan.h>
#include <vulkan/vulkan_android.h>
#include <cstdint>

namespace amaze {
class HardwareBufferImport final {
public:
    HardwareBufferImport(VkPhysicalDevice physical, VkDevice device,
                         AHardwareBuffer* buffer, uint32_t width, uint32_t height,
                         VkImageUsageFlags usage);
    ~HardwareBufferImport();
    HardwareBufferImport(const HardwareBufferImport&) = delete;
    HardwareBufferImport& operator=(const HardwareBufferImport&) = delete;
    VkImage image() const noexcept { return image_; }
    VkImageView view() const noexcept { return view_; }
    // No implicit queue wait: caller must not release an in-flight import.
private:
    VkDevice device_ = VK_NULL_HANDLE;
    AHardwareBuffer* buffer_ = nullptr;
    VkDeviceMemory memory_ = VK_NULL_HANDLE;
    VkImage image_ = VK_NULL_HANDLE;
    VkImageView view_ = VK_NULL_HANDLE;
};
} // namespace amaze
