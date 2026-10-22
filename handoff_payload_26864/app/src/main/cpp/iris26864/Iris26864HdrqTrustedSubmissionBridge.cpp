#include "Iris26864HdrqTrustedSubmissionBridge.hpp"
#include <stdexcept>
#include <cmath>
#include <utility>
namespace iris26864 {
namespace {
void submitValidatedHdrq(
    amaze::CommandSubmissionOwner& trustedSubmission,
    const HdrqPinnedPipelineOwner& bOnlyKernels,
    const Plan& frozenPlan,
    const HdrqExpandedBindingProvider& bindingProvider,
    const std::function<void(VkCommandBuffer)>& initGeneralLayouts,
    const std::function<void(VkCommandBuffer)>& afterFrequency,
    HdrqExternalSynchronization synchronization) {
    if (frozenPlan.path != Path::HdrPlusFrequency ||
        frozenPlan.noiseOwner != NoiseOwner::HdrqReferenceTileRms ||
        !frozenPlan.createBResources || !frozenPlan.lscBeforeAmaze ||
        frozenPlan.lscAfterAmaze || frozenPlan.normals.size() < 2u ||
        frozenPlan.referenceNormal >= frozenPlan.normals.size() ||
        bOnlyKernels.size() != 23u || !bindingProvider || !initGeneralLayouts)
        throw std::invalid_argument("26864 B HDRq trusted-submit ownership incomplete");
    if (synchronization.usesExternalGl !=
        (synchronization.glAcquire != VK_NULL_HANDLE &&
         synchronization.glRelease != VK_NULL_HANDLE) ||
        (synchronization.glAcquire != VK_NULL_HANDLE) !=
        (synchronization.glRelease != VK_NULL_HANDLE) ||
        (synchronization.glAcquire != VK_NULL_HANDLE &&
         synchronization.glAcquire == synchronization.glRelease))
        throw std::invalid_argument("26864 HDRq invalid symmetric GL/Vulkan fence transfer");
    auto ownedBindings = [&](const HdrqDispatch& step) {
        auto jobs = bindingProvider(step);
        for (const auto& job : jobs) {
            if (job.kind == HdrqRecordedKind::Kernel &&
                (!job.kernel || !bOnlyKernels.owns(job.kernel)))
                throw std::invalid_argument("26864 B frequency stage imported non-B Vulkan pipeline");
        }
        return jobs;
    };
    // The exact 26863 successful owner does NOT submit on a record exception.
    // Any missing later CFA/AMaZE stage therefore cannot publish partial HDRq.
    trustedSubmission.execute([&](VkCommandBuffer cmd) {
        initGeneralLayouts(cmd);
        recordHdrqVulkanExpandedSchedule(frozenPlan, cmd, ownedBindings);
        if (afterFrequency) afterFrequency(cmd);
    }, synchronization.glAcquire, synchronization.glRelease);
}
} // namespace
void submitPinnedHdrqUsing26863Owner(
    amaze::CommandSubmissionOwner& trustedSubmission,
    const HdrqPinnedPipelineOwner& bOnlyKernels,
    const Plan& frozenPlan,
    const HdrqExpandedBindingProvider& bindingProvider,
    const std::function<void(VkCommandBuffer)>& initGeneralLayouts,
    HdrqExternalSynchronization synchronization) {
    // Legacy DEV-ONLY frequency isolated test. Runtime MUST use the complete
    // all-or-nothing HDRq -> packed CFA -> 26863 AMaZE entrypoint below.
    submitValidatedHdrq(trustedSubmission,bOnlyKernels,frozenPlan,bindingProvider,
                        initGeneralLayouts,{},synchronization);
}
void submitPinnedHdrqAndCanonicalAmazeUsing26863Owner(
    amaze::CommandSubmissionOwner& trustedSubmission,
    const HdrqPinnedPipelineOwner& bOnlyKernels,
    const Plan& frozenPlan,
    const HdrqExpandedBindingProvider& bindingProvider,
    const std::function<void(VkCommandBuffer)>& initGeneralLayouts,
    const VulkanKernelExecutor& irisOwnedCanonicalBridge,
    const HdrqCanonicalGpuFrame& frame,
    const std::function<void(VkCommandBuffer)>& record26863Amaze,
    HdrqExternalSynchronization synchronization) {
    if(!record26863Amaze || !frame.packedRgba16fImage ||
       frozenPlan.geometry.outputWidth != frame.cfg.width ||
       frozenPlan.geometry.outputHeight != frame.cfg.height ||
       frozenPlan.path != Path::HdrPlusFrequency ||
       frozenPlan.produceSyntheticCfaForAmaze ||
       frozenPlan.referenceClipNeeds2xRemap)
        throw std::invalid_argument("26864 HDRq/Amaze composite ownership or output extent invalid");
    // Preflight BEFORE even recording HDRq, to reject tint-prone wrong Bayer
    // phase and missing RAW/shading image sources without GPU mutation.
    preflightCanonicalCfaBridge(irisOwnedCanonicalBridge,frame);
    submitValidatedHdrq(trustedSubmission,bOnlyKernels,frozenPlan,bindingProvider,
        initGeneralLayouts,[&](VkCommandBuffer cmd) {
            recordCanonicalCfaForAmaze(cmd,irisOwnedCanonicalBridge,frame);
            // The unchanged 26863 AMaZE pipeline consumes frame.packedRgba16fView
            // in the SAME command buffer/context. JNI must verify handle identity.
            record26863Amaze(cmd);
        },synchronization);
}
} // namespace iris26864

namespace iris26864 {
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
    HdrqExternalSynchronization synchronization) {
    // Reject incorrect output and AMaZE configurations BEFORE ANY Vulkan
    // command recording, including cases which would produce full-frame tints.
    const auto& config=exact26863Amaze.config();
    if (config.inputMode != amaze::InputMode::PackedCfaRgba16fImage ||
        config.width != frame.cfg.width || config.height != frame.cfg.height ||
        static_cast<uint32_t>(config.pattern) != frame.cfg.pattern ||
        output.width != frame.cfg.width || output.height != frame.cfg.height ||
        output.format != VK_FORMAT_R16G16B16A16_SFLOAT ||
        output.layout != VK_IMAGE_LAYOUT_GENERAL ||
        output.image == VK_NULL_HANDLE || output.view == VK_NULL_HANDLE ||
        output.image == frame.packedRgba16fImage ||
        output.view == frame.packedRgba16fView ||
        output.view == frame.r32CfaView ||
        frame.packedRgba16fImage == VK_NULL_HANDLE ||
        frame.packedRgba16fView == VK_NULL_HANDLE)
        throw std::invalid_argument("26864 HDRq typed AMaZE output/config/image identity mismatch");
    for (float gain : whiteBalance) {
        if (!(gain > 0.f) || !std::isfinite(gain))
            throw std::invalid_argument("26864 HDRq typed AMaZE white balance non-finite or zero");
    }
    amaze::PackedCfaImageView packed{};
    packed.image=frame.packedRgba16fImage;
    packed.view=frame.packedRgba16fView;
    packed.format=VK_FORMAT_R16G16B16A16_SFLOAT;
    packed.layout=VK_IMAGE_LAYOUT_GENERAL;
    packed.width=frame.cfg.width/2u;
    packed.height=frame.cfg.height/2u;
    packed.rawWidth=frame.cfg.width;
    packed.rawHeight=frame.cfg.height;
    packed.pattern=static_cast<amaze::BayerPattern>(frame.cfg.pattern);
    // AMaZE input is constructed here from the EXACT bridge target. There
    // is no caller-supplied callback or independent CFA input handle.
    submitPinnedHdrqAndCanonicalAmazeUsing26863Owner(
        trustedSubmission,bOnlyKernels,frozenPlan,bindingProvider,
        initGeneralLayouts,irisOwnedCanonicalBridge,frame,
        [&](VkCommandBuffer cmd){exact26863Amaze.record(cmd,packed,output,whiteBalance);},
        synchronization);
}
} // namespace iris26864
