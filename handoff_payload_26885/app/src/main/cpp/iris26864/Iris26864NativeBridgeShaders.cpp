#include "Iris26864NativeBridgeShaders.hpp"
#include "iris26864_hdrq_cfa_bridge.h"
#include "iris26864_wronski_cfa_bridge.h"
#include "iris26864_clip_to_gl_bridge.h"
#include "iris26864_wronski_chroma_guide.h"
#include <stdexcept>
#include <vector>
namespace iris26864 {
namespace {
std::unique_ptr<VulkanKernelExecutor> create(VkDevice device,
    const unsigned char* bytes, size_t byteCount, bool wronski) {
    if(!device||!bytes||byteCount<84u||(byteCount%4u)!=0u||
       reinterpret_cast<uintptr_t>(bytes)%alignof(uint32_t))
        throw std::invalid_argument("26864 invalid genuinely-compiled SPIR-V bridge");
    ShaderBinary shader{};
    shader.words=reinterpret_cast<const uint32_t*>(bytes);
    shader.wordCount=byteCount/sizeof(uint32_t);
    shader.workgroupX=16u;shader.workgroupY=16u;shader.workgroupZ=1u;
    if(shader.words[0]!=0x07230203u)
        throw std::runtime_error("26864 generated shader SPIR-V magic mismatch");
    const std::vector<ComputeBinding> interface={
        {0,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
        {1,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
        {2,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
        {3,wronski?VK_DESCRIPTOR_TYPE_STORAGE_BUFFER:VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
        {4,wronski?VK_DESCRIPTOR_TYPE_STORAGE_IMAGE:VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}};
    return std::make_unique<VulkanKernelExecutor>(device,shader,interface,96u,1u);
}
}
std::unique_ptr<VulkanKernelExecutor> makeRealHdrqCfaBridge(VkDevice device){
    return create(device,iris26864_hdrq_cfa_bridge_spv,
                  iris26864_hdrq_cfa_bridge_spv_size,false);
}
std::unique_ptr<VulkanKernelExecutor> makeRealSensorClipToGlBridge(VkDevice device){
    const auto* bytes=iris26864_clip_to_gl_bridge_spv;
    const auto size=iris26864_clip_to_gl_bridge_spv_size;
    if(!device||size<84u||(size%4u)!=0u||
       reinterpret_cast<const uint32_t*>(bytes)[0]!=0x07230203u)
        throw std::invalid_argument("26864 missing genuine clipping SPIR-V");
    ShaderBinary shader{};
    shader.words=reinterpret_cast<const uint32_t*>(bytes);
    shader.wordCount=size/sizeof(uint32_t);
    shader.workgroupX=16;shader.workgroupY=16;shader.workgroupZ=1;
    return std::make_unique<VulkanKernelExecutor>(device,shader,
        std::vector<ComputeBinding>{{0,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
                                    {1,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}},16u,1u);
}
std::unique_ptr<VulkanKernelExecutor> makeRealWronskiChromaGuide(VkDevice device){
    const auto* bytes=iris26864_wronski_chroma_guide_spv;
    const auto byteCount=iris26864_wronski_chroma_guide_spv_size;
    if(!device||!bytes||byteCount<84u||byteCount%4u!=0u||
       reinterpret_cast<uintptr_t>(bytes)%alignof(uint32_t)||
       reinterpret_cast<const uint32_t*>(bytes)[0]!=0x07230203u)
        throw std::runtime_error("26885 real B-ON Wronski chroma SPIR-V invalid");
    ShaderBinary shader{};
    shader.words=reinterpret_cast<const uint32_t*>(bytes);
    shader.wordCount=byteCount/sizeof(uint32_t);
    shader.workgroupX=16u;shader.workgroupY=16u;shader.workgroupZ=1u;
    return std::make_unique<VulkanKernelExecutor>(device,shader,
        std::vector<ComputeBinding>{{0,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
                                    {1,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
                                    {2,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},
                                    {3,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}},112u,1u);
}
std::unique_ptr<VulkanKernelExecutor> makeRealWronskiCfaBridge(VkDevice device){
    return create(device,iris26864_wronski_cfa_bridge_spv,
                  iris26864_wronski_cfa_bridge_spv_size,true);
}
}
