#include "Iris26864RealRawrCoordinator.hpp"
#include <optional>
/* 26912: symbol is defined by the unchanged CMake B-only shadow
 * AndroidBurstCoordinator.cpp. No new header needs to cross into the
 * separate, pinned vendor build-copy include root. */
namespace rawr::raw_gpu_pipeline {
extern thread_local std::optional<std::array<float,8>> iris26912BOffNoiseOverride;
}
#include <cmath>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_set>

namespace iris26864 {
namespace {
using namespace rawr::raw_gpu_pipeline;
void checkFrozen(const RealRawrRunRequest& r) {
    if(!r.physical||!r.device||!r.inheritedQueue||r.width<32u||r.height<32u||
       (r.width&1u)||(r.height&1u)||r.width>16384u||r.height>16384u||
       r.effectiveCfa>=4u||r.normals.size()<2u||r.normals.size()>64u||
       r.referenceIndex>=r.normals.size())
        throw std::invalid_argument("26864 missing real B Vulkan/frozen NORMAL provenance");
    if(!r.prepareNormal) throw std::invalid_argument("26873 missing real fenced RAW16 source owner");
    if(r.inputLayout==FrozenRawInputLayout::CaptureResident &&
       r.algorithm!=RealBEngine::HdrPlusFrequency)
        throw std::invalid_argument("26873 resident inputs B-HDRq ONLY");
    const uint64_t physical=r.normals.front().physicalLensIdentity;
    if(!physical) throw std::invalid_argument("26864 missing physical lens identity");
    std::unordered_set<uint64_t> timestamps;
    const auto referenceRaw=r.normals[r.referenceIndex].borrowedRaw;
    VkImage companion=VK_NULL_HANDLE;
    VkImageView companionView=VK_NULL_HANDLE;
    std::unordered_set<VkImage> residentImages;
    std::unordered_set<VkImageView> residentViews;
    for(std::size_t index=0;index<r.normals.size();++index) {
        const auto& f=r.normals[index];
        if(r.inputLayout==FrozenRawInputLayout::CaptureResident) {
            // All per-frame RAW views must be unique, immutable until the
            // synchronous downstream consumer returns, and never alias scratch.
            if(!residentImages.insert(f.borrowedRaw.image).second||
               !residentViews.insert(f.borrowedRaw.view).second)
                throw std::invalid_argument("26873 resident RAW images must be distinct per frame");
        } else if(index!=r.referenceIndex) {
            if(!companion) { companion=f.borrowedRaw.image; companionView=f.borrowedRaw.view; }
            if(f.borrowedRaw.image!=companion||f.borrowedRaw.view!=companionView||
               f.borrowedRaw.image==referenceRaw.image||
               f.borrowedRaw.view==referenceRaw.view)
                throw std::invalid_argument("26864 must have one reference and ONE fenced companion GPU slot");
        }
        if(f.physicalLensIdentity!=physical||!f.timestampNs||
           !timestamps.insert(f.timestampNs).second ||
           f.borrowedRaw.ref.width!=r.width||f.borrowedRaw.ref.height!=r.height||
           f.borrowedRaw.ref.timestampNs!=f.timestampNs||
           !f.borrowedRaw.image||!f.borrowedRaw.view||
           f.borrowedRaw.format!=VK_FORMAT_R16_UINT||
           !std::isfinite(f.exposureProduct)||f.exposureProduct<=0.f||
           !std::isfinite(f.sensorWhite)||f.sensorWhite<=0.f)
            throw std::invalid_argument("26864 stale/mixed/truncated native RAW burst");
        for(float b:f.phaseBlack) if(!std::isfinite(b)||b<0.f||b>=f.sensorWhite)
            throw std::invalid_argument("26864 invalid per-frame RAW black/white range");
        for(float w:f.whiteBalance) if(!std::isfinite(w)||w<=0.f)
            throw std::invalid_argument("26864 invalid physical white-balance metadata");
    }
}
} // namespace
void runRealPinnedRawrB(const RealRawrRunRequest& frozen,
                        const ConsumePinnedRawrGpuResult& consume) {
    checkFrozen(frozen);
    if(!consume) throw std::invalid_argument("26864 missing actual GPU output consumer");
    const bool sr=frozen.algorithm==RealBEngine::WronskiTrue2x;
    rawr::raw_merge_wronski_gpu::Config wronski{};
    wronski.cfa=static_cast<rawr::raw_merge_wronski_gpu::CfaPattern>(frozen.effectiveCfa);
    // Original Wronski RAW-burst fitting remains the fallback. Only an explicitly
    // selected, validated per-physical-lens .c model bypasses fitting and is
    // consistently supplied to merge plus the pre-WB chroma wavelet.
    wronski.estimateNoiseFromBurst=!(sr && frozen.hasBOffCustomNoise);
    if (sr && frozen.hasBOffCustomNoise) {
        rawr::raw_merge_wronski_gpu::CfaNoiseProfile model{};
        for (std::size_t phase=0;phase<4u;++phase) {
            model.slopeBySite[phase]=frozen.bOffNoiseByPhase[2u*phase];
            model.offsetBySite[phase]=frozen.bOffNoiseByPhase[2u*phase+1u];
        }
        if (!rawr::raw_merge_wronski_gpu::valid(model))
            throw std::invalid_argument("26914 invalid frozen B Wronski lens noise profile");
        wronski.sensorNoiseProfile=model;
        wronski.highSignalNoiseProfile.reset();
        wronski.noiseKneeBySite.fill(0.f);
    }
    // IRIS_26880_RAWR_REFERENCE_MULTIFRAME_PARITY (source/exif audited):
    // RAWR v0.5.0 Wronski Super-resolution is not the vendor Config default.
    // Match the user's RAWR MF8 reference, including motion/fallback cleanup;
    // leave the independent HDR+ (Super Res OFF) route byte-for-byte unchanged.
    // This is ONLY the merge-stage configuration. The separate RAWR JPEG-only
    // burst-noise wavelet chroma stage must be integrated after AMaZE and BEFORE
    // final Iris color; do not call this alone full RAWR pipeline parity.
    rawr::raw_alignment_gpu::Config alignment{};
    if (sr) {
        alignment.lkIterations=5u;
        alignment.hessianEpsilon=1.0e-10f;
        wronski.kDetail=0.150f;
        wronski.kDenoise=5.0f; // kDenoise is bypassed when flatSigma >= 0 (pinned kernel shader)
        wronski.dThreshold=0.710f;
        wronski.dTransition=1.0f;
        wronski.kStretch=2.0f;
        wronski.kShrink=8.0f;
        wronski.flatSigma=0.90f; // IRIS_26923_B_SR_ON_ACTIVE_FLAT_KERNEL_BANDWIDTH: measured 2x detail, B OFF unchanged
        wronski.detailFloorSigma=0.150f;
        wronski.scaleBandwidthGain=1.0f;
        wronski.coverageNeffLo=1.0f;
        wronski.coverageNeffHi=3.0f;
        wronski.coverageMassLo=0.010f;
        wronski.coverageMassHi=0.040f;
        wronski.robustnessT=0.080f;
        wronski.robustnessS1=1.5f;
        wronski.robustnessS2=9.0f;
        wronski.motionThreshold=0.650f;
        // Exact per-physical-lens, shutter-admitted user quarter-steps.
        // This controls only the existing native fallback radius, never
        // RAW-burst variance estimation or the independent chroma correction.
        const float limits[3]={8.f,4.f,16.f};
        for(std::size_t i=0;i<3u;++i) {
            const float v=frozen.iris26926Fallback[i];
            if(!std::isfinite(v)||v<0.f||v>limits[i]||
               std::abs(v*4.f-std::round(v*4.f))>1e-5f)
                throw std::invalid_argument("26926 invalid quarter-step native fallback");
        }
        wronski.fallbackChromaGain=frozen.iris26926Fallback[0];
        wronski.fallbackLumaGain=frozen.iris26926Fallback[1];
        wronski.fallbackChromaMaxSigma=frozen.iris26926Fallback[2];
    }
    wronski.iris26920Active = sr && frozen.iris26920Active;
    rawr::raw_merge_hdrplus_gpu::Config hdrq{};
    // RAWR's chunk fence can fail after a successful VkQueueSubmit. Keep the
    // coordinator alive until an explicit queue-idle proof has settled every
    // possible submission, rather than letting stack unwinding release its
    // arena and command pool before the frozen uploader's outer catch runs.
    auto coordinator = std::make_unique<AndroidBurstCoordinator>();
    auto inheritedSubmit=[queue=frozen.inheritedQueue](const VkSubmitInfo& si,VkFence fence){
        if(vkQueueSubmit(queue,1u,&si,fence)!=VK_SUCCESS)
            throw std::runtime_error("26864 actual RAWR GPU queue submission failed");
    };
    coordinator->initialize(frozen.physical,frozen.device,frozen.queueFamily,
        inheritedSubmit,frozen.width,frozen.height,sr?2.f:1.f,{},
        alignment,wronski,sr?MergeAlgorithm::Wronski:MergeAlgorithm::HdrPlusFrequency,hdrq);
    std::vector<BurstFrame> upstream;
    upstream.reserve(frozen.normals.size());
    for(const auto& f:frozen.normals) {
        BurstFrame frame{};
        frame.raw=f.borrowedRaw;
        frame.exposure=f.exposureProduct;
        frame.parameters.normalization.blackByPhase=f.phaseBlack;
        frame.parameters.normalization.whiteLevel=f.sensorWhite;
        frame.parameters.whiteBalance=f.whiteBalance;
        upstream.push_back(frame);
    }
    // The output image and cfaView remain owned by coordinator's scratch
    // arena. NEVER return these Vulkan handles to Java or release scratch
    // until the downstream packed-CFA+AMaZE fence has completed.
    try {
        /* IRIS_26914_B_OFF_THREAD_LOCAL_SCOPE: synchronous, thread-local, RAII-restored
         * independent physical-lens model. Source vendor APIs remain intact.
         * A missing profile leaves the successful 26911 burst estimator alone.
         */
        struct RestoreBNoise final {
            std::optional<std::array<float,8>> previous;
            ~RestoreBNoise() noexcept {
                rawr::raw_gpu_pipeline::iris26912BOffNoiseOverride = previous;
            }
        } restore{rawr::raw_gpu_pipeline::iris26912BOffNoiseOverride};
        if (!sr && frozen.hasBOffCustomNoise)
            rawr::raw_gpu_pipeline::iris26912BOffNoiseOverride = frozen.bOffNoiseByPhase;
        else rawr::raw_gpu_pipeline::iris26912BOffNoiseOverride.reset();
        auto result=coordinator->run(upstream,frozen.referenceIndex,{},frozen.prepareNormal);
        if(sr && frozen.hasBOffCustomNoise) {
            // Exact calibrated model, not an empirical fit. The original
            // post-AMaZE RAWR wavelet must consume the SAME sensor-site model
            // as Wronski merging; preserve real full-burst count.
            result.noiseEstimated=true;
            result.estimatedNoise=*wronski.sensorNoiseProfile;
        }
        if(sr && (!result.noiseEstimated || !rawr::raw_merge_wronski_gpu::valid(result.estimatedNoise)))
            throw std::runtime_error("26923 B SR ON mandatory RAW burst/custom .c noise missing");
        if(!result.output||!result.outputView||result.frameCount!=upstream.size()||
           result.referenceIndex!=frozen.referenceIndex)
            throw std::runtime_error("26864 real RAWR output missing or frame-count degraded");
        if(sr) {
            // The pinned RAWR MfsrCaptureJob allows a completed multiframe
            // Wronski reconstruction without a valid burst-noise fit.  It
            // then leaves its pre-WB chroma wavelet OFF instead of fabricating
            // a Camera2 profile.  The B-only downstream bridge makes that
            // same measured-noise decision and logs an explicit warning.
            // Rejecting noiseEstimated=false here made the proven original
            // Wronski reconstruction/fallback unreachable.  Never weaken the
            // true-2x output, participating-frame or ownership checks below.
            if(result.outputExtent.width!=frozen.width*2u||
               result.outputExtent.height!=frozen.height*2u)
                throw std::runtime_error("26864 Wronski must produce true-2x output");
        } else {
            if(!result.cfaImage||!result.cfaView||
               result.outputExtent.width!=frozen.width||
               result.outputExtent.height!=frozen.height)
                throw std::runtime_error("26864 HDR+ Higher quality must provide native CFA output");
        }
        consume(result,frozen); // synchronous AMaZE/clip/LSC/JPEG boundary
    } catch (...) {
        const VkResult idle = vkQueueWaitIdle(frozen.inheritedQueue);
        if (idle != VK_SUCCESS) {
            // On an unresolved/device-lost queue, the upstream coordinator's
            // destructor would free images/buffers while the submitted work
            // might still refer to them. Quarantine exactly that instance.
            // The outer two-slot owner independently quarantines its inputs.
            (void)coordinator.release();
        }
        throw; // Never publish a partial B image or use an A/Camera2 fallback.
    }
}
}
