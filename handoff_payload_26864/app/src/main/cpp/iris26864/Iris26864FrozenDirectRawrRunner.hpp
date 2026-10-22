#pragma once
// IRIS_26864_NATIVE_JNI_DIRECT_NORMAL_TWO_SLOT_REAL_GPU_RUN
// Native stage called synchronously on the Android B processing worker.
// No fallback to A, Camera2 noise, Photon, or legacy Iris temporal merger.
#include "Iris26864RealRawrCoordinator.hpp"
#include "Iris26864TwoSlotRaw16Uploader.hpp"
#include <array>
#include <vector>
namespace iris26864 {
struct FrozenDirectNormal final {
    Raw16PlaneBorrow borrowed{};
    uint64_t physicalLensIdentity=0;
    float exposureProduct=0.f;
    float whiteLevel=0.f;
    std::array<float,4> blackByPhase{};
    std::array<float,3> whiteBalance{{1.f,1.f,1.f}};
};
struct FrozenDirectBRequest final {
    VkPhysicalDevice physical=VK_NULL_HANDLE;
    VkDevice device=VK_NULL_HANDLE;
    VkQueue inheritedQueue=VK_NULL_HANDLE;
    uint32_t queueFamily=0;
    uint32_t width=0,height=0,localCfa=0,referenceIndex=0;
    RealBEngine algorithm=RealBEngine::HdrPlusFrequency;
    std::vector<FrozenDirectNormal> normals;
};
// The caller's original SafeImage ByteBuffer owners stay live through this
// synchronous call. JNI must not free the source between stage and GPU fence.
void runRealRawrFromFrozenDirectNormals(
    const FrozenDirectBRequest&, amaze::CommandSubmissionOwner& inheritedUploads,
    const ConsumePinnedRawrGpuResult& consumeGpuBeforeScratchRelease);
} // namespace iris26864
