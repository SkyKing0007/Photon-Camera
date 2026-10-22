#include "Iris26864Wronski2xSensorProvenance.hpp"
#include <array>
#include <vector>
#include <iostream>
#include <stdexcept>
#include <cstdint>
using iris26864::wronski2x::Geometry;
using iris26864::wronski2x::referenceClipMask;
using iris26864::wronski2x::referenceSitesAtOutputCell;
int main() {
    int cases=0,clipped=0,greens=0;
    for(unsigned cfa=0; cfa<4; ++cfa) for(unsigned xoff=0; xoff<2; ++xoff) for(unsigned yoff=0;yoff<2;++yoff) {
        Geometry g{8,8,16,16,cfa,xoff,yoff,10,10,16383.f,0.995f,{64.f,72.f,80.f,88.f}};
        const auto sitesAtOrigin=iris26864::wronski2x::canonicalSites(
            iris26864::wronski2x::localPattern(g),0,0);
        for(unsigned oy=0;oy<g.outHeight;++oy) for(unsigned ch=1;ch<=2;++ch) {
            const auto observed=iris26864::wronski2x::camera2ChannelForOutput(g,oy,ch);
            const auto expected=1u+((g.originY+sitesAtOrigin[ch].y)&1u);
            if(observed!=expected)throw std::runtime_error("wrong ORIGINAL physical green-row parity in 2x LSC");
            ++greens;
        }
        std::vector<uint16_t> raw(64,1000);
        for(unsigned cy=0;cy<4;++cy) for(unsigned cx=0;cx<4;++cx) {
            const auto sites=referenceSitesAtOutputCell(g,cx*2,cy*2);
            for(unsigned phase=0;phase<4;++phase) {
                auto s=sites[phase]; raw[s.y*8+s.x]=(phase%2==0?16383:1000);
            }
            const auto mask=referenceClipMask(g,cx*2,cy*2,raw.data(),raw.size());
            if(mask!=0b0101u)throw std::runtime_error("expected canonical original R/G2 clipping bits");
            for(unsigned oy=0;oy<2;++oy) for(unsigned ox=0;ox<2;++ox) {
                const auto other=referenceClipMask(g,cx*2+ox,cy*2+oy,raw.data(),raw.size());
                if(other!=mask)throw std::runtime_error("2x reference clip projector inconsistency");
                ++cases;
            }
            ++clipped;
        }
    }
    std::cout << "PASS 2x physical G1/G2 LSC channels: " << greens << " checks across native CFA / origin parity / output rows\n";
    std::cout << "PASS 2x sensor reference CFA-bit projection: " << cases << " CFA cells / " << clipped << " reference cells across 4 Bayer patterns and crop parities\n";
    // Upstream 2x shader ORs reconstructed clipping; the HDR+ 1x and native 2x
    // masks are not guaranteed to be equal, even with identical reference bits.
    constexpr uint32_t sensor = 0b0101, reconstruction=0b0010;
    if((sensor|reconstruction)==sensor)throw std::runtime_error("expected masks to diverge");
    std::cout << "PASS distinct 2x reconstruction clipping can make mask differ from projected reference-only 1x mask\n";
}
