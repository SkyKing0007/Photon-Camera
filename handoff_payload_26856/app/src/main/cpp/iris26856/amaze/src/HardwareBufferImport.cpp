// IRIS_26856_PINNED_VULKAN_AHB_IMPORT_OWNER
// Import an existing Iris RGBA16F AHardwareBuffer; never CPU-lock or copy it.
#include "amaze/HardwareBufferImport.hpp"
#include <stdexcept>

namespace amaze {
namespace {
void requireVk(VkResult result, const char* message) {
    if (result != VK_SUCCESS) throw std::runtime_error(message);
}
}
HardwareBufferImport::HardwareBufferImport(VkPhysicalDevice physical, VkDevice device,
        AHardwareBuffer* buffer, uint32_t width, uint32_t height, VkImageUsageFlags usage)
        : device_(device) {
    if (!physical || !device || !buffer || !width || !height)
        throw std::runtime_error("AMaZE AHB import: invalid owner or dimensions");
    AHardwareBuffer_Desc desc{};
    AHardwareBuffer_describe(buffer, &desc);
    if (desc.width != width || desc.height != height || desc.layers != 1 ||
        desc.format != AHARDWAREBUFFER_FORMAT_R16G16B16A16_FLOAT)
        throw std::runtime_error("AMaZE AHB import: incompatible RGBA16F allocation");
    // Input and output have different Vulkan roles. Never reuse a sampled-only
    // import as a storage output, or claim an unsupported image usage.
    const bool sampledInput = usage == VK_IMAGE_USAGE_SAMPLED_BIT;
    const bool storageOutput = usage == VK_IMAGE_USAGE_STORAGE_BIT;
    if (!sampledInput && !storageOutput)
        throw std::runtime_error("AMaZE AHB import: only sampled CFA or storage RGB permitted");
    if (!(desc.usage & AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT))
        throw std::runtime_error("AMaZE AHB import: requires GLES color-output allocation");
    if (sampledInput && !(desc.usage & AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE))
        throw std::runtime_error("AMaZE AHB import: CFA lacks sampled usage");
    if (storageOutput && !(desc.usage & AHARDWAREBUFFER_USAGE_GPU_DATA_BUFFER))
        throw std::runtime_error("AMaZE AHB import: RGB output lacks Vulkan STORAGE_IMAGE allocation usage");
    auto getProperties = reinterpret_cast<PFN_vkGetAndroidHardwareBufferPropertiesANDROID>(
        vkGetDeviceProcAddr(device, "vkGetAndroidHardwareBufferPropertiesANDROID"));
    if (!getProperties) throw std::runtime_error("AMaZE AHB import: missing Vulkan Android extension");
    VkAndroidHardwareBufferFormatPropertiesANDROID format{};
    format.sType = VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_FORMAT_PROPERTIES_ANDROID;
    VkAndroidHardwareBufferPropertiesANDROID props{};
    props.sType = VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_PROPERTIES_ANDROID;
    props.pNext = &format;
    requireVk(getProperties(device, buffer, &props), "AMaZE AHB import: properties failed");
    if (format.format != VK_FORMAT_R16G16B16A16_SFLOAT || !props.allocationSize)
        throw std::runtime_error("AMaZE AHB import: non-RGBA16F Vulkan format");
    if (sampledInput && !(format.formatFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT))
        throw std::runtime_error("AMaZE AHB import: RGBA16F is not Vulkan sampleable");
    if (storageOutput && !(format.formatFeatures & VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT))
        throw std::runtime_error("AMaZE AHB import: RGBA16F is not Vulkan storage-writable");
    // External AHB memory may require a dedicated allocation. Reject any
    // unsupported alias instead of letting a driver silently reinterpret it.
    AHardwareBuffer_acquire(buffer);
    buffer_ = buffer;
    try {
        VkExternalMemoryImageCreateInfo external{};
        external.sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO;
        external.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_ANDROID_HARDWARE_BUFFER_BIT_ANDROID;
        VkImageCreateInfo imageInfo{};
        imageInfo.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        imageInfo.pNext = &external;
        imageInfo.imageType = VK_IMAGE_TYPE_2D;
        imageInfo.format = VK_FORMAT_R16G16B16A16_SFLOAT;
        imageInfo.extent = {width, height, 1};
        imageInfo.mipLevels = 1;
        imageInfo.arrayLayers = 1;
        imageInfo.samples = VK_SAMPLE_COUNT_1_BIT;
        imageInfo.tiling = VK_IMAGE_TILING_OPTIMAL;
        imageInfo.usage = usage;
        imageInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        imageInfo.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        requireVk(vkCreateImage(device_, &imageInfo, nullptr, &image_), "AMaZE AHB import: image failed");
        // VK_ANDROID_external_memory_android_hardware_buffer: an image backed by an
        // imported AHB is not yet bound here. vkGetImageMemoryRequirements is
        // forbidden before binding; props.memoryTypeBits from the imported AHB
        // is the authoritative memory-type mask for this dedicated allocation.
        uint32_t type = UINT32_MAX;
        const uint32_t compatible = props.memoryTypeBits;
        VkPhysicalDeviceMemoryProperties memProps{};
        vkGetPhysicalDeviceMemoryProperties(physical, &memProps);
        for (uint32_t i = 0; i < memProps.memoryTypeCount; ++i) {
            if (!(compatible & (1u << i))) continue;
            if (memProps.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT) {
                type = i;
                break;
            }
        }
        // Non-device-local memory is legal only when the GPU exposes no
        // device-local compatible type for the imported allocation.
        if (type == UINT32_MAX) for (uint32_t i = 0; i < memProps.memoryTypeCount; ++i)
            if (compatible & (1u << i)) { type = i; break; }
        if (type == UINT32_MAX) throw std::runtime_error("AMaZE AHB import: no memory type");
        VkImportAndroidHardwareBufferInfoANDROID imported{};
        imported.sType = VK_STRUCTURE_TYPE_IMPORT_ANDROID_HARDWARE_BUFFER_INFO_ANDROID;
        imported.buffer = buffer_;
        VkMemoryDedicatedAllocateInfo dedicated{};
        dedicated.sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO;
        dedicated.pNext = &imported;
        dedicated.image = image_;
        VkMemoryAllocateInfo alloc{};
        alloc.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        alloc.pNext = &dedicated;
        alloc.allocationSize = props.allocationSize;
        alloc.memoryTypeIndex = type;
        requireVk(vkAllocateMemory(device_, &alloc, nullptr, &memory_), "AMaZE AHB import: memory failed");
        requireVk(vkBindImageMemory(device_, image_, memory_, 0), "AMaZE AHB import: bind failed");
        VkImageViewCreateInfo viewInfo{};
        viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        viewInfo.image = image_;
        viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
        viewInfo.format = imageInfo.format;
        viewInfo.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        requireVk(vkCreateImageView(device_, &viewInfo, nullptr, &view_), "AMaZE AHB import: view failed");
    } catch (...) {
        if (view_) vkDestroyImageView(device_, view_, nullptr);
        if (image_) vkDestroyImage(device_, image_, nullptr);
        if (memory_) vkFreeMemory(device_, memory_, nullptr);
        AHardwareBuffer_release(buffer_);
        view_ = VK_NULL_HANDLE; image_ = VK_NULL_HANDLE;
        memory_ = VK_NULL_HANDLE; buffer_ = nullptr;
        throw;
    }
}
HardwareBufferImport::~HardwareBufferImport() {
    // Contract: owner must wait for all GPU work before destroying this object.
    if (view_) vkDestroyImageView(device_, view_, nullptr);
    if (image_) vkDestroyImage(device_, image_, nullptr);
    if (memory_) vkFreeMemory(device_, memory_, nullptr);
    if (buffer_) AHardwareBuffer_release(buffer_);
}
} // namespace amaze
