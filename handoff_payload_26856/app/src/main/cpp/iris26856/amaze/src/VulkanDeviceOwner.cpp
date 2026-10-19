// IRIS_26856_B_ONLY_VULKAN_DEVICE_OWNER
#include "amaze/VulkanDeviceOwner.hpp"
#include <vulkan/vulkan_android.h>
#include <algorithm>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace amaze {
namespace {
void requireVk(VkResult r, const char* context) {
    if (r != VK_SUCCESS) throw std::runtime_error(context);
}
bool containsExtension(const std::vector<VkExtensionProperties>& all, const char* name) {
    return std::any_of(all.begin(), all.end(), [name](const VkExtensionProperties& e) {
        return std::strcmp(e.extensionName, name) == 0;
    });
}
}
VulkanDeviceOwner::VulkanDeviceOwner() {
    try {
        VkApplicationInfo app{};
        app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
        app.pApplicationName = "Iris26856Amaze";
        app.apiVersion = VK_API_VERSION_1_1;
        VkInstanceCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
        ici.pApplicationInfo = &app;
        requireVk(vkCreateInstance(&ici, nullptr, &instance_), "26856 Vulkan instance creation failed");
        uint32_t count = 0;
        requireVk(vkEnumeratePhysicalDevices(instance_, &count, nullptr), "26856 Vulkan device enumeration failed");
        if (!count) throw std::runtime_error("26856 no Vulkan physical devices");
        std::vector<VkPhysicalDevice> physicals(count);
        requireVk(vkEnumeratePhysicalDevices(instance_, &count, physicals.data()), "26856 Vulkan device list failed");
        // GL/Vulkan ownership requires externally imported/exported native
        // fence semaphores plus the Android AHB external memory extension.
        // Never accept a device where only AHB memory sharing is available.
        const char* required[] = {
            VK_ANDROID_EXTERNAL_MEMORY_ANDROID_HARDWARE_BUFFER_EXTENSION_NAME,
            VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME,
            VK_EXT_QUEUE_FAMILY_FOREIGN_EXTENSION_NAME,
        };
        for (VkPhysicalDevice p : physicals) {
            VkPhysicalDeviceProperties props{};
            vkGetPhysicalDeviceProperties(p, &props);
            if (props.apiVersion < VK_API_VERSION_1_1) continue;
            uint32_t ec = 0;
            if (vkEnumerateDeviceExtensionProperties(p, nullptr, &ec, nullptr) != VK_SUCCESS) continue;
            std::vector<VkExtensionProperties> exts(ec);
            if (vkEnumerateDeviceExtensionProperties(p, nullptr, &ec, exts.data()) != VK_SUCCESS) continue;
            bool ok = true;
            for (const char* ext : required) if (!containsExtension(exts, ext)) ok = false;
            if (!ok) continue;
            uint32_t fc = 0;
            vkGetPhysicalDeviceQueueFamilyProperties(p, &fc, nullptr);
            std::vector<VkQueueFamilyProperties> families(fc);
            vkGetPhysicalDeviceQueueFamilyProperties(p, &fc, families.data());
            for (uint32_t i = 0; i < fc; ++i) {
                if ((families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) == 0 || families[i].queueCount == 0) continue;
                float priority = 1.0f;
                VkDeviceQueueCreateInfo q{};
                q.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
                q.queueFamilyIndex = i;
                q.queueCount = 1;
                q.pQueuePriorities = &priority;
                VkDeviceCreateInfo d{};
                d.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
                d.queueCreateInfoCount = 1;
                d.pQueueCreateInfos = &q;
                d.enabledExtensionCount = uint32_t(sizeof(required) / sizeof(required[0]));
                d.ppEnabledExtensionNames = required;
                VkDevice dev = VK_NULL_HANDLE;
                if (vkCreateDevice(p, &d, nullptr, &dev) != VK_SUCCESS) continue;
                VkQueue queue = VK_NULL_HANDLE;
                vkGetDeviceQueue(dev, i, 0, &queue);
                if (!queue) { vkDestroyDevice(dev, nullptr); continue; }
                physical_ = p;
                device_ = dev;
                family_ = i;
                queue_ = queue;
                return;
            }
        }
        throw std::runtime_error("26856 no Vulkan 1.1 compute device with Android AHB import");
    } catch (...) {
        if (device_) vkDestroyDevice(device_, nullptr);
        if (instance_) vkDestroyInstance(instance_, nullptr);
        device_ = VK_NULL_HANDLE;
        instance_ = VK_NULL_HANDLE;
        throw;
    }
}
VulkanDeviceOwner::~VulkanDeviceOwner() {
    // The caller must have destroyed imported resources and completed all submissions.
    // Never reinterpret a failed device wait as successful completion.
    if (device_) {
        if (vkDeviceWaitIdle(device_) != VK_SUCCESS) return;
        vkDestroyDevice(device_, nullptr);
    }
    if (instance_) vkDestroyInstance(instance_, nullptr);
}
VulkanContext VulkanDeviceOwner::context() const noexcept {
    VulkanContext c{};
    c.physicalDevice = physical_;
    c.device = device_;
    c.queueFamilyIndex = family_;
    return c;
}
}  // namespace amaze
