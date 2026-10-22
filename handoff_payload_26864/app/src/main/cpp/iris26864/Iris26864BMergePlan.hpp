#pragma once
// IRIS_26864_B_NATIVE_DISPATCH_PLAN_PORT_INCOMPLETE
// IMPORTANT: This is a host-compiled, standalone integration contract, not yet
// linked into the Android capture path. The Vulkan GPU implementation is absent.
// RAWR geometric and exposure semantics derived from pinned RAWR commit:
// ce767e80bfce2e1641abf7dad6b1bf504d844fd9
// native/multiframe/merge_hdrplus/include/rawr/raw_merge_hdrplus_gpu/RawMergeHdrPlusGpu.h
// native/multiframe/pipeline/src/HdrPlusRecorder.cpp
// native/multiframe/pipeline/src/AndroidBurstCoordinator.cpp
// No change to proven Experiment A / UHDR / DNG implementations.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace iris26864 {
enum class Path { ExactA, HdrPlusFrequency, WronskiTrue2x };
enum class FrameRole { Normal, ShadowLong };
// B never imports A/Camera2 noise. RAWR frequency owns scene-tile RMS, whereas
// RAWR Wronski owns the per-CFA-site empirical RAW-burst noise fit.
enum class NoiseOwner { None, HdrqReferenceTileRms, WronskiRawBurstFit };
struct Request {
    bool bOnly = true;
    bool night = false;
    bool superRes = false;
    float localPhysicalLensZoom = 1.f;
    uint32_t rawWidth = 0, rawHeight = 0;
    uint32_t cfa = 0;
    uint32_t reference = 0;  // index in unfiltered shutter-frozen immutable burst
    float hdrqStrength = 13.f;
    uint32_t alignmentTileSize = 32;
    uint32_t searchDistance = 64;
    bool frequencyAlignOnce = true;
};
struct Frame {
    FrameRole role = FrameRole::Normal;
    uint32_t rawWidth = 0, rawHeight = 0;
    uint32_t cfa = 0;
    uint64_t physicalCameraIdentity = 0;  // source owner identifies physical lens
    uint64_t exposureNs = 0;
    uint32_t iso = 0;
    float white = 0;
    std::array<float, 4> black{};  // physical RAW CFA-site order
};
struct Pass {
    uint32_t index = 0;
    uint32_t padLeft = 0, padTop = 0;
    int32_t passOffsetX = 0, passOffsetY = 0;
    int32_t accumOffsetX = 0, accumOffsetY = 0;
    bool align = false;
    bool overwriteAccumulator = false;
};
struct Geometry {
    uint32_t inputWidth = 0, inputHeight = 0;
    uint32_t outputWidth = 0, outputHeight = 0;
    uint32_t paddedWidth = 0, paddedHeight = 0;
    uint32_t rgbaWidth = 0, rgbaHeight = 0;
    uint32_t tilesX = 0, tilesY = 0;
    uint32_t cropX = 0, cropY = 0;
    std::array<Pass, 4> passes{};
};
struct Plan {
    Path path = Path::ExactA;
    Geometry geometry{};
    std::vector<uint32_t> normals;  // preserve actual frozen frame indices
    std::vector<float> gainsToReference;  // refExposure / thisExposure
    uint32_t referenceNormal = 0;
    NoiseOwner noiseOwner = NoiseOwner::None;
    bool createBResources = false;
    bool lscBeforeAmaze = false;
    bool lscAfterAmaze = false;
    bool produceSyntheticCfaForAmaze = false;
    bool referenceClipNeeds2xRemap = false;
};
inline bool validPositive(float n) { return std::isfinite(n) && n > 0.f; }
inline uint32_t checkedMultiply(uint32_t x, uint32_t y) {
    if (!x || !y || x > std::numeric_limits<uint32_t>::max() / y)
        throw std::invalid_argument("26864 native output extent overflow");
    return x*y;
}
inline uint32_t checkedRoundUp(uint32_t a, uint32_t base) {
    if (!base || a > std::numeric_limits<uint32_t>::max()-(base-1u))
        throw std::invalid_argument("26864 padded geometry overflow");
    return (a+base-1u)/base*base;
}
inline Geometry makeFrequencyGeometry(uint32_t width, uint32_t height,
                                     uint32_t tileSize, uint32_t searchDistance,
                                     bool alignOnce) {
    // Exact translated RAWR alignment-pyramid and frequency-pad equations.
    // Four frequency passes, 8x8 RGBA tile == 16x16 original RAW pixels.
    if (width < 32u || height < 32u || (width&1u) || (height&1u) ||
        (tileSize!=16u && tileSize!=32u) ||
        (searchDistance!=32u && searchDistance!=64u && searchDistance!=128u))
        throw std::invalid_argument("26864 frequency geometry/config invalid");
    uint64_t factor=2;
    uint32_t lastTile=tileSize;
    uint32_t res=std::min(width,height)/2;
    uint32_t levels=1;
    while(res>searchDistance) {
        ++levels;
        lastTile=std::max(lastTile/2u,8u);
        factor*=2;
        res/=2;
        if(factor>UINT32_MAX) throw std::invalid_argument("26864 geometry factor overflow");
    }
    const uint64_t tileFactor=uint64_t(lastTile)*factor;
    if(tileFactor>UINT32_MAX || width>UINT32_MAX-8u || height>UINT32_MAX-8u)
        throw std::invalid_argument("26864 geometry oversize");
    const uint32_t pf=uint32_t(tileFactor);
    const uint32_t paddedW=checkedRoundUp(width+8u,pf);
    const uint32_t paddedH=checkedRoundUp(height+8u,pf);
    if(paddedW<width+8u || paddedH<height+8u)
        throw std::invalid_argument("26864 invalid frequency padding");
    const uint32_t px=(paddedW-width-8u)/2u;
    const uint32_t py=(paddedH-height-8u)/2u;
    if((px&1u)||(py&1u)||((paddedW-width-8u)&1u)||((paddedH-height-8u)&1u))
        throw std::invalid_argument("26864 frequency pad breaks Bayer phase");
    Geometry g{};
    g.inputWidth=width;g.inputHeight=height;
    g.outputWidth=width;g.outputHeight=height;
    g.paddedWidth=paddedW;g.paddedHeight=paddedH;
    g.cropX=px/16u*16u;g.cropY=py/16u*16u;
    g.rgbaWidth=(paddedW-2*g.cropX)/2u;
    g.rgbaHeight=(paddedH-2*g.cropY)/2u;
    g.tilesX=g.rgbaWidth/8u;g.tilesY=g.rgbaHeight/8u;
    if(!g.tilesX||!g.tilesY||g.rgbaWidth%8u||g.rgbaHeight%8u)
        throw std::invalid_argument("26864 fractional frequency tiles");
    for(uint32_t p=0;p<4;++p) {
        const bool left=(p&1u)!=0u, top=p<2u;
        auto& a=g.passes[p];
        a.index=p;
        a.padLeft=px+(left?8u:0u);
        a.padTop=py+(top?8u:0u);
        a.passOffsetX=alignOnce ? int32_t(px)-int32_t(a.padLeft) : 0;
        a.passOffsetY=alignOnce ? int32_t(py+8u)-int32_t(a.padTop) : 0;
        a.accumOffsetX=int32_t(a.padLeft)-int32_t(g.cropX);
        a.accumOffsetY=int32_t(a.padTop)-int32_t(g.cropY);
        a.align=!alignOnce||p==0;
        a.overwriteAccumulator=(p==0);
    }
    (void)levels;
    return g;
}
inline Path selectPath(const Request& req) {
    if(!req.bOnly||req.night)
        throw std::invalid_argument("26864 B GPU plan may not capture A, A+B or Night");
    if(!validPositive(req.localPhysicalLensZoom))
        throw std::invalid_argument("26864 invalid local physical lens zoom");
    // Super Res is an explicit B/Wronski selection; never dispatch A at 1.1x+.
    if(req.superRes) return Path::WronskiTrue2x;
    if(req.localPhysicalLensZoom>=1.10f) return Path::ExactA;
    return Path::HdrPlusFrequency;
}
inline Plan makePlan(const Request& req, const std::vector<Frame>& frames) {
    Plan out{};
    out.path=selectPath(req);
    // Full A path doesn't borrow B's metadata, noise/profile gate or geometry.
    if(out.path==Path::ExactA) return out;
    if(req.rawWidth<32u||req.rawHeight<32u||(req.rawWidth&1u)||
        (req.rawHeight&1u)||req.cfa>3u||req.reference>=frames.size())
        throw std::invalid_argument("26864 B raw geometry/reference invalid");
    const Frame& ref=frames[req.reference];
    if(ref.role!=FrameRole::Normal||!ref.physicalCameraIdentity)
        throw std::invalid_argument("26864 B reference must be physical NORMAL");
    if(!ref.exposureNs||!ref.iso)
        throw std::invalid_argument("26864 B missing reference exposure; no Camera2 fallback");
    for(const auto& f:frames) {
        if(f.role!=FrameRole::Normal)continue;
        if(f.rawWidth!=req.rawWidth||f.rawHeight!=req.rawHeight||f.cfa!=req.cfa||
            f.physicalCameraIdentity!=ref.physicalCameraIdentity||!f.exposureNs||!f.iso||
            !validPositive(f.white))
            throw std::invalid_argument("26864 NORMAL metadata/lens mismatch; cannot borrow A");
        for(float black:f.black) if(!std::isfinite(black)||black>=f.white)
            throw std::invalid_argument("26864 invalid phase normalization");
        if(out.normals.size()>=64u)
            throw std::invalid_argument("26864 RAW burst exceeds pinned RAWR 64-frame upper bound");
        out.normals.push_back(uint32_t(&f-frames.data()));
        const long double e=(long double)f.exposureNs * (long double)f.iso;
        const long double er=(long double)ref.exposureNs * (long double)ref.iso;
        const double gain=double(er/e);
        if(!(std::isfinite(gain)&&gain>0.0&&gain<=std::numeric_limits<float>::max()))
            throw std::invalid_argument("26864 nonfinite reference-normalizing exposure gain");
        out.gainsToReference.push_back(std::abs(gain-1.0)<1e-3?1.0f:float(gain));
        if(&f==&ref) out.referenceNormal=uint32_t(out.normals.size()-1);
    }
    if(out.normals.size()<2u)
        throw std::invalid_argument("26864 B requires at least two NORMALs; no single-frame fallback");
    out.geometry.inputWidth=req.rawWidth;out.geometry.inputHeight=req.rawHeight;
    if(out.path==Path::HdrPlusFrequency) {
        if(!validPositive(req.hdrqStrength)||req.hdrqStrength<1.f||req.hdrqStrength>22.f)
            throw std::invalid_argument("26864 invalid frequency strength");
        out.geometry=makeFrequencyGeometry(req.rawWidth,req.rawHeight,req.alignmentTileSize,
                                           req.searchDistance,req.frequencyAlignOnce);
        out.noiseOwner=NoiseOwner::HdrqReferenceTileRms;
    }else{
        // True Wronski 2x; must be retained even at local zoom >=1.10.
        out.geometry.outputWidth=checkedMultiply(req.rawWidth,2u);
        out.geometry.outputHeight=checkedMultiply(req.rawHeight,2u);
        out.referenceClipNeeds2xRemap=true;
        out.noiseOwner=NoiseOwner::WronskiRawBurstFit;
    }
    out.createBResources=true;
    out.lscBeforeAmaze=true;
    out.lscAfterAmaze=false;
    out.produceSyntheticCfaForAmaze=(out.path==Path::WronskiTrue2x);
    return out;
}
}
