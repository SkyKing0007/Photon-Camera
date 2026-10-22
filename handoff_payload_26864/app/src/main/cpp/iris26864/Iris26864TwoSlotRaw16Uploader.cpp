#include "Iris26864TwoSlotRaw16Uploader.hpp"
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
namespace iris26864 {
namespace {
void check(VkResult r,const char* what){
    if(r!=VK_SUCCESS)throw std::runtime_error(std::string("26864 actual RAW16 transfer: ")+what);
}
void transition(VkCommandBuffer c,VkImage image,VkImageLayout oldLayout,VkImageLayout newLayout,
                VkAccessFlags src,VkAccessFlags dst,VkPipelineStageFlags srcStage,VkPipelineStageFlags dstStage){
    VkImageMemoryBarrier b{};b.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    b.oldLayout=oldLayout;b.newLayout=newLayout;
    b.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
    b.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
    b.image=image;b.srcAccessMask=src;b.dstAccessMask=dst;
    b.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
    vkCmdPipelineBarrier(c,srcStage,dstStage,0,0,nullptr,0,1,&b);
}
}
TwoSlotRaw16Uploader::TwoSlotRaw16Uploader(VkPhysicalDevice p,VkDevice d,
    amaze::CommandSubmissionOwner& submit,uint32_t width,uint32_t height)
  : physical_(p),device_(d),submit_(submit),width_(width),height_(height) {
    if(!p||!d||width<32u||height<32u||(width&1u)||(height&1u)||
       width>16384u||height>16384u||uint64_t(width)*height*2u>INT32_MAX)
        throw std::invalid_argument("26864 invalid frozen RAW16 two-slot extent");
    stagingBytes_=uint64_t(width)*height*2u;
    try {
        // Exactly two device-local R16_UINT images regardless of burst length.
        // 16 MiB padding headroom is for allocation granularity, not a third image.
        images_.reset(new VulkanImageArena(p,d,stagingBytes_*2u+(16ull<<20u)));
        const auto usage=VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT;
        images_->allocate(width,height,VK_FORMAT_R16_UINT,usage);
        images_->allocate(width,height,VK_FORMAT_R16_UINT,usage);
        VkBufferCreateInfo bi{};bi.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bi.size=stagingBytes_;bi.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
        bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        check(vkCreateBuffer(d,&bi,nullptr,&staging_),"staging VkBuffer allocation");
        VkMemoryRequirements mr{};vkGetBufferMemoryRequirements(d,staging_,&mr);
        VkPhysicalDeviceMemoryProperties mp{};vkGetPhysicalDeviceMemoryProperties(p,&mp);
        uint32_t type=UINT32_MAX;
        for(uint32_t i=0;i<mp.memoryTypeCount;++i) {
            const auto flags=mp.memoryTypes[i].propertyFlags;
            if((mr.memoryTypeBits&(1u<<i))&&
               (flags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==
               (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)){
                type=i;break;
            }
        }
        if(type==UINT32_MAX)throw std::runtime_error("26864 no host-coherent GPU transfer staging memory");
        VkMemoryAllocateInfo ai{};ai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize=mr.size;ai.memoryTypeIndex=type;
        check(vkAllocateMemory(d,&ai,nullptr,&stagingMemory_),"staging VkDeviceMemory");
        check(vkBindBufferMemory(d,staging_,stagingMemory_,0),"staging buffer bind");
        check(vkMapMemory(d,stagingMemory_,0,stagingBytes_,0,&stagingMapped_),"staging map");
    }catch(...){
        if(stagingMapped_)vkUnmapMemory(device_,stagingMemory_);
        if(staging_)vkDestroyBuffer(device_,staging_,nullptr);
        if(stagingMemory_)vkFreeMemory(device_,stagingMemory_,nullptr);
        throw;
    }
}
TwoSlotRaw16Uploader::~TwoSlotRaw16Uploader(){
    if(quarantined_)return;
    if(stagingMapped_)vkUnmapMemory(device_,stagingMemory_);
    if(staging_)vkDestroyBuffer(device_,staging_,nullptr);
    if(stagingMemory_)vkFreeMemory(device_,stagingMemory_,nullptr);
    // Destruction of images_ is after this body; all upstream chunks and
    // AMaZE must be successfully fence-completed before caller lets us die.
}
TransientImageView TwoSlotRaw16Uploader::referenceImage()const{return images_->at(0);}
TransientImageView TwoSlotRaw16Uploader::companionImage()const{return images_->at(1);}
void TwoSlotRaw16Uploader::quarantineUnresolved()noexcept{
    quarantined_=true;
    (void)images_.release(); // device teardown retains ownership on lost fence
}
void TwoSlotRaw16Uploader::upload(uint32_t index,uint32_t referenceIndex,
    const std::vector<Raw16PlaneBorrow>& frames){
    if(quarantined_||index>=frames.size()||referenceIndex>=frames.size()||
       !stagingMapped_)throw std::invalid_argument("26864 invalid/poisoned two-slot transfer");
    const auto& frame=frames[index];
    if(!frame.source||frame.width!=width_||frame.height!=height_||!frame.timestamp||
       frame.rowStride<width_*2u||(frame.rowStride&1u)||
       (uint64_t(height_)-1u)*frame.rowStride+uint64_t(width_)*2u>frame.bytes)
        throw std::invalid_argument("26864 invalid frozen direct RAW16 stride/bytes");
    // Immutable JNI buffers are borrowed ONLY during this bounded copy. This
    // does not free the SafeImage or change the capture's exposure metadata.
    auto* dst=static_cast<unsigned char*>(stagingMapped_);
    for(uint32_t row=0;row<height_;++row)
        std::memcpy(dst+uint64_t(row)*width_*2u,
                    frame.source+uint64_t(row)*frame.rowStride,width_*2u);
    const auto output=index==referenceIndex?referenceImage():companionImage();
    try {
        submit_.execute([&](VkCommandBuffer cmd){
            images_->recordInitialGeneralTransitions(cmd);
            transition(cmd,output.image,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                VK_ACCESS_SHADER_READ_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
            VkBufferImageCopy copy{};
            copy.imageSubresource.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
            copy.imageSubresource.mipLevel=0;
            copy.imageSubresource.baseArrayLayer=0;
            copy.imageSubresource.layerCount=1;
            copy.imageExtent={width_,height_,1u};
            vkCmdCopyBufferToImage(cmd,staging_,output.image,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1u,&copy);
            transition(cmd,output.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,
                VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
        });
    }catch(...){
        // Any failed fence or unresolved submission must not permit recycling.
        quarantineUnresolved();
        throw;
    }
}
}
