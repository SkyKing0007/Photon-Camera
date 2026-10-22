#pragma once
// IRIS_26864_HDRQ_PINNED_STAGE_BINDINGS_PARTIAL_NOT_RUNTIME
// Only THREE real pinned-RAWR shader interfaces are wired. Everything else
// must fail closed; a full Vulkan frequency merge is NOT yet implemented.
// Pinned RAWR commit ce767e80bfce2e1641abf7dad6b1bf504d844fd9:
// hdrq_rms.comp, hdrq_mismatch.comp, hdrq_merge.comp
#include "Iris26864HdrqVulkanRecorder.hpp"
#include "Iris26864HdrqScratchOwner.hpp"
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <vector>
namespace iris26864 {
struct HdrqPinnedKernels {
    VulkanKernelExecutor* rms=nullptr;
    VulkanKernelExecutor* mismatch=nullptr;
    VulkanKernelExecutor* merge=nullptr;
};
struct HdrqFrequencyNorms {
    // MUST be derived from RAWR's pinned frequencyNorms(strength); no
    // unknown defaults or guessed ISP noise constants allowed.
    float robustnessNorm=0.0f,readNoise=0.0f,maxMotionNorm=0.0f;
};
inline uint32_t hdrqFloatBits(float x) {
    uint32_t u=0;static_assert(sizeof(x)==sizeof(u),"float push constant must be IEEE32");
    std::memcpy(&u,&x,sizeof(u));return u;
}
inline BoundResource hdrqStorageImage(const VulkanHdrqScratchOwner& scratch,
                                      uint32_t slot,const char* name) {
    const auto i=scratch.image(name);
    if(!i.view)throw std::runtime_error("26864 HDRq image not allocated");
    BoundResource r{};
    r.binding=slot;r.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;r.imageView=i.view;
    return r;
}
inline BoundResource hdrqStorageBuffer(const VulkanHdrqScratchOwner& scratch,
                                       uint32_t slot,const char* name) {
    const auto b=scratch.buffer(name);
    if(!b.buffer||!b.size)throw std::runtime_error("26864 HDRq SSBO not allocated");
    BoundResource r{};
    r.binding=slot;r.type=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    r.buffer=b.buffer;r.bufferRange=b.size;
    return r;
}
inline HdrqKernelInvocation bindPinnedHdrqStage(const Plan& p,const HdrqDispatch& s,
                const VulkanHdrqScratchOwner& scratch,const HdrqPinnedKernels& kernels,
                const HdrqFrequencyNorms& norms) {
    if(p.path!=Path::HdrPlusFrequency || s.pass>=4 || (s.normalIndex!=UINT32_MAX && s.normalIndex>=p.normals.size()))
        throw std::invalid_argument("26864 HDRq pinned source stage requires B-only frequency owner");
    auto j=HdrqKernelInvocation{};
    j.ownership=s;
    const auto& g=p.geometry;
    if(g.tilesX>UINT32_MAX/16u || g.tilesY>UINT32_MAX/16u)
        throw std::invalid_argument("26864 HDRq workgroup span overflow");
    // All three pinned kernels use the per-tile dispatch grid. RMS uses
    // gl_GlobalInvocationID; mismatch and merge use gl_WorkGroupID.
    const uint32_t lanes=(s.step==HdrqStep::CompanionWienerMerge?8u:16u);
    j.width=g.tilesX*lanes; j.height=g.tilesY*lanes;
    if(s.step==HdrqStep::ReferenceTileRms && s.normalIndex==UINT32_MAX) {
        if(!kernels.rms)throw std::invalid_argument("26864 HDRq RMS SPIR-V missing");
        j.kernel=kernels.rms;
        j.resources={hdrqStorageImage(scratch,0,"hdrq_ref_rgba"),
                     hdrqStorageImage(scratch,1,"hdrq_rms")};
        j.pushWords={g.tilesX,g.tilesY};
    } else if(s.step==HdrqStep::CompanionTileMismatch && s.normalIndex<p.gainsToReference.size() &&
              s.normalIndex!=p.referenceNormal) {
        if(!kernels.mismatch)throw std::invalid_argument("26864 HDRq mismatch SPIR-V missing");
        const float exposureFactor=1.0f/p.gainsToReference[s.normalIndex];
        if(!std::isfinite(exposureFactor)||exposureFactor<=0)
            throw std::invalid_argument("26864 HDRq companion exposure nonfinite");
        j.kernel=kernels.mismatch;
        j.resources={hdrqStorageImage(scratch,0,"hdrq_ref_rgba"),
                     hdrqStorageImage(scratch,1,"hdrq_aligned_rgba"),
                     hdrqStorageImage(scratch,2,"hdrq_rms"),
                     hdrqStorageImage(scratch,3,"hdrq_mismatch")};
        j.pushWords={g.tilesX,g.tilesY,g.rgbaWidth,g.rgbaHeight,
                     hdrqFloatBits(exposureFactor)};
    } else if(s.step==HdrqStep::CompanionWienerMerge && s.normalIndex<p.gainsToReference.size() &&
              s.normalIndex!=p.referenceNormal) {
        if(!kernels.merge)throw std::invalid_argument("26864 HDRq Wiener SPIR-V missing");
        if(!(std::isfinite(norms.robustnessNorm)&&norms.robustnessNorm>0 &&
             std::isfinite(norms.readNoise)&&norms.readNoise>=0 &&
             std::isfinite(norms.maxMotionNorm)&&norms.maxMotionNorm>=1))
            throw std::invalid_argument("26864 HDRq pinned frequency norms missing");
        j.kernel=kernels.merge;
        j.resources={hdrqStorageImage(scratch,0,"hdrq_ref_ft"),
                     hdrqStorageImage(scratch,1,"hdrq_aligned_ft"),
                     hdrqStorageImage(scratch,2,"hdrq_final_ft"),
                     hdrqStorageImage(scratch,3,"hdrq_rms"),
                     hdrqStorageImage(scratch,4,"hdrq_mismatch"),
                     hdrqStorageBuffer(scratch,5,"hdrq_shift_table"),
                     hdrqStorageImage(scratch,6,"hdrq_highlights"),
                     hdrqStorageImage(scratch,7,"hdrq_weight_sum")};
        j.pushWords={g.tilesX,g.tilesY,hdrqFloatBits(norms.robustnessNorm),
                     hdrqFloatBits(norms.readNoise),hdrqFloatBits(norms.maxMotionNorm),
                     1u,hdrqFloatBits(1.0f)};
        // Source uniformExposure=1. Bracketed and LONG color are forbidden.
    } else {
        throw std::invalid_argument("26864 HDRq stage not yet ported to pinned Vulkan shader; no fallback");
    }
    return j;
}
} // namespace iris26864
