#include "Iris26864RealRawrCoordinator.hpp"
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
    if(!r.prepareNormal) throw std::invalid_argument("26864 missing real fenced two-slot RAW16 source owner");
    const uint64_t physical=r.normals.front().physicalLensIdentity;
    if(!physical) throw std::invalid_argument("26864 missing physical lens identity");
    std::unordered_set<uint64_t> timestamps;
    const auto referenceRaw=r.normals[r.referenceIndex].borrowedRaw;
    VkImage companion=VK_NULL_HANDLE;
    VkImageView companionView=VK_NULL_HANDLE;
    for(std::size_t index=0;index<r.normals.size();++index) {
        const auto& f=r.normals[index];
        if(index!=r.referenceIndex) {
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
    // Always require freshly measured RAW-burst noise on Wronski. Upstream
    // accepts a configured fallback if fitting fails; the Iris caller does NOT.
    wronski.estimateNoiseFromBurst=true;
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
        {},wronski,sr?MergeAlgorithm::Wronski:MergeAlgorithm::HdrPlusFrequency,hdrq);
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
        const auto result=coordinator->run(upstream,frozen.referenceIndex,{},frozen.prepareNormal);
        if(!result.output||!result.outputView||result.frameCount!=upstream.size()||
           result.referenceIndex!=frozen.referenceIndex)
            throw std::runtime_error("26864 real RAWR output missing or frame-count degraded");
        if(sr) {
            if(!result.noiseEstimated)
                throw std::runtime_error("26864 Wronski measured RAW burst fit absent: no noise fallback");
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
