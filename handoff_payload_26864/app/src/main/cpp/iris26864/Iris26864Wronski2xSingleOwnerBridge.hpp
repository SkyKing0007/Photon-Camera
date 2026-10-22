#pragma once
// IRIS_26864_WRONSKI_2X_TYPED_SINGLE_OWNER_DEV_ONLY_NOT_ANDROID_ACTIVE
// Uses the exact successful 26863 AMaZE packed-CFA input contract. This file
// neither submits a queue nor imports an AHB nor publishes an output image.
// Upstream RAWR provenance: ce767e80bfce2e1641abf7dad6b1bf504d844fd9
#include "Iris26864Wronski2xPackedBinding.hpp"
#include "Iris26864VulkanKernelExecutor.hpp"
#include "amaze/Amaze.hpp"
#include <array>

namespace iris26864::wronski2x {
struct SingleOwner2xFrames final {
    Geometry geometry;
    LscMap lsc;
    SurfaceSpec mergedCameraRgb; // output of pinned RAWR a11_finalize; camera-linear, before LSC
    SurfaceSpec originalReferenceRaw;
    SurfaceSpec packedCfa; // physical LSC applied HERE before the SAME 26863 AMaZE image/view
    SurfaceSpec sensorClip; // a separate downstream ownership sidecar
    SurfaceSpec amazeRgb;
    VkBuffer lscBuffer=VK_NULL_HANDLE;
    VkDeviceSize lscBytes=0;
    std::array<float,3> whiteBalance{{1.f,1.f,1.f}};
    // The upstream coordinator can retain a configured noise profile when
    // estimateNoiseFromBurst fails. Iris B forbids that fallback. This field
    // must be populated ONLY from BurstRunResult::noiseEstimated after a real
    // per-site RAW-burst fit; the default is deliberately non-publishable.
    bool rawrBurstNoiseFitted = false;
};
struct ClipSidecarReceipt final {
    VkImage image=VK_NULL_HANDLE;
    VkImageView view=VK_NULL_HANDLE;
    uint32_t width=0,height=0,localCfa=0;
    // RAWR-domain ownership receipt for the NEW B engine only. The downstream
    // caller must not apply legacy Iris post-AMaZE LSC or residual noise.
    // These are declared semantics of the Wronski packer; device proof pending.
    bool preAmazeLscStageComplete=true;
    bool physicalLscMapPresent=false;
    bool legacyPostAmazeLscPermitted=false;
    bool legacyIrisChromaDenoisePermitted=false;
    // AMaZE does NOT read this sidecar. The separate sensor-clip owner must
    // preserve/consume it before any JPEG/UHDR publication can be verified.
};
struct PreparedSingleOwner2x final {
    BoundPackedOutput kernel;
    amaze::PackedCfaImageView amazeInput;
    amaze::LinearRgbImage amazeOutput;
    ClipSidecarReceipt clipping;
};
PreparedSingleOwner2x prepareSingleOwner2x(
    const SingleOwner2xFrames&,
    const VulkanKernelExecutor& packedKernel,
    const amaze::AmazePipeline& amaze);
// ONLY records Vulkan compute on the inherited caller command buffer. The
// exact 26863 submission owner is responsible for fences and queue lifetime.
ClipSidecarReceipt recordWronski2xToAmaze(
    VkCommandBuffer, const SingleOwner2xFrames&,
    const VulkanKernelExecutor& packedKernel,
    amaze::AmazePipeline& amaze);
} // namespace iris26864::wronski2x
