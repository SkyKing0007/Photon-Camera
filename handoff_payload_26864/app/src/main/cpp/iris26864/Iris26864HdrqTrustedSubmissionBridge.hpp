#pragma once
// IRIS_26864_HDRQ_26863_SUBMISSION_OWNER_REUSE_NOT_ANDROID_ACTIVE
// HDR+ Higher quality uses the exact successful 26863 AMaZE Vulkan command
// submission implementation. This adapter does not create a competing queue,
// fence, or GL ownership system. Commands are recorded only for the B HDRq
// path, with all stages (and kernel identities) validated before GPU submit.
// Caller MUST keep source RAW image imports, scratch and all pipelines alive
// through the fence wait. On a fence failure the command owner's queue must
// be settled BEFORE those resources may be reclaimed; retain their owners on
// an unresolved device/queue. No original 26863 owner source is modified.
#include "Iris26864HdrqPinnedPipelineOwner.hpp"
#include "bridge/Iris26864HdrqCanonicalGpuBridge.hpp"
#include "Iris26864HdrqVulkanRecorder.hpp"
#include "amaze/CommandSubmissionOwner.hpp"
#include "amaze/Amaze.hpp"
#include <array>
#include <functional>
namespace iris26864 {
struct HdrqExternalSynchronization {
    // Both semaphores must be supplied together ONLY for a GL/AHB boundary.
    // The caller imports the GL release fence and exports the Vulkan release
    // fence using the existing 26863 ExternalFenceSync owner.
    VkSemaphore glAcquire = VK_NULL_HANDLE;
    VkSemaphore glRelease = VK_NULL_HANDLE;
    bool usesExternalGl = false;
};
// Queue submission is synchronous to the Vulkan fence, NOT image/color proof.
// initGeneralLayouts records the resource arena's first-use UNDEFINED->GENERAL
// image barriers; it may not contain CPU pixel mapping or GL calls.
// No camera request, JPEG publication, A/B fallback or LONG processing occurs
// in this narrow native method.
void submitPinnedHdrqUsing26863Owner(
    amaze::CommandSubmissionOwner& trustedSubmission,
    const HdrqPinnedPipelineOwner& bOnlyKernels,
    const Plan& frozenPlan,
    const HdrqExpandedBindingProvider& bindingProvider,
    const std::function<void(VkCommandBuffer)>& initGeneralLayouts,
    HdrqExternalSynchronization synchronization = {});
// B HDRq -> canonical packed CFA -> unchanged AMaZE in ONE command buffer.
// The last callback must be the 26863 AmazePipeline::record bound to EXACT
// frame.packedRgba16fView. JNI identity validation is a release blocker.
void submitPinnedHdrqAndCanonicalAmazeUsing26863Owner(
    amaze::CommandSubmissionOwner& trustedSubmission,
    const HdrqPinnedPipelineOwner& bOnlyKernels,
    const Plan& frozenPlan,
    const HdrqExpandedBindingProvider& bindingProvider,
    const std::function<void(VkCommandBuffer)>& initGeneralLayouts,
    const VulkanKernelExecutor& irisOwnedCanonicalBridge,
    const HdrqCanonicalGpuFrame& frame,
    const std::function<void(VkCommandBuffer)>& record26863Amaze,
    HdrqExternalSynchronization synchronization = {});
}

namespace iris26864 {
// Runtime-facing strongly typed alternative to the development-only arbitrary
// record callback. Build the AMaZE input from the same caller-owned image/view
// used as the bridge descriptor: no opportunity to substitute a GL, old-frame,
// demosaiced-RGB or foreign Bayer CFA texture at the last stage.
// Must be called on the inherited Vulkan queue/device with ALL owners kept
// alive until successful fence wait; does not take ownership or publish JPEG.
void submitPinnedHdrqAndBoundAmazeUsing26863Owner(
    amaze::CommandSubmissionOwner& trustedSubmission,
    const HdrqPinnedPipelineOwner& bOnlyKernels,
    const Plan& frozenPlan,
    const HdrqExpandedBindingProvider& bindingProvider,
    const std::function<void(VkCommandBuffer)>& initGeneralLayouts,
    const VulkanKernelExecutor& irisOwnedCanonicalBridge,
    const HdrqCanonicalGpuFrame& frame,
    amaze::AmazePipeline& exact26863Amaze,
    const amaze::LinearRgbImage& output,
    const std::array<float,3>& whiteBalance,
    HdrqExternalSynchronization synchronization = {});
} // namespace iris26864
