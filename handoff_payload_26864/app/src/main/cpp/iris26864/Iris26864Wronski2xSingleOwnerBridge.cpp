#include "Iris26864Wronski2xSingleOwnerBridge.hpp"
#include <cmath>
#include <stdexcept>
#include <vector>

namespace iris26864::wronski2x {
namespace {
std::vector<BoundResource> resources(const SingleOwner2xFrames& f) {
    auto img=[](uint32_t binding, const SurfaceSpec& s) {
        BoundResource out{}; out.binding=binding;
        out.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
        out.imageView=VkImageView(s.view);return out;
    };
    BoundResource lsc{};lsc.binding=3u;lsc.type=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    lsc.buffer=f.lscBuffer;lsc.bufferRange=f.lscBytes;
    return {img(0,f.mergedCameraRgb),img(1,f.packedCfa),
            img(2,f.sensorClip),lsc,img(4,f.originalReferenceRaw)};
}
void computeWriteReadBarrier(VkCommandBuffer cmd){
    VkMemoryBarrier b{};b.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    b.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
    b.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1u,&b,0,nullptr,0,nullptr);
}
}
PreparedSingleOwner2x prepareSingleOwner2x(
    const SingleOwner2xFrames& f,
    const VulkanKernelExecutor& packedKernel,
    const amaze::AmazePipeline& amaze) {
    if (!f.rawrBurstNoiseFitted)
        throw std::invalid_argument(
            "26864 Wronski requires measured RAWR RAW-burst noise; no Camera2/configured noise fallback");
    auto p=validatePacked2xOutput(f.geometry,f.lsc,f.mergedCameraRgb,
        f.originalReferenceRaw,f.packedCfa,f.sensorClip);
    if (!f.lscBuffer || f.lscBytes <
            (f.lsc.texels.empty()?16u:uint64_t(f.lsc.texels.size())*16u) ||
        f.geometry.outWidth<32u||f.geometry.outHeight<32u ||
        f.geometry.outWidth>16384u||f.geometry.outHeight>16384u ||
        !f.amazeRgb.image||!f.amazeRgb.view||
        f.amazeRgb.format!=RGBA16_SFLOAT ||
        f.amazeRgb.width!=f.geometry.outWidth ||
        f.amazeRgb.height!=f.geometry.outHeight ||
        f.amazeRgb.image==f.packedCfa.image ||
        f.amazeRgb.image==f.mergedCameraRgb.image ||
        f.amazeRgb.image==f.originalReferenceRaw.image ||
        f.amazeRgb.image==f.sensorClip.image ||
        f.amazeRgb.view==f.packedCfa.view ||
        f.amazeRgb.view==f.sensorClip.view ||
        f.amazeRgb.view==f.originalReferenceRaw.view ||
        f.amazeRgb.view==f.mergedCameraRgb.view)
        throw std::invalid_argument("26864 Wronski output/Amaze/LSC ownership invalid");
    for (auto wb:f.whiteBalance)
        if (!std::isfinite(wb) || wb<=0.f)
            throw std::invalid_argument("26864 Wronski non-physical WB gain");
    const auto& cfg=amaze.config();
    if (cfg.inputMode!=amaze::InputMode::PackedCfaRgba16fImage ||
        cfg.width!=f.geometry.outWidth||cfg.height!=f.geometry.outHeight ||
        uint32_t(cfg.pattern)!=localPattern(f.geometry))
        throw std::invalid_argument("26864 26863 AMaZE compiled pipeline config mismatch");
    packedKernel.preflight(resources(f),sizeof(PackedPc),
                           f.packedCfa.width,f.packedCfa.height);
    PreparedSingleOwner2x a{};a.kernel=p;
    a.amazeInput.image=VkImage(f.packedCfa.image);
    a.amazeInput.view=VkImageView(f.packedCfa.view);
    a.amazeInput.format=VK_FORMAT_R16G16B16A16_SFLOAT;
    a.amazeInput.layout=VK_IMAGE_LAYOUT_GENERAL;
    a.amazeInput.width=f.packedCfa.width;
    a.amazeInput.height=f.packedCfa.height;
    a.amazeInput.rawWidth=f.geometry.outWidth;
    a.amazeInput.rawHeight=f.geometry.outHeight;
    a.amazeInput.pattern=amaze::BayerPattern(localPattern(f.geometry));
    a.amazeOutput.image=VkImage(f.amazeRgb.image);
    a.amazeOutput.view=VkImageView(f.amazeRgb.view);
    a.amazeOutput.format=VK_FORMAT_R16G16B16A16_SFLOAT;
    a.amazeOutput.layout=VK_IMAGE_LAYOUT_GENERAL;
    a.amazeOutput.width=f.amazeRgb.width;
    a.amazeOutput.height=f.amazeRgb.height;
    a.clipping={VkImage(f.sensorClip.image),VkImageView(f.sensorClip.view),
        f.sensorClip.width,f.sensorClip.height,localPattern(f.geometry)};
    // Map absent is a valid RAWR identity-LSC stage, not evidence that any
    // legacy Iris post-AMaZE correction may run on this RAWR output.
    a.clipping.preAmazeLscStageComplete = true;
    a.clipping.physicalLscMapPresent = !f.lsc.texels.empty();
    return a;
}
ClipSidecarReceipt recordWronski2xToAmaze(VkCommandBuffer cmd,
    const SingleOwner2xFrames& f,
    const VulkanKernelExecutor& packedKernel,
    amaze::AmazePipeline& amaze) {
    if (cmd==VK_NULL_HANDLE)
        throw std::invalid_argument("26864 Wronski missing inherited command buffer");
    // CPU preflight of every owner and image BEFORE issuing a Vulkan command.
    const auto a=prepareSingleOwner2x(f,packedKernel,amaze);
    // Prior RAWR a11_finalize writes camera RGB; packing reads that image.
    computeWriteReadBarrier(cmd);
    packedKernel.record(cmd,resources(f),&a.kernel.push,sizeof(PackedPc),
                        f.packedCfa.width,f.packedCfa.height,1u,false);
    // AMaZE reads the exact same packed image/view after this barrier.
    computeWriteReadBarrier(cmd);
    amaze.record(cmd,a.amazeInput,a.amazeOutput,f.whiteBalance);
    // Sensor clip is NOT consumed by AMaZE; caller owns its sidecar lifetime.
    return a.clipping;
}
} // namespace iris26864::wronski2x
