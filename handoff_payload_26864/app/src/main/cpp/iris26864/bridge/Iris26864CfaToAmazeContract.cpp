#include "Iris26864CfaToAmazeContract.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <limits>
namespace iris26864 {
namespace {
// Physical CFA layout indexed by (y&1)*2 + (x&1); green identifiers are
// *color-row identities*, never Camera2 LSC green-even/odd identifiers.
constexpr uint32_t phaseChannels[4][4]={{0,1,2,3},{1,0,3,2},{2,3,0,1},{3,2,1,0}};
void require(bool condition,const char* why){if(!condition)throw std::invalid_argument(why);}
float shadeAt(const CfaBridgeConfig& cfg,
              const std::vector<std::array<float,4>>& map,
              uint32_t x,uint32_t y,uint32_t logicalChannel){
    if(!cfg.lscWidth)return 1.f;
    // LSC is indexed by *absolute physical sensor row*, not CFA green label.
    uint32_t ch=(logicalChannel==1u||logicalChannel==2u)
                      ?1u+((cfg.originY+y)&1u):logicalChannel;
    const float fx=float(cfg.originX+x)*float(cfg.lscWidth-1u)/float(cfg.fullSensorWidth-1u);
    const float fy=float(cfg.originY+y)*float(cfg.lscHeight-1u)/float(cfg.fullSensorHeight-1u);
    const uint32_t x0=uint32_t(std::floor(fx)),y0=uint32_t(std::floor(fy));
    const uint32_t x1=std::min(x0+1u,cfg.lscWidth-1u),y1=std::min(y0+1u,cfg.lscHeight-1u);
    const float sx=fx-float(x0),sy=fy-float(y0);
    auto at=[&](uint32_t col,uint32_t row){
        return map[size_t(row)*cfg.lscWidth+col][ch];};
    const float top=at(x0,y0)*(1.f-sx)+at(x1,y0)*sx;
    const float bottom=at(x0,y1)*(1.f-sx)+at(x1,y1)*sx;
    const float out=top*(1.f-sy)+bottom*sy;
    require(std::isfinite(out)&&out>0.f&&out<64.f,"26864 invalid sensor LSC gain");
    return out;
}
}
uint32_t patternAtCrop(uint32_t physicalPattern,uint32_t ox,uint32_t oy){
    require(physicalPattern<4,"26864 invalid physical Bayer pattern");
    std::array<uint32_t,4> shifted{};
    for(uint32_t y=0;y<2;++y)for(uint32_t x=0;x<2;++x)
       shifted[y*2u+x]=phaseChannels[physicalPattern][((y+oy)&1u)*2u+((x+ox)&1u)];
    for(uint32_t pattern=0;pattern<4;++pattern){
        bool same=true;
        for(uint32_t i=0;i<4;++i)same &= shifted[i]==phaseChannels[pattern][i];
        if(same)return pattern;
    }
    throw std::logic_error("26864 impossible effective Bayer phase");
}
std::array<CfaSite,4> canonicalSites(uint32_t pattern,uint32_t cellX,uint32_t cellY){
    require(pattern<4u,"26864 invalid local Bayer pattern");
    require(cellX<=UINT32_MAX/2u&&cellY<=UINT32_MAX/2u,
            "26864 CFA site coordinate overflow");
    std::array<CfaSite,4> sites{};
    for(uint32_t dy=0;dy<2;++dy)for(uint32_t dx=0;dx<2;++dx){
        const uint32_t channel=phaseChannels[pattern][dy*2u+dx];
        sites[channel]={cellX*2u+dx,cellY*2u+dy};
    }
    return sites;
}
std::vector<CanonicalCell> packCfaToAmazeReference(
    const CfaBridgeConfig& cfg,const std::vector<float>& mergedCfa,
    const std::vector<uint16_t>& referenceRaw,
    const std::vector<std::array<float,4>>& map){
    require(cfg.width>=32u&&cfg.height>=32u&&!(cfg.width&1u)&&!(cfg.height&1u)&&
            cfg.width<=16384u&&cfg.height<=16384u&&cfg.pattern<4u,
            "26864 invalid canonical CFA extent/phase");
    require(cfg.fullSensorWidth>=cfg.width&&cfg.fullSensorHeight>=cfg.height&&
            cfg.originX<=cfg.fullSensorWidth-cfg.width&&
            cfg.originY<=cfg.fullSensorHeight-cfg.height,
            "26864 RAW crop exceeds sensor extent");
    const size_t count=size_t(cfg.width)*cfg.height;
    require(mergedCfa.size()==count&&referenceRaw.size()==count,
            "26864 canonical handoff requires exact immutable RAW reference");
    require((cfg.lscWidth==0u)==(cfg.lscHeight==0u),
            "26864 half-present LSC forbidden");
    if(cfg.lscWidth){
        require(cfg.lscWidth>=2u&&cfg.lscHeight>=2u&&
                map.size()==size_t(cfg.lscWidth)*cfg.lscHeight&&
                cfg.fullSensorWidth>1u&&cfg.fullSensorHeight>1u,
                "26864 invalid LSC map geometry");
        for(const auto& g:map)for(float v:g)
            require(std::isfinite(v)&&v>0.f&&v<64.f,
                    "26864 invalid LSC map data");
    }else require(map.empty(),"26864 stale LSC data with absent LSC map");
    require(std::isfinite(cfg.clippingThreshold)&&cfg.clippingThreshold>0.f&&
            cfg.clippingThreshold<=1.f,"26864 invalid clip threshold");
    for(uint32_t i=0;i<4;++i){
        require(std::isfinite(cfg.blackPhase[i])&&cfg.blackPhase[i]>=0.f&&
                std::isfinite(cfg.inverseRangePhase[i])&&cfg.inverseRangePhase[i]>0.f,
                "26864 invalid phase sensor normalization");
    }
    std::vector<CanonicalCell> out(count/4u);
    for(uint32_t y=0;y<cfg.height/2u;++y)for(uint32_t x=0;x<cfg.width/2u;++x){
        auto& cell=out[size_t(y)*(cfg.width/2u)+x];
        const auto sites=canonicalSites(cfg.pattern,x,y);
        for(uint32_t ch=0;ch<4;++ch){
            const auto site=sites[ch];
            const size_t pos=size_t(site.y)*cfg.width+site.x;
            const float raw=mergedCfa[pos];
            // Zero invalid merged pixels but mark their highlight/validity bit;
            // never turn NaN into an arbitrary green/pink image.
            const bool invalid=!std::isfinite(raw);
            const float normalized=invalid?0.f:std::clamp(raw,0.f,1.f);
            const uint32_t phase=(site.y&1u)*2u+(site.x&1u);
            const float sensor=(float(referenceRaw[pos])-cfg.blackPhase[phase])*cfg.inverseRangePhase[phase];
            if(invalid||raw>=cfg.clippingThreshold||sensor>=cfg.clippingThreshold)
                cell.sensorClipMask|=uint16_t(1u<<ch);
            const float lsc=shadeAt(cfg,map,site.x,site.y,ch);
            const float color=normalized*lsc;
            require(std::isfinite(color)&&color<=65504.f,"26864 packed CFA half-float overflow");
            cell.rgba[ch]=color;
        }
    }
    return out;
}
}
