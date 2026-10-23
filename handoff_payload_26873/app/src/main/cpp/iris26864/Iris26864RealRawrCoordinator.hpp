#pragma once
// IRIS_26864_REAL_PINNED_RAWR_B_DISPATCH
// Only the pinned upstream AndroidBurstCoordinator runs alignment, empirical
// noise, robustness and merging. No Iris copies of these algorithms, and no
// second Vulkan device/queue owner. GL/JNI output consumption is synchronous:
// upstream arena pixels must not outlive the coordinator's run scope.
#include <rawr/raw_gpu_pipeline/AndroidBurstCoordinator.h>
#include <vulkan/vulkan.h>
#include <array>
#include <cstdint>
#include <functional>
#include <vector>

namespace iris26864 {
enum class RealBEngine { HdrPlusFrequency, WronskiTrue2x };
enum class FrozenRawInputLayout { FencedTwoSlot, CaptureResident };
struct RealRawrNormal final {
    rawr::zsl_ring::GpuRawImageView borrowedRaw{};
    uint64_t timestampNs = 0;
    uint64_t physicalLensIdentity = 0;
    float exposureProduct = 0.f;
    float sensorWhite = 0.f;
    std::array<float,4> phaseBlack{{0,0,0,0}};
    std::array<float,3> whiteBalance{{1,1,1}};
};
struct RealRawrRunRequest final {
    VkPhysicalDevice physical=VK_NULL_HANDLE;
    VkDevice device=VK_NULL_HANDLE;
    VkQueue inheritedQueue=VK_NULL_HANDLE;
    uint32_t queueFamily=0;
    uint32_t width=0,height=0;
    uint32_t effectiveCfa=0;
    uint32_t referenceIndex=0;
    RealBEngine algorithm=RealBEngine::HdrPlusFrequency;
    FrozenRawInputLayout inputLayout=FrozenRawInputLayout::FencedTwoSlot;
    // Native RAW images, acquired through the existing 26863 fenced uploader,
    // remain owned by the JNI caller through the entire synchronous callback.
    std::vector<RealRawrNormal> normals;
    // Synchronous JNI RAW16 -> fenced Vulkan transfer into one reference
    // slot or the single reusable companion slot; called from RAWR run().
    rawr::raw_gpu_pipeline::AndroidBurstCoordinator::FramePrepared prepareNormal;
};
using ConsumePinnedRawrGpuResult = std::function<void(
    const rawr::raw_gpu_pipeline::BurstRunResult& result,
    const RealRawrRunRequest& frozen)>;

// Synchronously executes real RAWR kernels and consumes output while the
// upstream Vulkan arena is alive. Exceptions always abort JPEG publication.
// The caller is responsible for input's last fence and GLES handoff fences.
void runRealPinnedRawrB(const RealRawrRunRequest& frozen,
                        const ConsumePinnedRawrGpuResult& consume);
}
