#pragma once
// IRIS_26864_HDRQ_FREQUENCY_STAGE_BINDINGS_PARTIAL_NOT_RUNTIME
// Source-specific descriptors and push constants for pinned RAWR HDR+ Higher
// quality *frequency* kernels at ce767e80bfce2e1641abf7dad6b1bf504d844fd9.
// No SPIR-V loading or queue/GL ownership is implemented here. No synthetic
// alignment kernels, clearing substitutes, Wronski, or fallback are provided.
#include "Iris26864HdrqPinnedStageBindings.hpp"
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

namespace iris26864 {
struct HdrqFrequencyKernels {
    HdrqPinnedKernels original{};
    VulkanKernelExecutor *shiftTable=nullptr, *toRgba=nullptr, *seedDft=nullptr,
        *warpRgba=nullptr, *forwardDft=nullptr, *regionMean=nullptr,
        *mismatchNorm=nullptr, *highlightsNorm=nullptr, *deconvolute=nullptr,
        *backwardDft=nullptr, *border=nullptr, *accumulate=nullptr,
        *finalize=nullptr;
};
struct HdrqFrequencyInputs {
    // Reference phase order: (y&1)*2+(x&1), BEFORE lens shading or WB.
    std::array<float,4> referenceBlack{};
    float referenceWhite=0.0f;
    // One white level for each entry of Plan.normals (not the raw-burst index).
    std::vector<float> normalWhite;
    uint32_t level0TilesX=0, level0TilesY=0, level0HalfTileSize=0;
    uint32_t normalFrameCount=0;
    // Aligned shift storage uses 256-byte padded slots, if align-once.
    bool alignOnce=true;
};
inline void validateHdrqFrequencyInputs(const Plan& p, const HdrqFrequencyInputs& m) {
    if(p.path!=Path::HdrPlusFrequency||!p.createBResources||p.normals.size()<2 ||
       p.referenceNormal>=p.normals.size()||m.normalFrameCount!=p.normals.size()||
       m.normalWhite.size()!=p.normals.size() || !std::isfinite(m.referenceWhite)||
       m.referenceWhite<=0 || !m.level0TilesX||!m.level0TilesY||!m.level0HalfTileSize ||
       (m.alignOnce!=(!p.geometry.passes[1].align)))
        throw std::invalid_argument("26864 frequency metadata/schedule mismatch");
    for(float b:m.referenceBlack)
        if(!std::isfinite(b)||b<0||b>=m.referenceWhite)
            throw std::invalid_argument("26864 invalid native-phase black metadata");
    if(m.normalWhite[p.referenceNormal]!=m.referenceWhite)
        throw std::invalid_argument("26864 reference white-level conflict");
    for(float w:m.normalWhite)
        if(!std::isfinite(w)||w<=0)
            throw std::invalid_argument("26864 missing NORMAL white level");
    // Alignment tile count must be compatible with a slot in the pinned
    // RAWR resource layout. The exact pyramid geometry is validated upstream.
    if(uint64_t(m.level0TilesX)*m.level0TilesY>UINT32_MAX/8u)
        throw std::invalid_argument("26864 alignment store slot overflow");
}
inline HdrqKernelInvocation bindPinnedHdrqFrequencyStage(
    const Plan& p,const HdrqDispatch& s,const VulkanHdrqScratchOwner& scratch,
    const HdrqFrequencyKernels& k,const HdrqFrequencyNorms& norms,
    const HdrqFrequencyInputs& m) {
    // Validate before any descriptor allocations or VkCmd* recording.
    validateHdrqFrequencyInputs(p,m);
    if(s.pass>4u || (s.pass==4u && s.step!=HdrqStep::FinalizeCfa) ||
       (s.pass<4u && s.step==HdrqStep::FinalizeCfa) ||
       (s.pass<4u && p.geometry.passes[s.pass].index!=s.pass))
        throw std::invalid_argument("26864 HDRq frequency stage invalid pass");
    if(s.step==HdrqStep::ClearTileMismatch){
        if(s.pass>=4u||s.normalIndex!=UINT32_MAX)
            throw std::invalid_argument("26864 HDRq mismatch clear ownership invalid");
        HdrqKernelInvocation out{};
        out.ownership=s;
        out.kind=HdrqRecordedKind::ClearTileMismatch;
        out.clearImage=scratch.image("hdrq_total_mismatch").image;
        if(out.clearImage==VK_NULL_HANDLE)
            throw std::invalid_argument("26864 HDRq total mismatch image not allocated");
        return out;
    }
    if(s.step==HdrqStep::ReferenceTileRms || s.step==HdrqStep::CompanionTileMismatch ||
       s.step==HdrqStep::CompanionWienerMerge) {
        auto original=bindPinnedHdrqStage(p,s,scratch,k.original,norms);
        if(s.step==HdrqStep::CompanionTileMismatch){
            // This exact dispatch selects the UNIFORM frequency route. Its
            // padded RAW samples were already scaled to reference exposure;
            // bracketed exposure correction is not applied a second time.
            original.pushWords[4]=hdrqFloatBits(1.0f);
        }
        return original;
    }
    HdrqKernelInvocation j{};j.ownership=s;
    const auto& g=p.geometry;
    const auto tilePixels=[&](uint32_t local) {
        if(g.tilesX>UINT32_MAX/local||g.tilesY>UINT32_MAX/local)
            throw std::invalid_argument("26864 HDRq grid overflow");
        j.width=g.tilesX*local;j.height=g.tilesY*local;
    };
    const auto rawPixels=[&]() {j.width=g.inputWidth;j.height=g.inputHeight;};
    const auto rgbaPixels=[&]() {j.width=g.rgbaWidth;j.height=g.rgbaHeight;};
    const auto require=[&](VulkanKernelExecutor* kernel) {
        if(!kernel)throw std::invalid_argument("26864 pinned frequency SPIR-V pipeline absent");
        j.kernel=kernel;
    };
    const auto ensureCompanion=[&]() {
        if(s.normalIndex==UINT32_MAX||s.normalIndex>=p.normals.size()||
           s.normalIndex==p.referenceNormal||s.pass>=4u)
            throw std::invalid_argument("26864 HDRq companion owner mismatch");
    };
    const auto ensurePass=[&]() {
        if(s.normalIndex!=UINT32_MAX||s.pass>=4u)
            throw std::invalid_argument("26864 HDRq pass-only owner mismatch");
    };
    const auto passOffset=[&]() -> const Pass& {return g.passes[s.pass];};
    const auto asWord=[](int32_t x)->uint32_t {
        uint32_t word=0;std::memcpy(&word,&x,sizeof(word));return word;
    };
    const uint32_t tx=g.tilesX,ty=g.tilesY;
    switch(s.step) {
        case HdrqStep::ShiftTable:
            ensurePass();if(s.pass!=0u)throw std::invalid_argument("26864 shift table must initialize pass zero");
            require(k.shiftTable);j.resources={hdrqStorageBuffer(scratch,0,"hdrq_shift_table")};
            j.width=49u*64u;j.height=1u;break;
        case HdrqStep::ReferenceRgba: {
            ensurePass();require(k.toRgba);rgbaPixels();
            const auto& pp=passOffset();
            j.resources={hdrqStorageImage(scratch,0,"hdrp_ref_padded"),hdrqStorageImage(scratch,1,"hdrq_ref_rgba")};
            j.pushWords={g.rgbaWidth,g.rgbaHeight,g.cropX,g.cropY,asWord(pp.passOffsetX),asWord(pp.passOffsetY),
                         g.paddedWidth,g.paddedHeight};break;
        }
        case HdrqStep::ReferenceSeedDft:
            ensurePass();require(k.seedDft);tilePixels(8u);
            j.resources={hdrqStorageImage(scratch,0,"hdrq_ref_rgba"),hdrqStorageImage(scratch,1,"hdrq_ref_ft"),
                         hdrqStorageImage(scratch,2,"hdrq_final_ft")};
            j.pushWords={tx,ty};break;
        case HdrqStep::CompanionWarpRgba: {
            ensureCompanion();require(k.warpRgba);rgbaPixels();
            auto align=hdrqStorageBuffer(scratch,2,m.alignOnce?"hdrq_align_store":"hdrp_align_a");
            const uint64_t bytes=uint64_t(m.level0TilesX)*m.level0TilesY*8u;
            if(m.alignOnce){
                // RAWR companion slots are contiguous and EXCLUDE the frozen
                // reference. Plan.normalIndex includes that reference.
                const uint32_t slot=s.normalIndex-(s.normalIndex>p.referenceNormal?1u:0u);
                const uint64_t stride=hdrqAlign256(bytes), offset=stride*slot;
                if(offset>align.bufferRange||bytes>align.bufferRange-offset)
                    throw std::invalid_argument("26864 align-once per-frame SSBO slot out of range");
                align.bufferOffset=offset;align.bufferRange=bytes;
            }else if(bytes>align.bufferRange)
                throw std::invalid_argument("26864 alignment SSBO undersized");
            // RAWR uniform frequency uses exposure-normalized padded samples,
            // NOT bracketed substitution or HDR+ weight normalization.
            // Companion exposure factor must equal 1 in this uniform mode.
            const auto& pp=passOffset();
            j.resources={hdrqStorageImage(scratch,0,"hdrp_comp_padded"),hdrqStorageImage(scratch,1,"hdrq_aligned_rgba"),
                         align,hdrqStorageImage(scratch,3,"hdrq_ref_rgba")};
            j.pushWords={g.rgbaWidth,g.rgbaHeight,g.cropX,g.cropY,g.paddedWidth,g.paddedHeight,
                         m.level0TilesX,m.level0TilesY,m.level0HalfTileSize,0u,
                         asWord(pp.passOffsetX),asWord(pp.passOffsetY),m.alignOnce?1u:0u,
                         hdrqFloatBits(1.0f),hdrqFloatBits(m.normalWhite[s.normalIndex]),
                         hdrqFloatBits(0.25f*(m.referenceBlack[0]+m.referenceBlack[1]+m.referenceBlack[2]+m.referenceBlack[3])),0u};
            break;
        }
        case HdrqStep::CompanionForwardDft:
            ensureCompanion();require(k.forwardDft);tilePixels(8u);
            j.resources={hdrqStorageImage(scratch,0,"hdrq_aligned_rgba"),hdrqStorageImage(scratch,1,"hdrq_aligned_ft")};
            j.pushWords={tx,ty};break;
        case HdrqStep::CompanionRegionMean: {
            ensureCompanion();require(k.regionMean);
            // RAWR excludes the boundary tile introduced by each shift.
            const uint32_t left=(s.pass&1u)?1u:0u,right=left?0u:1u;
            const uint32_t top=s.pass<2u?1u:0u,bottom=top?0u:1u;
            if(tx<=left+right || ty<=top+bottom)
                throw std::invalid_argument("26864 frequency tiles too small for region mean");
            j.width=256u;j.height=1u;
            j.resources={hdrqStorageImage(scratch,0,"hdrq_mismatch"),hdrqStorageBuffer(scratch,1,"hdrq_mean")};
            j.pushWords={left,top,tx-left-right,ty-top-bottom};break;
        }
        case HdrqStep::CompanionMismatchNorm:
            ensureCompanion();require(k.mismatchNorm);tilePixels(16u);
            j.resources={hdrqStorageImage(scratch,0,"hdrq_mismatch"),
                         hdrqStorageImage(scratch,1,"hdrq_total_mismatch"),hdrqStorageBuffer(scratch,2,"hdrq_mean")};
            j.pushWords={tx,ty,hdrqFloatBits(1.0f/float(m.normalFrameCount))};break;
        case HdrqStep::CompanionHighlightsNorm:
            ensureCompanion();require(k.highlightsNorm);tilePixels(16u);
            j.resources={hdrqStorageImage(scratch,0,"hdrq_aligned_rgba"),hdrqStorageImage(scratch,1,"hdrq_highlights")};
            // In the pinned uniform RAWR path there is no brighter-frame
            // substitution: highlights factor is 1, although this kernel still
            // executes as part of the source frequency merge ordering.
            j.pushWords={tx,ty,hdrqFloatBits(1.0f),hdrqFloatBits(m.normalWhite[s.normalIndex]),
                         hdrqFloatBits(0.25f*(m.referenceBlack[0]+m.referenceBlack[1]+m.referenceBlack[2]+m.referenceBlack[3]))};
            break;
        case HdrqStep::PassDeconvolute:
            ensurePass();require(k.deconvolute);tilePixels(8u);
            j.resources={hdrqStorageImage(scratch,0,"hdrq_final_ft"),hdrqStorageImage(scratch,1,"hdrq_total_mismatch")};
            j.pushWords={tx,ty};break;
        case HdrqStep::PassBackwardDft:
            ensurePass();require(k.backwardDft);tilePixels(8u);
            j.resources={hdrqStorageImage(scratch,0,"hdrq_final_ft"),hdrqStorageImage(scratch,1,"hdrq_out_rgba")};
            j.pushWords={tx,ty,hdrqFloatBits(float(m.normalFrameCount))};break;
        case HdrqStep::PassBorder:
            ensurePass();require(k.border);rgbaPixels();
            j.resources={hdrqStorageImage(scratch,0,"hdrq_out_rgba"),hdrqStorageImage(scratch,1,"hdrq_ref_rgba")};
            j.pushWords={g.rgbaWidth,g.rgbaHeight,hdrqFloatBits(-2.0f)};break;
        case HdrqStep::PassAccumulateCfa:
            ensurePass();require(k.accumulate);rawPixels();
            j.resources={hdrqStorageImage(scratch,0,"hdrq_out_rgba"),hdrqStorageImage(scratch,1,"hdrp_accum")};
            j.pushWords={g.inputWidth,g.inputHeight,asWord(passOffset().accumOffsetX),
                         asWord(passOffset().accumOffsetY),s.pass==0u?0u:1u};break;
        case HdrqStep::FinalizeCfa:
            if(s.normalIndex!=UINT32_MAX||s.pass!=4u)throw std::invalid_argument("26864 finalize stage invalid");
            require(k.finalize);rawPixels();
            j.resources={hdrqStorageImage(scratch,0,"hdrp_accum"),hdrqStorageImage(scratch,1,"hdrp_output"),
                         hdrqStorageImage(scratch,2,"hdrp_cfa")};
            for(float b:m.referenceBlack)j.pushWords.push_back(hdrqFloatBits(b));
            j.pushWords.insert(j.pushWords.end(),{hdrqFloatBits(m.referenceWhite),0u,g.inputWidth,g.inputHeight});
            break;
        default:
            // Alignment, padded RAW preparation and transfer-clears are
            // deliberately NOT a fake compute kernel or historical B path.
            throw std::invalid_argument("26864 native alignment/clear stage still missing: fail closed");
    }
    return j;
}
} // namespace iris26864
