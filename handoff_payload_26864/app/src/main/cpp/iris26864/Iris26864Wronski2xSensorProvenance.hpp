#pragma once
// IRIS_26864_WRONSKI_2X_SENSOR_PROVENANCE_DEV_ONLY
// Source-lock baseline: RAWR ce767e80... prepare_packed_cfa.comp,
// Git blob 796346b30229c01cd04a4c55f7df95e565dec410.
// Numeric oracle for the NEW Iris-only 2x sensor provenance/physical LSC
// corrections. Never treat synthesized Wronski RGB as sensor RAW data.
#include <array>
#include <cstdint>
#include <cmath>
#include <limits>
#include <stdexcept>
namespace iris26864::wronski2x {
struct Geometry final {
    uint32_t refWidth,refHeight,outWidth,outHeight;
    uint32_t nativeCfa,originX,originY,fullSensorWidth,fullSensorHeight;
    float whiteLevel,clipThreshold;
    // Camera2 black offsets in uncropped physical 2x2 row-major sensor order.
    std::array<float,4> sensorBlack;
};
struct Sample final {uint32_t x,y;};
using Sites=std::array<Sample,4>; // canonical R,G1,G2,B
inline void validate(const Geometry& g) {
    if(g.refWidth<2||g.refHeight<2||g.refWidth%2||g.refHeight%2||
       uint64_t(g.refWidth)*2!=g.outWidth||uint64_t(g.refHeight)*2!=g.outHeight||
       g.nativeCfa>=4 || g.fullSensorWidth<g.refWidth || g.fullSensorHeight<g.refHeight ||
       g.originX>g.fullSensorWidth-g.refWidth || g.originY>g.fullSensorHeight-g.refHeight ||
       g.fullSensorWidth<2||g.fullSensorHeight<2 ||
       !std::isfinite(g.whiteLevel)||g.whiteLevel<=0 ||
       !std::isfinite(g.clipThreshold)||g.clipThreshold<=0||g.clipThreshold>1)
        throw std::invalid_argument("26864 Wronski must be true 2x with native physical RAW provenance");
    for (float black:g.sensorBlack)
        if(!std::isfinite(black)||black<0||black>=g.whiteLevel)
            throw std::invalid_argument("26864 invalid physical black/white level");
}
inline uint32_t localPattern(const Geometry& g) {
    validate(g);
    return g.nativeCfa ^ (g.originX&1u) ^ ((g.originY&1u)<<1u);
}
inline Sites canonicalSites(uint32_t cfa,uint32_t cx,uint32_t cy){
    if(cfa>3 || cx>UINT32_MAX/2||cy>UINT32_MAX/2) throw std::invalid_argument("invalid Bayer site");
    constexpr uint32_t ch[4][4]={{0,1,2,3},{1,0,3,2},{2,3,0,1},{3,2,1,0}};
    Sites out{};
    for(uint32_t y=0;y<2;++y)for(uint32_t x=0;x<2;++x)
        out[ch[cfa][y*2+x]]={cx*2+x,cy*2+y};
    return out;
}
inline std::array<float,4> croppedBlackPhases(const Geometry& g){
    const uint32_t parity=(g.originX&1u)|((g.originY&1u)<<1u);
    return {g.sensorBlack[parity],g.sensorBlack[parity^1u],
            g.sensorBlack[parity^2u],g.sensorBlack[parity^3u]};
}
inline std::array<float,4> canonicalBlack(const Geometry& g){
    auto phase=croppedBlackPhases(g);
    const auto s=canonicalSites(localPattern(g),0,0);
    std::array<float,4> out{};
    for(size_t i=0;i<4;++i)out[i]=phase[((s[i].y&1u)<<1u)|(s[i].x&1u)];
    return out;
}
inline std::array<float,4> canonicalInverseRange(const Geometry& g){
    auto black=canonicalBlack(g);
    for(float& v:black)v=1.f/(g.whiteLevel-v);
    return black;
}
inline Sites referenceSitesAtOutputCell(const Geometry& g,uint32_t outCellX,uint32_t outCellY){
    const uint32_t ow=g.outWidth/2, oh=g.outHeight/2;
    if(outCellX>=ow||outCellY>=oh) throw std::out_of_range("2x output CFA cell");
    // Every 2x2 group of OUTPUT CFA cells inherits reference clip evidence
    // from ONE native reference RAW CFA cell, never RGB channel saturation.
    return canonicalSites(localPattern(g),outCellX/2,outCellY/2);
}
inline uint16_t referenceClipMask(const Geometry& g,uint32_t outCellX,uint32_t outCellY,
                                 const uint16_t* nativeRaw,size_t rawCount){
    validate(g);
    if(!nativeRaw||rawCount!=size_t(g.refWidth)*g.refHeight)
        throw std::invalid_argument("missing native RAW16 reference sensor evidence");
    const auto sites=referenceSitesAtOutputCell(g,outCellX,outCellY);
    const auto black=canonicalBlack(g);
    const auto inv=canonicalInverseRange(g);
    uint16_t mask=0;
    for(size_t ch=0;ch<4;++ch){
        const auto p=sites[ch];
        if(p.x>=g.refWidth||p.y>=g.refHeight)throw std::logic_error("source CFA out of bounds");
        float n=(float(nativeRaw[size_t(p.y)*g.refWidth+p.x])-black[ch])*inv[ch];
        if(n>=g.clipThreshold)mask|=uint16_t(1u<<ch);
    }
    return mask;
}
inline uint32_t physicalSensorRowForOutput(const Geometry& g,uint32_t outputY){
    if(outputY>=g.outHeight)throw std::out_of_range("output pixel Y");
    return g.originY+outputY/2u;
}
inline uint32_t camera2ChannelForOutput(const Geometry& g,uint32_t outputY,uint32_t canonical){
    if(outputY>=g.outHeight)throw std::out_of_range("2x output Y for physical lens shading");
    if(canonical>=4)throw std::invalid_argument("CFA channel");
    // G1/G2 are the two original physical sensor green ROWS, not the
    // synthetic doubled-output row. The Camera2 shading map is indexed by
    // physical row parity of the respective source Bayer site.
    if(canonical!=1u && canonical!=2u) return canonical;
    const uint32_t local=localPattern(g);
    const uint32_t siteRow=(canonical==1u) ? uint32_t(local>=2u) : uint32_t(local<2u);
    return 1u+((g.originY+siteRow)&1u);
}
}  // namespace iris26864::wronski2x
