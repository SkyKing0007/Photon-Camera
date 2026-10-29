#pragma once
// Development-only coarse global RAW-alignment seeds. The GPU must locally
// re-estimate and verify each TILE and then each PIXEL before counting even
// one sensor color measurement. These offsets are NOT color truth by themselves.
#include "Iris26887BOffRawPhaseDiversity.hpp"
#include <vector>
namespace iris26887 {
struct RawColorSeed {bool valid=false;int dx=0,dy=0;};
// A necessary, not sufficient, GPU allocation prerequisite. The accepted
// tile shift must equal its integer coarse seed (the local kernel rejects
// nonzero delta), so source color-site parity at each reference pixel is
// completely determined by these seeds. If no pixel parity can observe
// TWO physical R/G/B samples, allocating ~48 MiB of witness state cannot
// produce one valid pixel. This check NEVER authorizes a color correction:
// every GPU tile and pixel still has to prove independent alignment,
// clipping and repeated per-channel agreement.
inline bool canSupplyTwiceEachBayerColor(
        const std::vector<RawColorSeed>& seeds,std::uint32_t cfa){
    if(cfa>3u||seeds.size()<6u)return false;
    constexpr unsigned channels[4][4]={{0,1,1,2},{1,0,2,1},
                                       {1,2,0,1},{2,1,1,0}};
    for(int y=0;y<2;++y)for(int x=0;x<2;++x){
        unsigned count[3]={0u,0u,0u};
        for(const auto& seed:seeds){
            if(!seed.valid)continue;
            const unsigned ix=unsigned((x+seed.dx)&1);
            const unsigned iy=unsigned((y+seed.dy)&1);
            ++count[channels[cfa][ix+2u*iy]];
        }
        if(count[0]>=2u&&count[1]>=2u&&count[2]>=2u)return true;
    }
    return false;
}
inline std::vector<RawColorSeed> estimateOriginalRawSensorSeeds(
    const std::vector<Raw16Frame>& frames,std::size_t reference,uint32_t cfa){
    std::vector<RawColorSeed> seeds(frames.size());
    if(frames.size()<2||frames.size()>64||reference>=frames.size()||cfa>3)return seeds;
    const auto& ref=frames[reference];
    if(ref.width<128u||ref.height<128u||!(ref.exposure>0.f))return seeds;
    seeds[reference]={true,0,0};
    for(std::size_t i=0;i<frames.size();++i){
      if(i==reference)continue;
      const auto& f=frames[i];
      if(!f.bytes||f.width!=ref.width||f.height!=ref.height||
         !std::isfinite(f.exposure)||f.exposure<=0.f||
         std::abs(f.exposure/ref.exposure-1.f)>.025f)continue;
      auto global=detail::estimate(ref,f,cfa,int(ref.width),int(ref.height),4);
      if(!global.good)continue;
      unsigned agree=0;
      for(int j=0;j<4;++j){
         auto local=detail::estimate(ref,f,cfa,int(ref.width),int(ref.height),j);
         if(local.good&&std::hypot(local.dx-global.dx,local.dy-global.dy)<.28f)++agree;
      }
      if(agree<3)continue;
      // The original alignment search operates on 2x2 Bayer cells.
      // Convert to raw-site units, but the GPU must validate odd CFA shifts.
      seeds[i]={true,int(std::lround(2.f*global.dx)),
                     int(std::lround(2.f*global.dy))};
    }
    return seeds;
}
} // namespace iris26887
