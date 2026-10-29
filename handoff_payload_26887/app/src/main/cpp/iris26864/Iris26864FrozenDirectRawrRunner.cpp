#include "Iris26864FrozenDirectRawrRunner.hpp"
#include <cmath>
#include <algorithm>
#include <chrono>
#include <memory>
#include <android/log.h>
#include <stdexcept>
#include <string>
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
    // IRIS_26873_B_RESIDENT_INPUT_OWNER. One capture scoped owner, not a
    // second camera ZSL ring, not a new JNI/GL/Vulkan context.
    // RAWR Wronski 2x intentionally remains exactly inherited two-slot.
    const bool hdrq=request.algorithm==RealBEngine::HdrPlusFrequency;
    const uint64_t rawBytes=uint64_t(request.width)*request.height*2u;
    bool residentEligible=hdrq && request.normals.size()<=30u;
    if(residentEligible) {
        VkPhysicalDeviceMemoryProperties mem{};
        vkGetPhysicalDeviceMemoryProperties(request.physical,&mem);
        uint64_t largestDeviceHeap=0;
        for(uint32_t j=0;j<mem.memoryHeapCount;++j)
            if(mem.memoryHeaps[j].flags&VK_MEMORY_HEAP_DEVICE_LOCAL_BIT)
                largestDeviceHeap=std::max(largestDeviceHeap,uint64_t(mem.memoryHeaps[j].size));
        // Heap size is NOT free bytes. Leave at least 1.5 GiB nominal for
        // HDRq ~845MiB, AMaZE, GLES preview and driver allocations, with
        // actual vkAllocateMemory failures triggering exact two-slot fallback.
        const uint64_t reserve=1536ull*1024ull*1024ull;
        const uint64_t want=rawBytes*request.normals.size();
        residentEligible=largestDeviceHeap>=reserve &&
            want<=largestDeviceHeap-reserve;
    }
    std::unique_ptr<TwoSlotRaw16Uploader> inputs;
    bool resident=false;
    if(residentEligible) {
        try {
            inputs.reset(new TwoSlotRaw16Uploader(request.physical,request.device,
                inheritedUploads,request.width,request.height,
                uint32_t(request.normals.size())));
            resident=true;
        } catch(const std::exception& e) {
            // No submitted command has occurred yet: fully safe to retry
            // with exactly the proven two-slot GPU algorithm and all frames.
            __android_log_print(ANDROID_LOG_WARN,"Iris26873",
                "B_RESIDENT_ALLOC_FALLBACK normals=%zu why=%s",request.normals.size(),e.what());
        }
    }
    if(!inputs) inputs.reset(new TwoSlotRaw16Uploader(request.physical,request.device,
        inheritedUploads,request.width,request.height));
    const auto ref=inputs->referenceImage();
    const auto companion=inputs->companionImage();
    RealRawrRunRequest merge{};
    merge.physical=request.physical;
    merge.device=request.device;
    merge.inheritedQueue=request.inheritedQueue;
    merge.queueFamily=request.queueFamily;
    merge.width=request.width;merge.height=request.height;
    merge.effectiveCfa=request.localCfa;
    merge.referenceIndex=request.referenceIndex;
    merge.algorithm=request.algorithm;
    merge.inputLayout=resident?FrozenRawInputLayout::CaptureResident:FrozenRawInputLayout::FencedTwoSlot;
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
        const auto gpu=resident?inputs->imageAt(uint32_t(i)):
            ((i==request.referenceIndex)?ref:companion);
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
    auto now=[] {return std::chrono::steady_clock::now();};
    const auto uploadBegin=now();
    uint32_t uploadCalls=0;
    double uploadMs=0.0;
    if(resident) {
        try {
            // Every frozen direct RAW16 buffer remains borrowed until all
            // uploads are individually fence-complete. No post-shutter frame
            // collection or Camera2 exposure policy is touched.
            for(uint32_t i=0;i<raw.size();++i) {
                const auto t=now();
                inputs->uploadInto(i,i,raw);
                uploadMs+=std::chrono::duration<double,std::milli>(now()-t).count();
                ++uploadCalls;
            }
        } catch(...) {
            const VkResult idle=vkQueueWaitIdle(request.inheritedQueue);
            if(idle!=VK_SUCCESS) inputs->quarantineUnresolved();
            throw; // fence uncertainty: no silent alternate capture
        }
        merge.prepareNormal=[](std::uint32_t){}; // 4 passes reuse pinned views
    } else {
        merge.prepareNormal=[&](std::uint32_t index){
            const auto t=now();
            inputs->upload(index,request.referenceIndex,raw);
            uploadMs+=std::chrono::duration<double,std::milli>(now()-t).count();
            ++uploadCalls;
        };
    }
    // The pinned coordinator callback runs BEFORE it frees native GPU scratch;
    // the post-merge packer/AMaZE may ONLY consume its result synchronously.
    bool enteredConsumer=false;
    bool arenaRetry=false;
    // The B-OFF RAW color witness can revisit existing borrowed inputs only
    // AFTER the original merge has completed. Keep the original 26873 upload
    // count/latency receipt tied strictly to the original merge, not the
    // additional B-only evidence reads made inside the downstream consumer.
    uint32_t originalMergeUploads=0;
    double originalMergeUploadMs=0.;
    auto wrappedConsume=[&](const rawr::raw_gpu_pipeline::BurstRunResult& result,
                           const RealRawrRunRequest& frozen){
        enteredConsumer=true;
        originalMergeUploads=uploadCalls;
        originalMergeUploadMs=uploadMs;
        consume(result,frozen);
    };
    try {
        try {
            runRealPinnedRawrB(merge,wrappedConsume);
        } catch(const std::exception& error) {
            // A larger resident input set can starve HDRq's ~845MiB scratch
            // arena even though the input images themselves allocated. Retry
            // ONLY documented allocation failures, before any output consumer
            // was entered. The pinned native coordinator has already settled
            // its chunk fences, but the shared queue must also prove idle.
            const std::string why=error.what();
            const bool allocationFailure=
                why.find("multiframe arena: allocate")!=std::string::npos||
                why.find("multiframe arena: create image")!=std::string::npos||
                why.find("multiframe host buffer memory")!=std::string::npos||
                why.find("std::bad_alloc")!=std::string::npos;
            if(!resident||enteredConsumer||!allocationFailure)
                throw;
            if(vkQueueWaitIdle(request.inheritedQueue)!=VK_SUCCESS) {
                inputs->quarantineUnresolved();
                throw; // no device/fence proof: do not free images or retry
            }
            inputs.reset(); // no unresolved GPU use; free failed resident set
            inputs.reset(new TwoSlotRaw16Uploader(request.physical,request.device,
                inheritedUploads,request.width,request.height));
            resident=false;
            arenaRetry=true;
            merge.inputLayout=FrozenRawInputLayout::FencedTwoSlot;
            const auto safeRef=inputs->referenceImage();
            const auto safeCompanion=inputs->companionImage();
            for(std::size_t i=0;i<merge.normals.size();++i) {
                const auto safe=(i==request.referenceIndex)?safeRef:safeCompanion;
                merge.normals[i].borrowedRaw.image=safe.image;
                merge.normals[i].borrowedRaw.view=safe.view;
                merge.normals[i].borrowedRaw.format=safe.format;
            }
            uploadCalls=0;
            uploadMs=0.0;
            merge.prepareNormal=[&](std::uint32_t index){
                const auto t=now();
                inputs->upload(index,request.referenceIndex,raw);
                uploadMs+=std::chrono::duration<double,std::milli>(now()-t).count();
                ++uploadCalls;
            };
            __android_log_print(ANDROID_LOG_WARN,"Iris26873",
                "B_RESIDENT_SCRATCH_FALLBACK normals=%zu why=%s",
                raw.size(),error.what());
            runRealPinnedRawrB(merge,wrappedConsume); // exact math, all frames
        }
        const double uploadWallMs=std::chrono::duration<double,std::milli>(now()-uploadBegin).count();
        __android_log_print(ANDROID_LOG_INFO,"Iris26873",
            "B_GPU_INPUT mode=%s normals=%zu uploads=%u expected=%zu upload_ms=%.2f total_span_ms=%.2f retry=%d frame_drop=0",
            resident?"resident":"two_slot",raw.size(),originalMergeUploads,
            resident?raw.size():(size_t(1)+4u*(raw.size()-1u)),originalMergeUploadMs,uploadWallMs,
            arenaRetry?1:0);
        // Separate minimal sidecar receipt; never misattribute extra RAW
        // transfers to original HDR+ merge or frame-count degradation.
        if(uploadCalls>originalMergeUploads)
            __android_log_print(ANDROID_LOG_INFO,"Iris26887",
                "B_OFF_WITNESS_REUPLOAD normals=%zu extraUploads=%u extraUploadMs=%.2f",
                raw.size(),uploadCalls-originalMergeUploads,uploadMs-originalMergeUploadMs);
    }catch(...){
        // Every upstream chunk and upload uses a waited fence. Retain GPU
        // input allocations if the queue entered an unresolved state.
        const VkResult idle=vkQueueWaitIdle(request.inheritedQueue);
        if(idle!=VK_SUCCESS) inputs->quarantineUnresolved();
        throw;
    }
}
} // namespace iris26864
