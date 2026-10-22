#pragma once
// IRIS_26864_HDRP_PINNED_RAW_PREPARE_PYRAMID_CONTRACT_WIP_NOT_ANDROID
// Pinned RAWR revision ce767e80bfce2e1641abf7dad6b1bf504d844fd9:
// hdrp_prepare.comp, hdrp_avg_pool.comp, hdrp_blur.comp and
// HdrPlusRecorder::recordPrepare / recordPyramid. These are real typed GPU
// bindings, NOT an executable end-to-end alignment or camera capture path.
// The isolated renderer MUST continue to fail closed for missing alignment,
// SPIR-V assets, queue ownership and GL/Vulkan interop.
#include "Iris26864HdrqPinnedStageBindings.hpp"
#include "Iris26864HdrqScratchOwner.hpp"
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace iris26864 {
struct HdrpRawSource {
    // External immutable NORMAL RAW image owned by the capture/interop owner.
    // The owner MUST prove the image view has VK_FORMAT_R16_UINT and remains
    // GPU-accessible through the completion fence (not verified by a handle).
    VkImageView r16UintView=VK_NULL_HANDLE;
    VkFormat format=VK_FORMAT_UNDEFINED;
    std::array<float,4> black{};  // (y&1)*2+(x&1), before any WB or LSC
    float white=0.f;
};
struct HdrpRawPreparationInputs {
    std::vector<HdrpRawSource> normals;  // precisely Plan.normals order
    std::vector<HdrqAlignmentLevel> pyramid; // finest to coarsest
    // Pinned geometry tileSize decreases by 2 each level, floor 8.
    uint32_t finestTileSize=0;
};
struct HdrpRawPreparationKernels {
    VulkanKernelExecutor* prepare=nullptr; // shader local 16x16, push 60 B
    VulkanKernelExecutor* pool=nullptr;    // shader local 16x16, push 12 B
    VulkanKernelExecutor* blur=nullptr;    // shader local 16x16, push 40 B
};
inline uint32_t hdrpWord(int32_t signedValue) {
    uint32_t word=0;static_assert(sizeof(word)==sizeof(signedValue),"push word ABI");
    std::memcpy(&word,&signedValue,sizeof(word));return word;
}
inline void validateHdrpRawPreparation(const Plan& p,
                                       const HdrpRawPreparationInputs& in) {
    if(p.path!=Path::HdrPlusFrequency || p.noiseOwner!=NoiseOwner::HdrqReferenceTileRms ||
       !p.createBResources || !p.lscBeforeAmaze || p.lscAfterAmaze ||
       p.normals.size()<2 || p.referenceNormal>=p.normals.size() ||
       p.gainsToReference.size()!=p.normals.size() || in.normals.size()!=p.normals.size() ||
       in.pyramid.empty() || in.pyramid.size()>32 ||
       (in.finestTileSize!=16 && in.finestTileSize!=32))
        throw std::invalid_argument("26864 RAW preparation requires frozen B frequency NORMAL metadata");
    const auto& g=p.geometry;
    if(!g.inputWidth||!g.inputHeight || (g.inputWidth&1u) || (g.inputHeight&1u) ||
       !g.paddedWidth || !g.paddedHeight || (g.paddedWidth&1u) || (g.paddedHeight&1u) ||
       g.inputWidth>32768u || g.inputHeight>32768u ||
       g.paddedWidth>32768u || g.paddedHeight>32768u)
        throw std::invalid_argument("26864 RAW preparation geometry not finite/even");
    const auto& reference=in.normals[p.referenceNormal];
    if(!std::isfinite(reference.white) || reference.white<=0 ||
       p.gainsToReference[p.referenceNormal]!=1.f)
        throw std::invalid_argument("26864 RAW preparation reference exposure/white invalid");
    for(size_t n=0;n<in.normals.size();++n) {
        const auto& f=in.normals[n];
        if(f.r16UintView==VK_NULL_HANDLE || f.format!=VK_FORMAT_R16_UINT ||
           !std::isfinite(f.white) || f.white<=0 ||
           !std::isfinite(p.gainsToReference[n]) || p.gainsToReference[n]<=0.f ||
           p.gainsToReference[n]>65536.f)
            throw std::invalid_argument("26864 missing RAW16 Vulkan view or measured gain");
        for(float b:f.black)
            if(!std::isfinite(b) || b<0.f || b>=f.white)
                throw std::invalid_argument("26864 RAW phase black invalid");
    }
    uint32_t width=g.paddedWidth,height=g.paddedHeight,tile=in.finestTileSize;
    for(const auto& l:in.pyramid) {
        width/=2u;height/=2u;
        if(!width||!height||width<tile||height<tile||
           l.width!=width||l.height!=height ||
           l.tilesX!=width/(tile/2u)-1u||l.tilesY!=height/(tile/2u)-1u ||
           !l.tilesX||!l.tilesY || l.tilesX>65535u||l.tilesY>65535u)
            throw std::invalid_argument("26864 RAW alignment pyramid differs from pinned RAWR geometry");
        tile=std::max(tile/2u,8u);
    }
}
// Only expands RAW preparation and the upstream pyramid prefix. It never
// purports to satisfy the complete CompanionAlignCoarse/Finest owner stages.
// Those need upsample/cost/best kernels and an alignment-store transfer copy.
inline std::vector<HdrqKernelInvocation> buildHdrpRawPreparePrefix(
        const Plan& p,const HdrqDispatch& owner,
        const VulkanHdrqScratchOwner& scratch,
        const HdrpRawPreparationKernels& kernel,
        const HdrpRawPreparationInputs& in,bool buildPyramid) {
    validateHdrpRawPreparation(p,in);
    if(owner.pass>=4 ||
       (owner.step!=HdrqStep::ReferenceAlignPrepare &&
        owner.step!=HdrqStep::CompanionAlignCoarse &&
        owner.step!=HdrqStep::CompanionPaddedOnly))
        throw std::invalid_argument("26864 RAW preparation stage owner invalid");
    const bool reference=owner.step==HdrqStep::ReferenceAlignPrepare;
    if(reference ? (owner.normalIndex!=UINT32_MAX || !p.geometry.passes[owner.pass].align) :
                   (owner.normalIndex>=p.normals.size() || owner.normalIndex==p.referenceNormal ||
                    (owner.step==HdrqStep::CompanionAlignCoarse)!=p.geometry.passes[owner.pass].align))
        throw std::invalid_argument("26864 RAW preparation reference/companion/pass mismatch");
    if(buildPyramid!=p.geometry.passes[owner.pass].align || !kernel.prepare ||
       (buildPyramid && (!kernel.pool || (in.pyramid.size()>1 && !kernel.blur))))
        throw std::invalid_argument("26864 RAW preparation shaders or pyramid ownership missing");
    const uint32_t n=reference?p.referenceNormal:owner.normalIndex;
    const auto& g=p.geometry;
    const auto& frame=in.normals[n];
    const auto& ref=in.normals[p.referenceNormal];
    const auto& pass=g.passes[owner.pass];
    if(pass.padLeft>g.paddedWidth-g.inputWidth ||
       pass.padTop>g.paddedHeight-g.inputHeight ||
       (pass.padLeft&1u) || (pass.padTop&1u))
        throw std::invalid_argument("26864 per-pass Bayer pad violates RAW extent/phase");
    const char* padded=reference?"hdrp_ref_padded":"hdrp_comp_padded";
    const char* prefix=reference?"hdrp_ref_l":"hdrp_comp_l";
    std::vector<HdrqKernelInvocation> out;
    auto emit=[&](VulkanKernelExecutor* pipeline,
                  std::vector<BoundResource> resources,
                  std::vector<uint32_t> push,uint32_t width,uint32_t height) {
        if(!pipeline || !width || !height)
            throw std::invalid_argument("26864 RAW preprocessing pipeline/size missing");
        HdrqKernelInvocation j{};j.ownership=owner;j.kernel=pipeline;
        j.resources=std::move(resources);j.pushWords=std::move(push);
        j.width=width;j.height=height;
        // Validation here is CPU-only, before issuing any command.
        pipeline->preflight(j.resources,j.pushWords.size()*4u,j.width,j.height,j.depth);
        out.push_back(std::move(j));
    };
    BoundResource raw{};raw.binding=0;raw.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
    raw.imageView=frame.r16UintView;
    std::vector<uint32_t> prep;
    prep.reserve(15u);
    for(unsigned i=0;i<4;++i)prep.push_back(hdrqFloatBits(ref.black[i]-frame.black[i]));
    for(float b:ref.black)prep.push_back(hdrqFloatBits(b));
    prep.insert(prep.end(),{pass.padLeft,pass.padTop,g.inputWidth,g.inputHeight,
                             g.paddedWidth,g.paddedHeight,
                             hdrqFloatBits(reference?1.0f:p.gainsToReference[n])});
    emit(kernel.prepare,{raw,hdrqStorageImage(scratch,1,padded)},std::move(prep),
         g.paddedWidth,g.paddedHeight);
    if(!buildPyramid)return out;
    for(size_t level=0;level<in.pyramid.size();++level) {
        const auto& l=in.pyramid[level];
        std::string src=level==0?padded:(std::string(prefix)+std::to_string(level-1));
        if(level) {
            const auto& prev=in.pyramid[level-1];
            // RAWR: separable same-mosaic blur of previous level, binomial
            // kernel 2, stride 1, half-quantized before subsequent pooling.
            auto blur=[&](const std::string& from,const char* to,uint32_t dir) {
                emit(kernel.blur,{hdrqStorageImage(scratch,0,from.c_str()),
                                  hdrqStorageImage(scratch,1,to)},
                    {prev.width,prev.height,0,0,0,0,2u,1u,dir,1u},
                    prev.width,prev.height);
            };
            blur(src,"hdrp_pyr_tmp_a",0);
            blur("hdrp_pyr_tmp_a","hdrp_pyr_tmp_b",1);
            src="hdrp_pyr_tmp_b";
        }
        const auto dst=std::string(prefix)+std::to_string(level);
        emit(kernel.pool,{hdrqStorageImage(scratch,0,src.c_str()),
                          hdrqStorageImage(scratch,1,dst.c_str())},
             {l.width,l.height,hdrqFloatBits(0.f)},l.width,l.height);
    }
    return out;
}
} // namespace iris26864
