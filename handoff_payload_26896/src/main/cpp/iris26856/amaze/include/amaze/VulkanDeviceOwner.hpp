// IRIS_26856_B_ONLY_VULKAN_DEVICE_OWNER -- isolated from Experiment A and Spektra.
#pragma once
#include "amaze/Amaze.hpp"
#include <vulkan/vulkan.h>

namespace amaze {
// Owns a dedicated Android-AHB-compatible compute device and queue.
// Do not destroy until every GPU submission and imported AHB has settled.
class VulkanDeviceOwner final {
public:
    VulkanDeviceOwner();
    ~VulkanDeviceOwner();
    VulkanDeviceOwner(const VulkanDeviceOwner&) = delete;
    VulkanDeviceOwner& operator=(const VulkanDeviceOwner&) = delete;
    VulkanContext context() const noexcept;
    VkQueue queue() const noexcept { return queue_; }
    // B-only Vulkan 1.1 instance for optional physical-device budget dispatch.
    VkInstance instance() const noexcept { return instance_; }
private:
    VkInstance instance_ = VK_NULL_HANDLE;
    VkPhysicalDevice physical_ = VK_NULL_HANDLE;
    VkDevice device_ = VK_NULL_HANDLE;
    VkQueue queue_ = VK_NULL_HANDLE;
    uint32_t family_ = UINT32_MAX;
};
}  // namespace amaze
