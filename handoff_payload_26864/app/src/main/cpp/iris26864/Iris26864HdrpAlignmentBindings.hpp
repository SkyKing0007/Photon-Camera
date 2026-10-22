#pragma once
// IRIS_26864_HDRP_PINNED_TILE_ALIGNMENT_PREFIX_PROOF_NOT_ANDROID
// Pinned RAWR HdrPlusRecorder::recordCompanionAlignLevel, coarse -> fine,
// with VkCmdFillBuffer coarsest-init and VkCmdCopyBuffer align-once store.
// MUST be combined with the whole-burst expanded recorder and tested SPIR-V
// before linking to any Android path. This does NOT own the camera RAW source.
#include "Iris26864HdrpRawPrepareBindings.hpp"
#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace iris26864 {
struct HdrpAlignmentKernels {
    VulkanKernelExecutor* upsample=nullptr; // 2 SSBO, 24-byte push, 16x16
    VulkanKernelExecutor* correct=nullptr;  // 2 R32F + 2 SSBO, 32-byte push, 64x1
    VulkanKernelExecutor* tileDiff=nullptr; // 2 R32F + 2 SSBO, 32-byte push, 256x1
    VulkanKernelExecutor* best=nullptr;     // 3 SSBO, 12-byte push, 16x16
};
inline std::vector<HdrqKernelInvocation> buildHdrpAlignmentStage(
     const Plan& p,const HdrqDispatch& stage,
     const VulkanHdrqScratchOwner& scratch,
     const HdrpRawPreparationKernels& prep,
     const HdrpAlignmentKernels& align,
     const HdrpRawPreparationInputs& raw) {
    validateHdrpRawPreparation(p,raw);
    if(stage.pass>=4 || !p.geometry.passes[stage.pass].align ||
       stage.normalIndex>=p.normals.size() ||stage.normalIndex==p.referenceNormal ||
       (stage.step!=HdrqStep::CompanionAlignCoarse &&
        stage.step!=HdrqStep::CompanionAlignFinest))
        throw std::invalid_argument("26864 alignment requires frozen companion and aligning pass");
    if(!align.upsample || !align.correct || !align.tileDiff || !align.best)
        throw std::invalid_argument("26864 pinned alignment kernel absent");
    std::vector<HdrqKernelInvocation> out;
    if(stage.step==HdrqStep::CompanionAlignCoarse) {
        out=buildHdrpRawPreparePrefix(p,stage,scratch,prep,raw,true);
        // Coarsest RAWR upsample consumes cur[0] even though downscale=0.
        // Initialize exactly this source vector to zero rather than consuming
        // uninitialized driver storage. Every other tile comes from BestTile.
        const auto a=scratch.buffer("hdrp_align_a");
        if(a.buffer==VK_NULL_HANDLE || a.size<8u)
            throw std::invalid_argument("26864 align coarsest zero-init buffer absent");
        HdrqKernelInvocation z{};z.kind=HdrqRecordedKind::FillAlignmentZero;
        z.ownership=stage;z.transferDst=a.buffer;z.transferBytes=8u;
        out.push_back(z);
    }
    const auto makeLevel=[&](size_t n) {
        const auto& l=raw.pyramid[n];
        const bool coarsest=n+1u==raw.pyramid.size();
        const uint32_t srcX=coarsest?1u:raw.pyramid[n+1u].tilesX;
        const uint32_t srcY=coarsest?1u:raw.pyramid[n+1u].tilesY;
        const uint32_t downscale=coarsest?0u:2u;
        const uint32_t tile=std::max(raw.finestTileSize >> std::min<size_t>(n,30u),8u);
        // Shader uses shared arrays MAX_TILE=32 and tile sizes remain even.
        if(tile<8u||tile>32u || l.tilesX>UINT32_MAX/256u ||
           l.tilesY>UINT32_MAX/16u ||
           uint64_t(l.tilesX)*l.tilesY*100u>scratch.buffer("hdrp_tile_cost").size)
            throw std::invalid_argument("26864 alignment tile or scratch cost overflow");
        auto bind=[&](VulkanKernelExecutor* kernel,std::vector<BoundResource> res,
                      std::vector<uint32_t> push,uint32_t w,uint32_t h) {
            HdrqKernelInvocation j{};j.ownership=stage;j.kernel=kernel;
            j.resources=std::move(res);j.pushWords=std::move(push);j.width=w;j.height=h;
            kernel->preflight(j.resources,j.pushWords.size()*4u,w,h);
            out.push_back(std::move(j));
        };
        auto cur=hdrqStorageBuffer(scratch,0,"hdrp_align_a");
        auto previous=hdrqStorageBuffer(scratch,1,"hdrp_align_b");
        const auto ca=std::string("hdrp_ref_l")+std::to_string(n);
        const auto cb=std::string("hdrp_comp_l")+std::to_string(n);
        bind(align.upsample,{cur,previous},
             {srcX,srcY,l.tilesX,l.tilesY,
              hdrqFloatBits(float(double(l.tilesX)/srcX)),
              hdrqFloatBits(float(double(l.tilesY)/srcY))},
             l.tilesX*16u,l.tilesY*16u);
        auto tiles=[&](uint32_t outBinding,const char* output) {
            return std::vector<BoundResource>{
                hdrqStorageImage(scratch,0,ca.c_str()),hdrqStorageImage(scratch,1,cb.c_str()),
                hdrqStorageBuffer(scratch,2,outBinding==2?"hdrp_align_b":"hdrp_align_c"),
                hdrqStorageBuffer(scratch,3,output)};
        };
        const uint32_t ssd=n!=0u?1u:0u;
        // RAWR keeps bounded per-tile exposure-ratio correction in its
        // alignment estimator when a NORMAL's metadata gain differs from 1,
        // even though hdrp_prepare already normalizes the RAW signal once.
        // This is alignment-only (clamped +/-10%), never a second color or
        // frequency-domain brightness normalization.
        const uint32_t ratio=std::fabs(p.gainsToReference[stage.normalIndex]-1.f)>1e-3f?1u:0u;
        const std::vector<uint32_t> pc={l.width,l.height,l.tilesX,l.tilesY,
                                        downscale,tile,ssd,ratio};
        bind(align.correct,tiles(2,"hdrp_align_c"),pc,l.tilesX*64u,l.tilesY);
        bind(align.tileDiff,tiles(3,"hdrp_tile_cost"),pc,l.tilesX*256u,l.tilesY);
        bind(align.best,{hdrqStorageBuffer(scratch,0,"hdrp_tile_cost"),
                         hdrqStorageBuffer(scratch,1,"hdrp_align_c"),
                         hdrqStorageBuffer(scratch,2,"hdrp_align_a")},
             {l.tilesX,l.tilesY,downscale},l.tilesX*16u,l.tilesY*16u);
    };
    if(stage.step==HdrqStep::CompanionAlignCoarse) {
        for(size_t n=raw.pyramid.size();n-->1u;)makeLevel(n);
    }else{
        makeLevel(0u);
        // Pass-zero align-once: immutable slot excludes frozen reference.
        if(!p.geometry.passes[1].align) {
            const auto& l=raw.pyramid[0];
            const uint64_t bytes=uint64_t(l.tilesX)*l.tilesY*8u;
            const uint64_t stride=hdrqAlign256(bytes);
            const uint32_t slot=stage.normalIndex-(stage.normalIndex>p.referenceNormal?1u:0u);
            const uint64_t offset=hdrqCheckedMul(stride,slot);
            const auto src=scratch.buffer("hdrp_align_a"), dst=scratch.buffer("hdrq_align_store");
            if(!bytes || bytes>src.size ||offset>dst.size ||bytes>dst.size-offset ||
               !src.buffer || !dst.buffer)
                throw std::invalid_argument("26864 align-once transfer slot outside scratch owner");
            HdrqKernelInvocation copy{};copy.kind=HdrqRecordedKind::CopyAlignmentSlot;
            copy.ownership=stage;copy.transferSrc=src.buffer;copy.transferDst=dst.buffer;
            copy.transferDstOffset=offset;copy.transferBytes=bytes;
            out.push_back(copy);
        }
    }
    return out;
}
} // namespace iris26864
