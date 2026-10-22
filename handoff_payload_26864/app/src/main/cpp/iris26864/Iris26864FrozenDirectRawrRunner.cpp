#include "Iris26864FrozenDirectRawrRunner.hpp"
#include <cmath>
#include <stdexcept>
#include <utility>
namespace iris26864 {
void runRealRawrFromFrozenDirectNormals(
    const FrozenDirectBRequest& request, amaze::CommandSubmissionOwner& inheritedUploads,
    const ConsumePinnedRawrGpuResult& consume) {
    if(!request.physical||!request.device||!request.inheritedQueue||
       request.width<32u||request.height<32u||(request.width&1u)||(request.height&1u)||
       request.localCfa>3u||request.referenceIndex>=request.normals.size()||
       request.normals.size()<2u||request.normals.size()>64u||!consume)
        throw std::invalid_argument("26864 B frozen direct NORMAL run invalid");
    TwoSlotRaw16Uploader twoSlots(request.physical,request.device,
                                   inheritedUploads,request.width,request.height);
    const auto ref=twoSlots.referenceImage();
    const auto companion=twoSlots.companionImage();
    RealRawrRunRequest merge{};
    merge.physical=request.physical;
    merge.device=request.device;
    merge.inheritedQueue=request.inheritedQueue;
    merge.queueFamily=request.queueFamily;
    merge.width=request.width;merge.height=request.height;
    merge.effectiveCfa=request.localCfa;
    merge.referenceIndex=request.referenceIndex;
    merge.algorithm=request.algorithm;
    std::vector<Raw16PlaneBorrow> raw;
    raw.reserve(request.normals.size());
    merge.normals.reserve(request.normals.size());
    for(std::size_t i=0;i<request.normals.size();++i) {
        const auto& f=request.normals[i];
        if(f.borrowed.width!=request.width||f.borrowed.height!=request.height||
           !f.borrowed.timestamp||!f.physicalLensIdentity||
           !std::isfinite(f.exposureProduct)||f.exposureProduct<=0.f||
           !std::isfinite(f.whiteLevel)||f.whiteLevel<=0.f)
            throw std::invalid_argument("26864 B frozen normal bytes/lens/exposure invalid");
        const auto gpu=(i==request.referenceIndex)?ref:companion;
        RealRawrNormal frame{};
        frame.borrowedRaw.ref.frameId=i+1u;
        frame.borrowedRaw.ref.timestampNs=f.borrowed.timestamp;
        frame.borrowedRaw.ref.width=request.width;
        frame.borrowedRaw.ref.height=request.height;
        frame.borrowedRaw.image=gpu.image;
        frame.borrowedRaw.view=gpu.view;
        frame.borrowedRaw.format=gpu.format;
        frame.timestampNs=f.borrowed.timestamp;
        frame.physicalLensIdentity=f.physicalLensIdentity;
        frame.exposureProduct=f.exposureProduct;
        frame.sensorWhite=f.whiteLevel;
        frame.phaseBlack=f.blackByPhase;
        frame.whiteBalance=f.whiteBalance;
        merge.normals.push_back(frame);
        raw.push_back(f.borrowed);
    }
    merge.prepareNormal=[&](std::uint32_t index){
        twoSlots.upload(index,request.referenceIndex,raw);
    };
    // The pinned coordinator callback runs BEFORE it frees native GPU scratch;
    // the post-merge packer/AMaZE may ONLY consume its result synchronously.
    try {
        runRealPinnedRawrB(merge,consume);
    }catch(...){
        // Every upstream chunk and upload uses a waited fence. Retain GPU
        // input allocations if the queue entered an unresolved state.
        const VkResult idle=vkQueueWaitIdle(request.inheritedQueue);
        if(idle!=VK_SUCCESS) twoSlots.quarantineUnresolved();
        throw;
    }
}
} // namespace iris26864
