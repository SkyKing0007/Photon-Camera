#pragma once
// IRIS_26864_HDRQ_WHOLE_BURST_TYPED_OWNER_NOT_ANDROID
// Full CPU-side RAWR HDR+ frequency command composition, NO runtime SPIR-V,
// Android Vulkan submission, camera/GL handoff or Wronski yet.
#include "Iris26864HdrqFrequencyStageBindings.hpp"
#include "Iris26864HdrpAlignmentBindings.hpp"
#include <stdexcept>
namespace iris26864 {
struct HdrqBurstKernels {
    HdrqFrequencyKernels frequency;
    HdrpRawPreparationKernels raw;
    HdrpAlignmentKernels alignment;
};
struct HdrqBurstMetadata {
    HdrqFrequencyInputs frequency;
    HdrpRawPreparationInputs raw;
};
inline void validateHdrqBurstOwner(const Plan& p,const HdrqBurstMetadata& m) {
    validateHdrqFrequencyInputs(p,m.frequency);
    validateHdrpRawPreparation(p,m.raw);
    if(m.raw.pyramid.front().tilesX!=m.frequency.level0TilesX ||
       m.raw.pyramid.front().tilesY!=m.frequency.level0TilesY ||
       m.frequency.level0HalfTileSize!=m.raw.finestTileSize ||
       m.raw.normals.size()!=m.frequency.normalWhite.size())
        throw std::invalid_argument("26864 frequency warp vs RAW alignment ownership conflict");
    const auto& ref=m.raw.normals[p.referenceNormal];
    if(ref.black!=m.frequency.referenceBlack || ref.white!=m.frequency.referenceWhite)
        throw std::invalid_argument("26864 phase-black/white reference authority diverged");
    for(size_t i=0;i<m.raw.normals.size();++i)
        if(m.raw.normals[i].white!=m.frequency.normalWhite[i])
            throw std::invalid_argument("26864 frame RAW white vs frequency metadata differs");
}
inline void recordHdrqPinnedUniformBurst(const Plan& p,VkCommandBuffer cmd,
     const VulkanHdrqScratchOwner& scratch,
     const HdrqBurstKernels& kernels,const HdrqFrequencyNorms& norms,
     const HdrqBurstMetadata& metadata) {
    validateHdrqBurstOwner(p,metadata);
    recordHdrqVulkanExpandedSchedule(p,cmd,[&](const HdrqDispatch& stage) {
        if(stage.step==HdrqStep::ReferenceAlignPrepare ||
           stage.step==HdrqStep::CompanionPaddedOnly)
            return buildHdrpRawPreparePrefix(p,stage,scratch,kernels.raw,metadata.raw,
                                             p.geometry.passes[stage.pass].align);
        if(stage.step==HdrqStep::CompanionAlignCoarse ||
           stage.step==HdrqStep::CompanionAlignFinest)
            return buildHdrpAlignmentStage(p,stage,scratch,kernels.raw,
                                           kernels.alignment,metadata.raw);
        return std::vector<HdrqKernelInvocation>{bindPinnedHdrqFrequencyStage(
                 p,stage,scratch,kernels.frequency,norms,metadata.frequency)};
    });
}
} // namespace iris26864
