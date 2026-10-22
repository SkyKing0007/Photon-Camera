#pragma once
// IRIS_26864_HDRQ_PINNED_RESOURCE_LAYOUT_PROOF_ONLY_NOT_RUNTIME
// Reproduces named resources and formats in pinned RAWR
// native/multiframe/pipeline/src/HdrPlusRecorder.cpp
// commit ce767e80bfce2e1641abf7dad6b1bf504d844fd9,
// makeHdrPlusFrequencyScratchLayout(). No GL / foreign queue ownership here.
#include "../Iris26864BMergePlan.hpp"
#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <vulkan/vulkan.h>

namespace iris26864 {
enum class HdrqLifetime { Burst, Companion, PyramidTemp, Output };
struct HdrqAlignmentLevel {
    uint32_t width=0,height=0,tilesX=0,tilesY=0;
};
struct HdrqScratchImage {
    std::string name;
    uint32_t width=0,height=0;
    VkFormat format=VK_FORMAT_UNDEFINED;
    HdrqLifetime lifetime=HdrqLifetime::Companion;
};
struct HdrqScratchBuffer {
    std::string name;
    VkDeviceSize bytes=0;
    HdrqLifetime lifetime=HdrqLifetime::Companion;
};
struct HdrqScratchLayout {
    std::vector<HdrqScratchImage> images;
    std::vector<HdrqScratchBuffer> buffers;
    uint64_t logicalBytes=0; // no aliasing assumption; allocation overhead is not included
};

inline uint64_t hdrqCheckedAdd(uint64_t a,uint64_t b) {
    if(b>UINT64_MAX-a)throw std::invalid_argument("26864 HDRq scratch logical byte overflow");
    return a+b;
}
inline uint64_t hdrqCheckedMul(uint64_t a,uint64_t b) {
    if(b && a>UINT64_MAX/b)throw std::invalid_argument("26864 HDRq scratch extent overflow");
    return a*b;
}
inline uint64_t hdrqAlign256(uint64_t v) {
    if(v>UINT64_MAX-255u)throw std::invalid_argument("26864 HDRq 256-byte alignment overflow");
    return ((v+255u)/256u)*256u;
}
inline HdrqScratchLayout makeHdrqScratchLayout(const Plan& p,
                                const std::vector<HdrqAlignmentLevel>& levels) {
    const auto& g=p.geometry;
    if(p.path!=Path::HdrPlusFrequency || p.noiseOwner!=NoiseOwner::HdrqReferenceTileRms ||
       !p.createBResources || !p.lscBeforeAmaze || p.lscAfterAmaze ||
       !g.inputWidth || !g.inputHeight || !g.paddedWidth || !g.paddedHeight ||
       !g.rgbaWidth || !g.rgbaHeight || g.rgbaWidth%8u || g.rgbaHeight%8u ||
       g.tilesX!=g.rgbaWidth/8u || g.tilesY!=g.rgbaHeight/8u ||
       g.outputWidth!=g.inputWidth || g.outputHeight!=g.inputHeight ||
       levels.empty() || levels.size()>32u)
       throw std::invalid_argument("26864 B HDRq invalid path or alignment-level geometry");
    HdrqScratchLayout out;
    auto image=[&](const std::string& name,uint32_t w,uint32_t h,VkFormat fmt,
                   uint32_t bpp,HdrqLifetime life) {
        if(!w||!h||w>32768u||h>32768u)throw std::invalid_argument("26864 HDRq image extent invalid");
        out.logicalBytes=hdrqCheckedAdd(out.logicalBytes,hdrqCheckedMul(hdrqCheckedMul(w,h),bpp));
        out.images.push_back({name,w,h,fmt,life});
    };
    auto buffer=[&](const std::string& name,uint64_t bytes) {
        if(!bytes || bytes>(UINT64_C(1)<<38))
            throw std::invalid_argument("26864 HDRq buffer size invalid");
        out.logicalBytes=hdrqCheckedAdd(out.logicalBytes,bytes);
        out.buffers.push_back({name,bytes,HdrqLifetime::Companion});
    };
    const uint32_t w=g.inputWidth,h=g.inputHeight;
    image("hdrp_ref_padded",g.paddedWidth,g.paddedHeight,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Burst);
    image("hdrp_comp_padded",g.paddedWidth,g.paddedHeight,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Companion);
    image("hdrp_pyr_tmp_a",levels[0].width,levels[0].height,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::PyramidTemp);
    image("hdrp_pyr_tmp_b",levels[0].width,levels[0].height,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::PyramidTemp);
    uint64_t maxTiles=1;
    for(size_t i=0;i<levels.size();++i) {
        const auto& l=levels[i];
        if(!l.width||!l.height||!l.tilesX||!l.tilesY ||
           l.width>g.paddedWidth||l.height>g.paddedHeight ||
           (i && (l.width>levels[i-1].width||l.height>levels[i-1].height)))
            throw std::invalid_argument("26864 HDRq alignment pyramid invalid");
        image("hdrp_ref_l"+std::to_string(i),l.width,l.height,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Burst);
        image("hdrp_comp_l"+std::to_string(i),l.width,l.height,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Companion);
        maxTiles=std::max(maxTiles,hdrqCheckedMul(l.tilesX,l.tilesY));
    }
    const uint32_t rw=g.rgbaWidth,rh=g.rgbaHeight;
    // RAWR frequency bins: two RGBA32F texels per Fourier-bin pixel.
    const uint64_t specWidth=hdrqCheckedMul(2,rw);
    if(specWidth>UINT32_MAX)throw std::invalid_argument("26864 HDRq spectrum extent overflow");
    image("hdrq_ref_rgba",rw,rh,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Burst);
    image("hdrq_aligned_rgba",rw,rh,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Companion);
    image("hdrq_out_rgba",rw,rh,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Output);
    image("hdrq_ref_ft",uint32_t(specWidth),rh,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Burst);
    image("hdrq_aligned_ft",uint32_t(specWidth),rh,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Companion);
    image("hdrq_final_ft",uint32_t(specWidth),rh,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Output);
    image("hdrq_rms",g.tilesX,g.tilesY,VK_FORMAT_R32G32B32A32_SFLOAT,16,HdrqLifetime::Burst);
    image("hdrq_mismatch",g.tilesX,g.tilesY,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Companion);
    image("hdrq_total_mismatch",g.tilesX,g.tilesY,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Output);
    image("hdrq_highlights",g.tilesX,g.tilesY,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Companion);
    // Even uniform mode shader's binding 7 requires a typed dummy/allocated image.
    image("hdrq_weight_sum",rw,rh,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Output);
    image("hdrp_accum",w,h,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Output);
    image("hdrp_output",w,h,VK_FORMAT_R16G16B16A16_SFLOAT,8,HdrqLifetime::Output);
    image("hdrp_cfa",w,h,VK_FORMAT_R32_SFLOAT,4,HdrqLifetime::Output);
    buffer("hdrp_align_a",hdrqCheckedMul(maxTiles,8));
    buffer("hdrp_align_b",hdrqCheckedMul(maxTiles,8));
    buffer("hdrp_align_c",hdrqCheckedMul(maxTiles,8));
    buffer("hdrp_tile_cost",hdrqCheckedMul(maxTiles,100));
    buffer("hdrq_mean",16);
    buffer("hdrq_shift_table",49ull*64ull*8ull);
    // Match pinned RAWR 64-frame upper bound, including per-slot 256B alignment.
    buffer("hdrq_align_store",hdrqCheckedMul(64u,
        hdrqAlign256(hdrqCheckedMul(hdrqCheckedMul(levels[0].tilesX,levels[0].tilesY),8u))));
    return out;
}
} // namespace iris26864
