#include "Iris26864HdrqCanonicalGpuBridge.hpp"
#include <array>
#include <cstring>
#include <stdexcept>
#include <vector>
namespace iris26864 {
namespace {
struct alignas(16) Push final {
    uint32_t width=0,height=0,pattern=0,lscWidth=0;
    uint32_t lscHeight=0,originX=0,originY=0,fullWidth=0;
    uint32_t fullHeight=0,clipRequired=0,reserved0=0,reserved1=0;
    float black[4]{},invRange[4]{};
    float clipThreshold=0;
    uint32_t tail0=0,tail1=0,tail2=0;
};
static_assert(sizeof(Push)==96,"26864 GPU bridge push ABI size must stay 96 (std430 vec4+padding)");
std::vector<BoundResource> bind(const HdrqCanonicalGpuFrame& f){
    auto img=[&](uint32_t binding,VkImageView view){BoundResource b{};
        b.binding=binding;b.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;b.imageView=view;return b;};
    BoundResource lsc{};lsc.binding=4;lsc.type=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    lsc.buffer=f.camera2LscBuffer;lsc.bufferRange=f.camera2LscBytes;
    return {img(0,f.r32CfaView),img(1,f.rawReferenceR16uView),
            img(2,f.packedRgba16fView),img(3,f.clipR16uView),lsc};
}
Push makePush(const CfaBridgeConfig& c){
    Push p{};p.width=c.width;p.height=c.height;p.pattern=c.pattern;
    p.lscWidth=c.lscWidth;p.lscHeight=c.lscHeight;
    p.originX=c.originX;p.originY=c.originY;
    p.fullWidth=c.fullSensorWidth;p.fullHeight=c.fullSensorHeight;
    p.clipRequired=1; // Capture reference always required; never guess clipped pixels.
    for(int i=0;i<4;++i){p.black[i]=c.blackPhase[size_t(i)];p.invRange[i]=c.inverseRangePhase[size_t(i)];}
    p.clipThreshold=c.clippingThreshold;
    return p;
}
}
void preflightCanonicalCfaBridge(const VulkanKernelExecutor& bridge,
                                 const HdrqCanonicalGpuFrame& f){
    const auto& c=f.cfg;
    if(c.width<32u||c.height<32u||(c.width&1u)||(c.height&1u)||
       c.width>16384u||c.height>16384u||c.pattern>3u||
       c.fullSensorWidth<c.width||c.fullSensorHeight<c.height||
       c.originX>c.fullSensorWidth-c.width||c.originY>c.fullSensorHeight-c.height||
       c.pattern!=patternAtCrop(f.physicalSensorPattern,c.originX,c.originY)||
       !f.r32CfaImage||!f.r32CfaView||!f.rawReferenceR16uView||
       !f.packedRgba16fImage||!f.packedRgba16fView||!f.clipR16uView||
       f.r32CfaImage==f.packedRgba16fImage||
       (c.lscWidth==0u)!=(c.lscHeight==0u)||
       (c.lscWidth && (c.lscWidth<2u||c.lscHeight<2u)))
        throw std::invalid_argument("26864 HDRq invalid CFA/Amaze image ownership, dimensions or Bayer crop");
    if(!f.camera2LscBuffer || f.camera2LscBytes <
            (c.lscWidth?uint64_t(c.lscWidth)*c.lscHeight*16u:16u))
        throw std::invalid_argument("26864 HDRq LSC buffer absent/undersized (dummy required when unavailable)");
    if(!(c.clippingThreshold>0.f&&c.clippingThreshold<=1.f))
        throw std::invalid_argument("26864 HDRq clip provenance threshold invalid");
    for(int i=0;i<4;++i){
        if(!(c.blackPhase[size_t(i)]>=0.f)||!(c.inverseRangePhase[size_t(i)]>0.f))
            throw std::invalid_argument("26864 HDRq raw per-phase normalization invalid");
    }
    bridge.preflight(bind(f),sizeof(Push),c.width/2u,c.height/2u);
}
void recordCanonicalCfaForAmaze(VkCommandBuffer cmd,
                                const VulkanKernelExecutor& bridge,
                                const HdrqCanonicalGpuFrame& frame){
    if(!cmd)throw std::invalid_argument("26864 HDRq missing single 26863 command buffer");
    preflightCanonicalCfaBridge(bridge,frame);
    VkMemoryBarrier before{};before.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    before.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
    before.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&before,0,nullptr,0,nullptr);
    auto push=makePush(frame.cfg);
    bridge.record(cmd,bind(frame),&push,sizeof(push),frame.cfg.width/2u,frame.cfg.height/2u);
    // Shader wrote the SAME canonical CFA texture that 26863 AMaZE consumes.
    // Both stages must record in this command buffer before ONE queue submit.
    VkMemoryBarrier after{};after.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    after.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
    after.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&after,0,nullptr,0,nullptr);
}
}
