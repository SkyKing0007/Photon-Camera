// IRIS_26943_CAPTURE_TIME_GPU_RAW_RING_IMPORT
// Imported Camera2 AHardwareBuffer -> a permanently owned R16_UINT RAW image.
// Runs only on the bounded optional B/ZSL worker, never a Camera2 callback.
// The memory lifetime extends beyond all GPU fences; unsafe failures poison.
#include "Iris26864TwoSlotRaw16Uploader.hpp"
#include <vulkan/vulkan_android.h>
#include <android/hardware_buffer.h>
#include <android/log.h>
#include <poll.h>
#include <unistd.h>
#include <stdexcept>
#include <string>
#include <vector>
#include <memory>
#include <limits>
#include <cerrno>

namespace iris26864 {
namespace {
void checked(VkResult v, const char* message) {
    if (v != VK_SUCCESS) throw std::runtime_error(message);
}
// All Vulkan objects are destroyed only on a proven completed fence. The
// complete object may instead be intentionally quarantined on device loss.
struct Imported final {
    VkDevice device{};
    VkImage image{};
    VkBuffer buffer{};
    VkDeviceMemory memory{};
    VkImageLayout imageLayout = VK_IMAGE_LAYOUT_GENERAL;
    explicit Imported(VkDevice d) : device(d) {}
    ~Imported() {
        if (image) vkDestroyImage(device,image,nullptr);
        if (buffer) vkDestroyBuffer(device,buffer,nullptr);
        if (memory) vkFreeMemory(device,memory,nullptr);
    }
};
uint32_t memoryType(VkPhysicalDevice p, uint32_t compatible) {
    VkPhysicalDeviceMemoryProperties mem{};
    vkGetPhysicalDeviceMemoryProperties(p,&mem);
    for (uint32_t i=0; i<mem.memoryTypeCount; ++i)
        if ((compatible&(1u<<i)) &&
            (mem.memoryTypes[i].propertyFlags&VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)) return i;
    for (uint32_t i=0; i<mem.memoryTypeCount; ++i)
        if (compatible&(1u<<i)) return i;
    throw std::runtime_error("26943 RAW AHB incompatible memory type");
}
void waitForCameraFence(int fenceFd) {
    if (fenceFd < 0) return; // API 33 invalid fence means already signaled.
    struct pollfd pfd{fenceFd,POLLIN,0};
    int rc=0;
    do { rc=poll(&pfd,1,250); } while (rc<0 && errno==EINTR);
    if (rc!=1 || !(pfd.revents&(POLLIN|POLLHUP)))
        throw std::runtime_error("26943 camera acquire fence not signaled in optional 250ms budget");
}
void barrier(VkCommandBuffer cb, VkImage img, VkImageLayout oldL, VkImageLayout newL,
             VkAccessFlags src, VkAccessFlags dst, VkPipelineStageFlags from,
             VkPipelineStageFlags to, uint32_t oldFamily=VK_QUEUE_FAMILY_IGNORED,
             uint32_t newFamily=VK_QUEUE_FAMILY_IGNORED) {
    VkImageMemoryBarrier b{};
    b.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    b.srcAccessMask=src;b.dstAccessMask=dst;
    b.oldLayout=oldL;b.newLayout=newL;
    b.srcQueueFamilyIndex=oldFamily;b.dstQueueFamilyIndex=newFamily;
    b.image=img;
    b.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u};
    vkCmdPipelineBarrier(cb,from,to,0,0,nullptr,0,nullptr,1,&b);
}
std::unique_ptr<Imported> importDirect(VkPhysicalDevice p,VkDevice d,AHardwareBuffer* ahb,
                                      uint32_t width,uint32_t height) {
    auto get=reinterpret_cast<PFN_vkGetAndroidHardwareBufferPropertiesANDROID>(
        vkGetDeviceProcAddr(d,"vkGetAndroidHardwareBufferPropertiesANDROID"));
    if (!get) throw std::runtime_error("26943 AHB Vulkan extension unavailable");
    VkAndroidHardwareBufferFormatPropertiesANDROID fmt{};
    fmt.sType=VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_FORMAT_PROPERTIES_ANDROID;
    VkAndroidHardwareBufferPropertiesANDROID props{};
    props.sType=VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_PROPERTIES_ANDROID;
    props.pNext=&fmt;
    checked(get(d,ahb,&props),"26943 RAW AHB image properties");
    if (fmt.format!=VK_FORMAT_R16_UINT || !props.memoryTypeBits || !props.allocationSize)
        throw std::runtime_error("26943 RAW AHB direct R16_UINT not available");
    VkPhysicalDeviceExternalImageFormatInfo external{};
    external.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_IMAGE_FORMAT_INFO;
    external.handleType=VK_EXTERNAL_MEMORY_HANDLE_TYPE_ANDROID_HARDWARE_BUFFER_BIT_ANDROID;
    VkPhysicalDeviceImageFormatInfo2 fi{};
    fi.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2;
    fi.pNext=&external;fi.format=VK_FORMAT_R16_UINT;
    fi.type=VK_IMAGE_TYPE_2D;fi.tiling=VK_IMAGE_TILING_OPTIMAL;
    fi.usage=VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    VkExternalImageFormatProperties caps{};
    caps.sType=VK_STRUCTURE_TYPE_EXTERNAL_IMAGE_FORMAT_PROPERTIES;
    VkImageFormatProperties2 supported{};
    supported.sType=VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2;
    supported.pNext=&caps;
    if (vkGetPhysicalDeviceImageFormatProperties2(p,&fi,&supported)!=VK_SUCCESS ||
        !(caps.externalMemoryProperties.externalMemoryFeatures&VK_EXTERNAL_MEMORY_FEATURE_IMPORTABLE_BIT))
        throw std::runtime_error("26943 RAW AHB image transfer-source import unsupported");
    auto imported=std::make_unique<Imported>(d);
    VkExternalMemoryImageCreateInfo em{};
    em.sType=VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO;
    em.handleTypes=VK_EXTERNAL_MEMORY_HANDLE_TYPE_ANDROID_HARDWARE_BUFFER_BIT_ANDROID;
    VkImageCreateInfo ci{};
    ci.sType=VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ci.pNext=&em;
    ci.imageType=VK_IMAGE_TYPE_2D;
    ci.format=VK_FORMAT_R16_UINT;
    ci.extent={width,height,1u};ci.mipLevels=ci.arrayLayers=1u;
    ci.samples=VK_SAMPLE_COUNT_1_BIT;
    ci.tiling=VK_IMAGE_TILING_OPTIMAL;
    ci.usage=VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    ci.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
    checked(vkCreateImage(d,&ci,nullptr,&imported->image),"26943 direct imported image");
    VkImportAndroidHardwareBufferInfoANDROID ai{};
    ai.sType=VK_STRUCTURE_TYPE_IMPORT_ANDROID_HARDWARE_BUFFER_INFO_ANDROID;
    ai.buffer=ahb;
    VkMemoryDedicatedAllocateInfo dedicated{};
    dedicated.sType=VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO;
    dedicated.pNext=&ai;dedicated.image=imported->image;
    VkMemoryAllocateInfo alloc{};
    alloc.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc.pNext=&dedicated;
    alloc.allocationSize=props.allocationSize;
    alloc.memoryTypeIndex=memoryType(p,props.memoryTypeBits);
    checked(vkAllocateMemory(d,&alloc,nullptr,&imported->memory),"26943 direct AHB memory");
    checked(vkBindImageMemory(d,imported->image,imported->memory,0),"26943 direct AHB bind");
    return imported;
}
std::unique_ptr<Imported> importGpuBuffer(VkPhysicalDevice p,VkDevice d,AHardwareBuffer* ahb,
                                          uint32_t stride,uint32_t height) {
    auto get=reinterpret_cast<PFN_vkGetAndroidHardwareBufferPropertiesANDROID>(
        vkGetDeviceProcAddr(d,"vkGetAndroidHardwareBufferPropertiesANDROID"));
    if (!get) throw std::runtime_error("26943 RAW AHB buffer import extension unavailable");
    VkAndroidHardwareBufferPropertiesANDROID props{};
    props.sType=VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_PROPERTIES_ANDROID;
    checked(get(d,ahb,&props),"26943 AHB buffer properties");
    if (!props.allocationSize || !props.memoryTypeBits || uint64_t(stride)*height*2u>props.allocationSize)
        throw std::runtime_error("26943 AHB buffer size/stride incompatible");
    auto imported=std::make_unique<Imported>(d);
    // Same proven RAWR plain-buffer import route: Adreno devices can reject
    // the optional VkExternalMemoryBufferCreateInfo while accepting the AHB.
    VkBufferCreateInfo bi{};
    bi.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bi.size=uint64_t(stride)*height*2u;
    bi.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
    checked(vkCreateBuffer(d,&bi,nullptr,&imported->buffer),"26943 imported AHB transfer buffer");
    VkMemoryRequirements req{};
    vkGetBufferMemoryRequirements(d,imported->buffer,&req);
    if (req.size>props.allocationSize) throw std::runtime_error("26943 raw buffer requirements exceed AHB allocation");
    VkImportAndroidHardwareBufferInfoANDROID ai{};
    ai.sType=VK_STRUCTURE_TYPE_IMPORT_ANDROID_HARDWARE_BUFFER_INFO_ANDROID;
    ai.buffer=ahb;
    VkMemoryDedicatedAllocateInfo dedicated{};
    dedicated.sType=VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO;
    dedicated.pNext=&ai;dedicated.buffer=imported->buffer;
    VkMemoryAllocateInfo alloc{};
    alloc.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc.pNext=&dedicated;
    alloc.allocationSize=props.allocationSize;
    alloc.memoryTypeIndex=memoryType(p,props.memoryTypeBits);
    checked(vkAllocateMemory(d,&alloc,nullptr,&imported->memory),"26943 imported RAW buffer memory");
    checked(vkBindBufferMemory(d,imported->buffer,imported->memory,0),"26943 imported RAW buffer bind");
    return imported;
}
}
void TwoSlotRaw16Uploader::uploadHardwareBufferInto(uint32_t slot,AHardwareBuffer* ahb,int cameraFenceFd,uint32_t queueFamily) {
    if (quarantined_ || !ahb || slot>=slots_ || queueFamily==VK_QUEUE_FAMILY_IGNORED)
        throw std::invalid_argument("26943 invalid RAW AHB ring slot/queue family");
    AHardwareBuffer_Desc desc{};
    AHardwareBuffer_describe(ahb,&desc);
    if (desc.width!=width_||desc.height!=height_||desc.layers!=1u||
        desc.stride<width_||uint64_t(desc.stride)*height_*2u>INT32_MAX)
        throw std::invalid_argument("26943 AHB dimensions/stride mismatch");
    // No CPU synchronization on the real-time camera callback. Camera fence
    // completion is proven here on the optional worker before Vulkan reads.
    waitForCameraFence(cameraFenceFd);
    std::unique_ptr<Imported> source;
    bool imageSource=false;
    try { source=importDirect(physical_,device_,ahb,width_,height_);imageSource=true; }
    catch (const std::exception& e) {
        __android_log_print(ANDROID_LOG_INFO,"Iris26943","RAW_DIRECT_IMPORT_UNAVAILABLE why=%s",e.what());
    }
    if (!source) try {source=importGpuBuffer(physical_,device_,ahb,desc.stride,height_);}
    catch (const std::exception& e) {
        __android_log_print(ANDROID_LOG_INFO,"Iris26943","RAW_GPU_BUFFER_IMPORT_UNAVAILABLE why=%s",e.what());
    }
    if (source) {
        // The two Vulkan import variants must not be retried after an
        // uncertain submit. Keep their AHB and imported memory alive instead.
        try {
            const auto output=imageAt(slot);
            submit_.execute([&](VkCommandBuffer cmd){
                images_->recordInitialGeneralTransitions(cmd);
                if (imageSource) {
                    // Camera/foreign producer ownership is acquired only after
                    // the Camera2 sync FD was signaled on the ingress worker.
                    barrier(cmd,source->image,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                        0,VK_ACCESS_TRANSFER_READ_BIT,
                        VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,
                        VK_QUEUE_FAMILY_FOREIGN_EXT,queueFamily);
                } else {
                    VkMemoryBarrier b{};
                    b.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
                    b.srcAccessMask=VK_ACCESS_HOST_WRITE_BIT;
                    b.dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT;
                    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_HOST_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,
                        0,1,&b,0,nullptr,0,nullptr);
                }
                barrier(cmd,output.image,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                    VK_ACCESS_SHADER_READ_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,
                    VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
                if (imageSource) {
                    VkImageCopy cp{};
                    cp.srcSubresource.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
                    cp.srcSubresource.layerCount=1;
                    cp.dstSubresource.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
                    cp.dstSubresource.layerCount=1;
                    cp.extent={width_,height_,1};
                    vkCmdCopyImage(cmd,source->image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                        output.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&cp);
                } else {
                    VkBufferImageCopy cp{};
                    cp.bufferRowLength=desc.stride;
                    cp.imageSubresource.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
                    cp.imageSubresource.layerCount=1;
                    cp.imageExtent={width_,height_,1};
                    vkCmdCopyBufferToImage(cmd,source->buffer,output.image,
                        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&cp);
                }
                barrier(cmd,output.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,
                    VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT,
                    VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            });
            __android_log_print(ANDROID_LOG_INFO,"Iris26943","RAW_CAPTURE_STAGE route=%s bytes=%llu",
                imageSource?"direct_image":"gpu_buffer_copy",
                static_cast<unsigned long long>(uint64_t(width_)*height_*2u));
            return;
        } catch (...) {
            quarantineUnresolved();
            // Imported resources and their AHB backing must not be released
            // after a possibly submitted but unresolved GPU queue.
            (void)source.release();
            throw;
        }
    }
    // AHB device import unavailable: attempt a CPU-read mapping only on this
    // worker, never inside ImageReader. If impossible, discard this OPTIONAL
    // ring update; at shutter retain the known 26942 frozen-RAW fallback.
    AHardwareBuffer_Planes planes{};
    if (AHardwareBuffer_lockPlanes(ahb,AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN,-1,nullptr,&planes)!=0)
        throw std::runtime_error("26943 GPU/CPU AHB ingress not supported; use original postshutter upload");
    struct Unlock {AHardwareBuffer* b;~Unlock(){AHardwareBuffer_unlock(b,nullptr);}} unlock{ahb};
    if (planes.planeCount!=1 || !planes.planes[0].data ||
        planes.planes[0].pixelStride!=2 || planes.planes[0].rowStride<width_*2u)
        throw std::runtime_error("26943 AHB CPU fallback plane incompatible");
    Raw16PlaneBorrow frame{};
    frame.source=static_cast<const unsigned char*>(planes.planes[0].data);
    frame.bytes=uint64_t(planes.planes[0].rowStride)*height_;
    frame.rowStride=planes.planes[0].rowStride;
    frame.width=width_;frame.height=height_;frame.timestamp=1u;
    const std::vector<Raw16PlaneBorrow> one{frame};
    uploadInto(0u,slot,one);
    __android_log_print(ANDROID_LOG_INFO,"Iris26943","RAW_CAPTURE_STAGE route=cpu_worker_fallback bytes=%llu",
        static_cast<unsigned long long>(uint64_t(width_)*height_*2u));
}
} // namespace iris26864
