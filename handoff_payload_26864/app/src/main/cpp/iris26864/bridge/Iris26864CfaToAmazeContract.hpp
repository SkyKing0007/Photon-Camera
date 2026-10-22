#pragma once
// IRIS_26864_B_HDRQ_CANONICAL_CFA_HANDOFF_PROOF_ONLY_NOT_ANDROID_ACTIVE
// hdrp_finalize.comp -> R32F black-subtracted/white-normalized CFA (one
// scalar per physical RAW site) -> packed {R,G1,G2,B} RGBA16F for unchanged
// successful 26863 AMaZE. Neither display RGB nor a WB/color transform.
// The GPU implementation is Iris26864HdrqCfaToAmaze.comp; this reference
// verifies exact Bayer/color/physical-Camera2 LSC/clip domain math.
#include <array>
#include <cstdint>
#include <vector>
namespace iris26864 {
struct CfaBridgeConfig final {
    uint32_t width=0,height=0,pattern=0;
    uint32_t originX=0,originY=0,fullSensorWidth=0,fullSensorHeight=0;
    uint32_t lscWidth=0,lscHeight=0;
    // RAW phase row-major from the *cropped* frame, not R,G1,G2,B order.
    std::array<float,4> blackPhase{};
    std::array<float,4> inverseRangePhase{};
    float clippingThreshold=0.995f;
};
struct CanonicalCell final {
    std::array<float,4> rgba{};
    uint16_t sensorClipMask=0;
};
struct CfaSite final {uint32_t x=0,y=0;};
// A shift of the sensor origin changes effective local pattern, including
// green-row identities. Require/derive rather than silently reinterpret.
uint32_t patternAtCrop(uint32_t physicalPattern,uint32_t originX,uint32_t originY);
std::array<CfaSite,4> canonicalSites(uint32_t localPattern,uint32_t cellX,uint32_t cellY);
// Uses raw CFA float, exact reference sensor RAW16 and optional Camera2 LSC
// grid [R,G_even,G_odd,B]. If LSC unavailable, caller must explicitly
// provide zero-dimension/no-map configuration; no Camera2 NOISE fallback.
std::vector<CanonicalCell> packCfaToAmazeReference(
    const CfaBridgeConfig& cfg,const std::vector<float>& mergedCfa,
    const std::vector<uint16_t>& referenceRaw,
    const std::vector<std::array<float,4>>& camera2LensShading);
}
