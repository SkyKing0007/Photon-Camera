#pragma once
// IRIS_26864_B_WRONSKI_OUTPUT_TO_CANONICAL_AMAZE_DEV_ONLY
// Host-side typed push-constant and provenance preflight for the accompanying
// Iris-only Wronski 2x packed-CFA GLSL. No GPU queue, color matrix or JPEG owner.
#include "Iris26864Wronski2xSensorProvenance.hpp"
#include <array>
#include <cstddef>
#include <cmath>
#include <stdexcept>
#include <vector>
namespace iris26864::wronski2x {
struct LscMap final {
    uint32_t width=0,height=0;
    // Camera2 [R, G_even, G_odd, B] at each grid location, row major.
    std::vector<std::array<float,4>> texels;
};
struct SurfaceSpec final { uint64_t image=0,view=0; uint32_t width=0,height=0,format=0; };
// Explicit Vulkan VkFormat numeric values, typed preflight rather than
// interchangeably interpreting Wronski RGB as packed CFA.
constexpr uint32_t R16_UINT=74, RGBA16_SFLOAT=97;
struct alignas(16) PackedPc final {
    uint32_t width=0,height=0,lscWidth=0,lscHeight=0;
    uint32_t refWidth=0,refHeight=0,cfa=0,useSensorClip=0;
    alignas(16) std::array<float,4> black{};
    alignas(16) std::array<float,4> invRange{};
    float clipThreshold=0;
    uint32_t originX=0,originY=0,fullSensorWidth=0,fullSensorHeight=0;
    uint32_t padding[3]{};
};
static_assert(offsetof(PackedPc,black)==32);
static_assert(offsetof(PackedPc,invRange)==48);
static_assert(offsetof(PackedPc,clipThreshold)==64);
static_assert(offsetof(PackedPc,originX)==68);
static_assert(offsetof(PackedPc,fullSensorHeight)==80);
static_assert(sizeof(PackedPc)==96);
struct BoundPackedOutput final {PackedPc push;uint32_t groupX=0,groupY=0;};
inline BoundPackedOutput validatePacked2xOutput(
    const Geometry& g, const LscMap& lsc,
    const SurfaceSpec& mergedRgb, const SurfaceSpec& nativeReference,
    const SurfaceSpec& packedCfa, const SurfaceSpec& clipMask) {
    validate(g);
    if(!mergedRgb.image||!mergedRgb.view||!nativeReference.image||!nativeReference.view||
       !packedCfa.image||!packedCfa.view||!clipMask.image||!clipMask.view||
       mergedRgb.image==packedCfa.image||mergedRgb.image==nativeReference.image||
       mergedRgb.image==clipMask.image||packedCfa.image==clipMask.image||
       packedCfa.image==nativeReference.image||clipMask.image==nativeReference.image||
       mergedRgb.view==packedCfa.view||mergedRgb.view==clipMask.view||
       nativeReference.view==packedCfa.view||nativeReference.view==clipMask.view||
       packedCfa.view==clipMask.view||
       mergedRgb.format!=RGBA16_SFLOAT||nativeReference.format!=R16_UINT||
       packedCfa.format!=RGBA16_SFLOAT||clipMask.format!=R16_UINT||
       mergedRgb.width!=g.outWidth||mergedRgb.height!=g.outHeight||
       nativeReference.width!=g.refWidth||nativeReference.height!=g.refHeight||
       packedCfa.width!=g.outWidth/2||packedCfa.height!=g.outHeight/2||
       clipMask.width!=g.outWidth/2||clipMask.height!=g.outHeight/2)
        throw std::invalid_argument("26864 Wronski packed CFA surfaces/identity/format mismatch");
    if ((lsc.width==0)!=(lsc.height==0) ||
        (lsc.width!=0 && (lsc.width<2||lsc.height<2)) ||
        size_t(lsc.width)*lsc.height!=lsc.texels.size() ||
        lsc.texels.size()>(1u<<22))
        throw std::invalid_argument("26864 bad physical sensor LSC map shape");
    for(const auto& point:lsc.texels)for(float gain:point)
        if(!std::isfinite(gain)||gain<=0.f||gain>=64.f)
            throw std::invalid_argument("26864 invalid physical sensor LSC gain");
    PackedPc p{};
    p.width=g.outWidth;p.height=g.outHeight;
    p.lscWidth=lsc.width;p.lscHeight=lsc.height;
    p.refWidth=g.refWidth;p.refHeight=g.refHeight;
    p.cfa=localPattern(g);p.useSensorClip=1;
    p.black=canonicalBlack(g);p.invRange=canonicalInverseRange(g);
    p.clipThreshold=g.clipThreshold;
    p.originX=g.originX;p.originY=g.originY;
    p.fullSensorWidth=g.fullSensorWidth;
    p.fullSensorHeight=g.fullSensorHeight;
    return {p,(packedCfa.width+15u)/16u,(packedCfa.height+15u)/16u};
}
} // namespace iris26864::wronski2x
