// IRIS_26864_REAL_PINNED_B_GL_VULKAN_NATIVE_JNI_INTEROP
// This is included by the exact successful 26863 AMaZE JNI implementation,
// preserving its existing GL/AHB/fence helpers and original JNI entry point.
#include "Iris26864FrozenDirectRawrRunner.hpp"
#include "Iris26864NativeBridgeShaders.hpp"
#include "bridge/Iris26864HdrqCanonicalGpuBridge.hpp"
#include "bridge/Iris26887BOffRawPhaseDiversity.hpp"
#include "bridge/Iris26887BOffRawWitnessGlobalSeeds.hpp"
#include "Iris26864Wronski2xSingleOwnerBridge.hpp"
#include "raw_denoise/DenoisePipeline.hpp"
#include "iris26880_wavelet_precondition.h"
#include "iris26880_wavelet_atrous.h"
#include "iris26880_wavelet_threshold.h"
#include "iris26880_wavelet_backtransform.h"
#include "iris26880_wavelet_copy.h"
#include <android/log.h>
#include <algorithm>
#include <vector>
#include <cstring>
#include <limits>

namespace {
struct Iris26864LscGpu final {
    VkDevice device=VK_NULL_HANDLE;
    VkBuffer buffer=VK_NULL_HANDLE;
    VkDeviceMemory memory=VK_NULL_HANDLE;
    VkDeviceSize bytes=0;
    Iris26864LscGpu(VkPhysicalDevice physical,VkDevice d,const std::vector<float>& values):device(d) {
        // Never leak an allocated VkBuffer/VkDeviceMemory when a constructor
        // fails: its normal destructor will NOT run after a constructor throw.
        try {
        bytes=std::max<VkDeviceSize>(16u,values.size()*sizeof(float));
        VkBufferCreateInfo bi{};bi.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bi.size=bytes;bi.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
        bi.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        if(vkCreateBuffer(device,&bi,nullptr,&buffer)!=VK_SUCCESS)
            throw std::runtime_error("26864 physical LSC VkBuffer allocation failed");
        VkMemoryRequirements mr{};vkGetBufferMemoryRequirements(device,buffer,&mr);
        VkPhysicalDeviceMemoryProperties mp{};vkGetPhysicalDeviceMemoryProperties(physical,&mp);
        uint32_t type=UINT32_MAX;
        for(uint32_t i=0;i<mp.memoryTypeCount;++i)
            if((mr.memoryTypeBits&(1u<<i))&&
               (mp.memoryTypes[i].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|
                 VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==
                (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
                type=i;break;
            }
        if(type==UINT32_MAX)throw std::runtime_error("26864 no host coherent physical LSC memory");
        VkMemoryAllocateInfo ai{};ai.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize=mr.size;ai.memoryTypeIndex=type;
        if(vkAllocateMemory(device,&ai,nullptr,&memory)!=VK_SUCCESS ||
           vkBindBufferMemory(device,buffer,memory,0)!=VK_SUCCESS)
            throw std::runtime_error("26864 physical LSC GPU memory failed");
        void* ptr=nullptr;
        if(vkMapMemory(device,memory,0,bytes,0,&ptr)!=VK_SUCCESS||!ptr)
            throw std::runtime_error("26864 physical LSC map failed");
        const float identity[4]{1.f,1.f,1.f,1.f};
        std::memcpy(ptr,values.empty()?identity:values.data(),size_t(bytes));
        vkUnmapMemory(device,memory);
        } catch (...) {
            if (buffer) vkDestroyBuffer(device,buffer,nullptr);
            if (memory) vkFreeMemory(device,memory,nullptr);
            buffer=VK_NULL_HANDLE;memory=VK_NULL_HANDLE;
            throw;
        }
    }
    ~Iris26864LscGpu() {
        if(buffer)vkDestroyBuffer(device,buffer,nullptr);
        if(memory)vkFreeMemory(device,memory,nullptr);
    }
    Iris26864LscGpu(const Iris26864LscGpu&)=delete;
    Iris26864LscGpu& operator=(const Iris26864LscGpu&)=delete;
};
// RAWR wavelet compute descriptors are referenced by GPU work recorded on
// CommandSubmissionOwner. Its failure path can leave a submitted fence
// unresolved until its destructor; that owner outlives our scoped wavelet.
// Before releasing wavelet pipelines/scratch, settle the inherited queue.
// A device-lost/unresolved queue must retain those driver-owned allocations
// rather than turn an unknown GPU lifetime into a use-after-free. This guard
// applies ONLY to the new 26880 B wavelet resources.
template<class Resource> struct Iris26880WaitedVulkanRetire {
    VkQueue queue=VK_NULL_HANDLE;
    void operator()(Resource* resource) const noexcept {
        if(!resource)return;
        if(queue!=VK_NULL_HANDLE&&vkQueueWaitIdle(queue)==VK_SUCCESS){
            delete resource;
        }else{
            __android_log_print(ANDROID_LOG_ERROR,"Iris26880",
                "B_WAVELET_GPU_RESOURCE_QUARANTINE unresolved Vulkan queue; retaining resource");
        }
    }
};
// IRIS_26887_B_OFF_OPTIONAL_WITNESS_IMAGE_LIFETIME.
// A failed CommandSubmissionOwner fence wait can leave submitted GPU work
// unresolved. The optional RAW witness arena is declared AFTER that command
// owner, so ordinary unique_ptr destruction could free a live VkImage while
// the driver still owns its descriptors. Settle the SAME inherited queue
// before releasing these B-only images. If completion cannot be proven,
// quarantine them until the owning Vulkan device is torn down.
struct Iris26887WaitedWitnessArenaRetire {
    VkQueue queue=VK_NULL_HANDLE;
    void operator()(iris26864::VulkanImageArena* arena) const noexcept {
        if(!arena)return;
        if(queue!=VK_NULL_HANDLE&&vkQueueWaitIdle(queue)==VK_SUCCESS){
            delete arena;
        }else{
            __android_log_print(ANDROID_LOG_ERROR,"Iris26887",
                "B_OFF_WITNESS_IMAGE_QUARANTINE unresolved Vulkan queue; retaining images");
        }
    }
};
std::vector<float> iris26864ReadFloats(JNIEnv* e,jfloatArray v){
    if(!v)return {};
    const jsize n=e->GetArrayLength(v);
    if(n<0||n>4000000)throw std::invalid_argument("26864 invalid JNI float provenance size");
    std::vector<float> a(size_t(n),0.f);
    if(n)e->GetFloatArrayRegion(v,0,n,a.data());
    if(e->ExceptionCheck())throw std::runtime_error("26864 JNI float metadata read failed");
    return a;
}
void iris26864RunRealBGl(JNIEnv* env,AAssetManager* assets,jobjectArray javaNormals,
    jintArray javaStrides,jfloatArray javaExposure,jlongArray javaTimestamps,
    jfloatArray javaBlacks,jfloatArray javaWhites,jfloatArray javaWb,
    jfloatArray javaLsc,jint lscWidth,jint lscHeight,jint rawWidth,jint rawHeight,
    jint physicalCfa,jint cropX,jint cropY,jint fullSensorWidth,jint fullSensorHeight,
    jint referenceIndex,jboolean sr,jint outputRgbTexture,jint outputClipTexture,
    jlong physicalLensIdentity){
    if(!assets||!javaNormals||!javaStrides||!javaTimestamps||
       !javaExposure||!javaBlacks||!javaWhites||!javaWb||
       rawWidth<32||rawHeight<32||rawWidth>8192||rawHeight>8192||
       (rawWidth&1)||(rawHeight&1)||physicalCfa<0||physicalCfa>3||
       cropX<0||cropY<0||fullSensorWidth<rawWidth||fullSensorHeight<rawHeight||
       cropX>fullSensorWidth-rawWidth||cropY>fullSensorHeight-rawHeight||
       !outputRgbTexture||!outputClipTexture||outputRgbTexture==outputClipTexture||
       !physicalLensIdentity||lscWidth<0||lscHeight<0)
        throw std::invalid_argument("26864 invalid native B GPU/clip/JNI metadata");
    const jsize count=env->GetArrayLength(javaNormals);
    if(count<2||count>64||referenceIndex<0||referenceIndex>=count||
       env->GetArrayLength(javaStrides)!=count||
       env->GetArrayLength(javaExposure)!=count||
       env->GetArrayLength(javaTimestamps)!=count||
       env->GetArrayLength(javaBlacks)!=count*4||
       env->GetArrayLength(javaWhites)!=count||env->GetArrayLength(javaWb)!=3)
        throw std::invalid_argument("26864 mismatched frozen NORMAL JNI burst lengths");
    auto exposures=iris26864ReadFloats(env,javaExposure);
    auto blacks=iris26864ReadFloats(env,javaBlacks);
    auto whites=iris26864ReadFloats(env,javaWhites);
    auto gainsVec=iris26864ReadFloats(env,javaWb);
    auto lensVec=iris26864ReadFloats(env,javaLsc);
    if((lscWidth==0)!=(lscHeight==0)||
       (lscWidth!=0&&(lscWidth<2||lscHeight<2))||
       uint64_t(lscWidth)*lscHeight*4u!=lensVec.size())
        throw std::invalid_argument("26864 physical Camera2 LSC shape invalid");
    for(float x:lensVec)if(!std::isfinite(x)||x<=0.f||x>=64.f)
        throw std::invalid_argument("26864 invalid physical lens-shading gain");
    for(float x:gainsVec)if(!std::isfinite(x)||x<=0.f)
        throw std::invalid_argument("26864 invalid AMaZE white-balance gains");
    std::vector<jint> strides(size_t(count),0);
    std::vector<jlong> timestamps(size_t(count),0);
    env->GetIntArrayRegion(javaStrides,0,count,strides.data());
    env->GetLongArrayRegion(javaTimestamps,0,count,timestamps.data());
    if(env->ExceptionCheck())return;
    const uint32_t outWidth=uint32_t(rawWidth)*(sr?2u:1u);
    const uint32_t outHeight=uint32_t(rawHeight)*(sr?2u:1u);
    if(outWidth>16384u||outHeight>16384u)
        throw std::invalid_argument("26864 native B output exceeds physical GPU dimension");
    amaze::VulkanDeviceOwner device;
    const auto ctx=device.context();
    amaze::CommandSubmissionOwner commands(ctx.physicalDevice,ctx.device,
                                            device.queue(),ctx.queueFamilyIndex);
    amaze::PipelineConfig config{};
    config.width=outWidth;config.height=outHeight;
    const uint32_t localCfa=uint32_t(physicalCfa)^(uint32_t(cropX)&1u)^
                                    ((uint32_t(cropY)&1u)<<1u);
    config.pattern=static_cast<amaze::BayerPattern>(localCfa);
    config.inputMode=amaze::InputMode::PackedCfaRgba16fImage;
    config.tileSlots=16u;
    amaze::AmazePipeline amaze(ctx,amaze::makePinnedSpirvProvider(assets),config);
    ScopedAHB rgbAhb=createAhb(outWidth,outHeight,true);
    ScopedAHB clipAhb=createAhb(outWidth,outHeight,true);
    amaze::HardwareBufferImport rgb(ctx.physicalDevice,ctx.device,rgbAhb.get(),
                                    outWidth,outHeight,VK_IMAGE_USAGE_STORAGE_BIT);
    amaze::HardwareBufferImport clip(ctx.physicalDevice,ctx.device,clipAhb.get(),
                                     outWidth,outHeight,VK_IMAGE_USAGE_STORAGE_BIT);
    // Both AHB exports are new. Vulkan initializes them before their first GL
    // import, and the Vulkan->GL semaphore is signaled only after all writes.
    commands.execute([&](VkCommandBuffer cmd) {
        for(VkImage img:{rgb.image(),clip.image()})
            imageBarrier(cmd,img,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_GENERAL,
                ctx.queueFamilyIndex,VK_QUEUE_FAMILY_FOREIGN_EXT,0,0,
                VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
    });
    Iris26864LscGpu lsc(ctx.physicalDevice,ctx.device,lensVec);
    iris26864::FrozenDirectBRequest req{};
    req.physical=ctx.physicalDevice;req.device=ctx.device;req.inheritedQueue=device.queue();
    req.queueFamily=ctx.queueFamilyIndex;req.width=uint32_t(rawWidth);
    req.height=uint32_t(rawHeight);req.localCfa=localCfa;
    req.referenceIndex=uint32_t(referenceIndex);
    req.algorithm=sr?iris26864::RealBEngine::WronskiTrue2x:
                     iris26864::RealBEngine::HdrPlusFrequency;
    for(jsize i=0;i<count;++i){
        jobject b=env->GetObjectArrayElement(javaNormals,i);
        if(!b)throw std::invalid_argument("26864 missing direct RAW buffer");
        const auto* ptr=static_cast<const unsigned char*>(env->GetDirectBufferAddress(b));
        const jlong n=env->GetDirectBufferCapacity(b);
        env->DeleteLocalRef(b);
        if(!ptr||n<=0||strides[size_t(i)]<rawWidth*2||
           uint64_t(n)<uint64_t(rawHeight-1)*strides[size_t(i)]+rawWidth*2u)
            throw std::invalid_argument("26864 invalid direct RAW16 pointer, bytes or stride");
        iris26864::FrozenDirectNormal f{};
        f.borrowed={ptr,size_t(n),uint32_t(strides[size_t(i)]),uint32_t(rawWidth),
                    uint32_t(rawHeight),uint64_t(timestamps[size_t(i)])};
        f.physicalLensIdentity=uint64_t(physicalLensIdentity);
        f.exposureProduct=exposures[size_t(i)];f.whiteLevel=whites[size_t(i)];
        for(uint32_t k=0;k<4u;++k)f.blackByPhase[k]=blacks[size_t(i)*4u+k];
        f.whiteBalance={gainsVec[0],gainsVec[1],gainsVec[2]};
        req.normals.push_back(f);
    }
    // B OFF is independent of optional A DNG and uses ONLY original NORMAL
    // sensor RAW16. Coarse seeds authorize NOTHING; every GPU tile and pixel
    // must independently verify physical R/G/B support before color changes.
    std::vector<iris26887::Raw16Frame> bOffOriginalRaw;
    std::vector<iris26887::RawColorSeed> bOffCoarse;
    if(!sr){
        bOffOriginalRaw.reserve(req.normals.size());
        for(const auto& normal:req.normals){
            iris26887::Raw16Frame f{};
            f.bytes=normal.borrowed.source;f.byteCount=normal.borrowed.bytes;
            f.stride=normal.borrowed.rowStride;f.width=normal.borrowed.width;
            f.height=normal.borrowed.height;f.white=normal.whiteLevel;
            f.exposure=normal.exposureProduct;
            for(size_t k=0;k<4u;++k)f.black[k]=normal.blackByPhase[k];
            bOffOriginalRaw.push_back(f);
        }
        bOffCoarse=iris26887::estimateOriginalRawSensorSeeds(
            bOffOriginalRaw,size_t(referenceIndex),localCfa);
    }
    iris26864::VulkanImageArena surfaces(ctx.physicalDevice,ctx.device,
                                VkDeviceSize(outWidth)*outHeight*12ull+(16ull<<20u));
    surfaces.allocate(outWidth/2u,outHeight/2u,VK_FORMAT_R16G16B16A16_SFLOAT,
                      VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    surfaces.allocate(outWidth/2u,outHeight/2u,VK_FORMAT_R16_UINT,
                      VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    const auto packed=surfaces.at(0), rawClip=surfaces.at(1);
    // 4 bytes per physical RAW output pixel (~48 MiB at 3072x4096), NOT a
    // second 50MP RGB allocation; shifts are ~0.2 MiB at 32-site tiles.
    // A low-memory device fails this OPTIONAL evidence stage closed: its JPEG
    // remains the inherited successful B output with no unsafe color rewrite.
    size_t bOffWitnessSlot=SIZE_MAX,bOffShiftSlot=SIZE_MAX;
    // Independent optional arena: partial allocation failure frees all
    // witness resources and cannot retain 48 MiB needed by AMaZE/JPEG.
    std::unique_ptr<iris26864::VulkanImageArena,
        Iris26887WaitedWitnessArenaRetire> bOffArena(nullptr,{device.queue()});
    bool bOffWitnessAllocated=false;
    // A full RGB witness needs at least two physical observations of each
    // Bayer channel. No 48-MiB allocation on flat, ambiguous or short bursts
    // which have fewer than six independently registered original frames.
    const size_t seedCount=std::count_if(bOffCoarse.begin(),bOffCoarse.end(),
        [](const iris26887::RawColorSeed& seed){return seed.valid;});
    // Important: do NOT allocate the extra ~48 MiB sidecar before HDR+ runs.
    // Its scratch arena needs memory first. Optional color evidence is
    // allocated only AFTER the pinned merge has completed successfully.
    // Avoid optional witness allocation on equal-phase bursts: with the
    // current exact-integer tile acceptance there is not enough independent
    // physical RGB information at ANY pixel, regardless of GPU speed.
    const bool bOffWitnessPotential=(!sr&&seedCount>=6u&&
        iris26887::canSupplyTwiceEachBayerColor(bOffCoarse,localCfa));
    auto hdrqShader=sr?nullptr:iris26864::makeRealHdrqCfaBridge(ctx.device);
    auto wronskiShader=sr?iris26864::makeRealWronskiCfaBridge(ctx.device):nullptr;
    // The evidence shader exists ONLY for Super Res ON; under failure,
    // quarantine its pipeline until the inherited queue is actually idle.
    std::unique_ptr<iris26864::VulkanKernelExecutor,
        Iris26880WaitedVulkanRetire<iris26864::VulkanKernelExecutor>>
        bOnChromaEvidence(nullptr,{device.queue()});
    if(sr) bOnChromaEvidence.reset(
        iris26864::makeRealWronskiChromaGuide(ctx.device).release());
    // B OFF four independent source-of-truth compute kernels. Each separate
    // descriptor set remains owned through CommandSubmissionOwner's fence.
    using BOffKernel=std::unique_ptr<iris26864::VulkanKernelExecutor,
        Iris26880WaitedVulkanRetire<iris26864::VulkanKernelExecutor>>;
    BOffKernel bOffTile(nullptr,{device.queue()}),bOffAcc(nullptr,{device.queue()}),
               bOffFinish(nullptr,{device.queue()}),bOffReconcile(nullptr,{device.queue()});
    auto clipShader=iris26864::makeRealSensorClipToGlBridge(ctx.device);
    // Capture scope is the GPU lifetime. The real RAWR original tiled wavelet
    // and its final copy descriptor/pipeline are created before command record
    // and cannot be destroyed until CommandSubmissionOwner's fence completes.
    // Not enabled for HDRq (Super Res OFF) or any other experiment.
    std::unique_ptr<raw_denoise::DenoisePipeline,
        Iris26880WaitedVulkanRetire<raw_denoise::DenoisePipeline>>
        bWavelet(nullptr,{device.queue()});
    std::unique_ptr<iris26864::VulkanKernelExecutor,
        Iris26880WaitedVulkanRetire<iris26864::VulkanKernelExecutor>>
        bWaveletCopy(nullptr,{device.queue()});
    bool publishedClip=false;
    // This callback executes while RAWR still owns the exact completed GPU
    // merge scratch. The B engines cannot return an alias of inherited A RGB.
    iris26864::runRealRawrFromFrozenDirectNormals(req,commands,[&](
        const rawr::raw_gpu_pipeline::BurstRunResult& result,
        const iris26864::RealRawrRunRequest& original){
        // IRIS_26887_B_OFF_PIXEL_LOCAL_ORIGINAL_RAW_COLOR_WITNESS.
        // The original RAWR merge has finished and its GPU scratch is held.
        // In fenced-two-slot mode, the existing upload callback safely
        // revisits each original DirectByteBuffer after the pinned merge;
        // resident mode reuses its already loaded unique immutable views.
        // Extra uploads MUST be accounted for separately in source receipts.
        // Optional sidecar creation is deferred until AFTER HDR+ succeeds;
        // a low-memory device must never sacrifice primary RAW reconstruction
        // or optional-DNG independence to make room for this color witness.
        if(bOffWitnessPotential){
            try {
                bOffArena.reset(new iris26864::VulkanImageArena(
                    ctx.physicalDevice,ctx.device,
                    VkDeviceSize(outWidth)*outHeight*6ull+(4ull<<20u)));
                bOffWitnessSlot=bOffArena->allocate(outWidth,outHeight,VK_FORMAT_R32_UINT,
                    VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT);
                bOffShiftSlot=bOffArena->allocate((outWidth+31u)/32u,(outHeight+31u)/32u,
                    VK_FORMAT_R32G32B32A32_SINT,VK_IMAGE_USAGE_STORAGE_BIT);
                bOffWitnessAllocated=true;
            } catch (const std::exception& error) {
                bOffArena.reset(); // free any successful partial allocation
                bOffWitnessSlot=SIZE_MAX;bOffShiftSlot=SIZE_MAX;
                __android_log_print(ANDROID_LOG_WARN,"Iris26887",
                    "B_OFF_RAW_WITNESS_NO_MEMORY inherited HDRQ fallback: %s",error.what());
            }
            if(bOffWitnessAllocated){
                try {
                    bOffTile.reset(iris26864::makeRealBOffRawTileRefine(ctx.device).release());
                    bOffAcc.reset(iris26864::makeRealBOffRawAccumulate(ctx.device).release());
                    bOffFinish.reset(iris26864::makeRealBOffRawFinalize(ctx.device).release());
                    bOffReconcile.reset(iris26864::makeRealBOffStrictWitnessReconcile(ctx.device).release());
                } catch (const std::exception& error) {
                    // No evidence has been dispatched yet. Fail this optional
                    // color guide closed, preserving the successful HDRQ JPEG.
                    __android_log_print(ANDROID_LOG_WARN,"Iris26887",
                        "B_OFF_WITNESS_PIPELINE_UNAVAILABLE fallback: %s",error.what());
                    bOffReconcile.reset();bOffFinish.reset();bOffAcc.reset();bOffTile.reset();
                    bOffArena.reset(); // no GPU use started, free optional arena
                    bOffWitnessSlot=SIZE_MAX;bOffShiftSlot=SIZE_MAX;
                    bOffWitnessAllocated=false;
                }
            }
            if(bOffWitnessAllocated){
                // Layout initialization and its transfer-clear are separate
                // fence-waited submissions, preventing a COMPUTE->TRANSFER race.
                commands.execute([&](VkCommandBuffer cmd){
                    bOffArena->recordInitialGeneralTransitions(cmd);
                });
                commands.execute([&](VkCommandBuffer cmd){
                    VkClearColorValue zero{};
                    VkImageSubresourceRange whole{VK_IMAGE_ASPECT_COLOR_BIT,0u,1u,0u,1u};
                    vkCmdClearColorImage(cmd,bOffArena->at(bOffWitnessSlot).image,
                        VK_IMAGE_LAYOUT_GENERAL,&zero,1u,&whole);
                    VkMemoryBarrier cleared{};cleared.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
                    cleared.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
                    cleared.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
                    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,
                        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1u,&cleared,0,nullptr,0,nullptr);
                });
            }
        }
        bool bOffWitnessReady=false;
        uint32_t bOffEvidenceFrames=0;
        if(bOffWitnessAllocated && bOffCoarse.size()==original.normals.size() &&
           bOffTile && bOffAcc && bOffFinish && bOffReconcile){
            const auto state=bOffArena->at(bOffWitnessSlot), shifts=bOffArena->at(bOffShiftSlot);
            const auto refView=original.normals[size_t(referenceIndex)].borrowedRaw.view;
            for(size_t i=0;i<original.normals.size();++i){
                if(!bOffCoarse[i].valid)continue;
                const auto& n=original.normals[i];
                const auto& ref=original.normals[size_t(referenceIndex)];
                if(!(n.exposureProduct>0.f&&ref.exposureProduct>0.f)||
                   std::abs(n.exposureProduct/ref.exposureProduct-1.f)>.025f)continue;
                // Original 26873 fenced RAW16 upload owner and receipt;
                // no new camera frame collection, no change to merge count.
                // The reference image is permanently pinned in slot 0 by
                // the successful HDR+ merge. Only companions may occupy the
                // recycled two-slot upload and therefore need re-uploading.
                if(i!=size_t(referenceIndex)) original.prepareNormal(uint32_t(i));
                const VkImageView view=n.borrowedRaw.view;
                // Missing OPTIONAL evidence must never fail an otherwise
                // successful B HDR+ JPEG. The incomplete per-pixel witness
                // remains invalid and cannot authorize a color correction.
                if(!view||!refView){
                    __android_log_print(ANDROID_LOG_WARN,"Iris26887",
                        "B_OFF_RAW_WITNESS_SOURCE_MISSING frame=%zu no_color_evidence",i);
                    continue;
                }
                struct alignas(16) TileParams {
                    uint32_t extent[4];int32_t initial[4];
                    float referenceBlack[4];float companionBlack[4];float values[4];
                } tile{};
                static_assert(sizeof(TileParams)==80u,"26887 tile push ABI");
                tile.extent[0]=outWidth;tile.extent[1]=outHeight;
                tile.extent[2]=32u;tile.extent[3]=localCfa;
                tile.initial[0]=bOffCoarse[i].dx;tile.initial[1]=bOffCoarse[i].dy;
                for(uint32_t c=0;c<4u;++c){
                    tile.referenceBlack[c]=ref.phaseBlack[c];
                    tile.companionBlack[c]=n.phaseBlack[c];
                }
                tile.values[0]=ref.sensorWhite;tile.values[1]=n.sensorWhite;
                tile.values[2]=ref.exposureProduct;tile.values[3]=n.exposureProduct;
                struct alignas(16) AccParams {
                    uint32_t extent[4];float black[4],refBlack[4],exposure[4];
                    uint32_t flags[4];
                } acc{};
                static_assert(sizeof(AccParams)==80u,"26887 accumulation push ABI");
                acc.extent[0]=outWidth;acc.extent[1]=outHeight;
                acc.extent[2]=32u;acc.extent[3]=localCfa;
                for(uint32_t c=0;c<4u;++c){
                    acc.black[c]=n.phaseBlack[c];acc.refBlack[c]=ref.phaseBlack[c];
                }
                for(int c=0;c<4;++c)acc.exposure[c]=tile.values[c];
                acc.flags[0]=uint32_t(i==size_t(referenceIndex));
                acc.flags[1]=1u;acc.flags[2]=uint32_t(i);
                commands.execute([&](VkCommandBuffer cmd){
                    if(i!=size_t(referenceIndex)){
                        std::vector<iris26864::BoundResource> b;
                        for(const auto& [slot,imageView]:{
                            std::pair<uint32_t,VkImageView>{0u,refView},
                            {1u,view},{2u,shifts.view}}){
                            iris26864::BoundResource t{};t.binding=slot;
                            t.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;t.imageView=imageView;
                            b.push_back(t);
                        }
                        bOffTile->record(cmd,b,&tile,sizeof(tile),shifts.width,shifts.height);
                        VkMemoryBarrier shiftReady{};
                        shiftReady.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
                        shiftReady.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
                        shiftReady.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;
                        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1u,&shiftReady,
                            0,nullptr,0,nullptr);
                    }
                    std::vector<iris26864::BoundResource> b;
                    for(const auto& [slot,imageView]:{
                            std::pair<uint32_t,VkImageView>{0u,view},
                            {1u,refView},{2u,shifts.view},{3u,state.view}}){
                        iris26864::BoundResource t{};t.binding=slot;
                        t.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;t.imageView=imageView;
                        b.push_back(t);
                    }
                    bOffAcc->record(cmd,b,&acc,sizeof(acc),outWidth,outHeight);
                });
                ++bOffEvidenceFrames;
            }
            if(bOffEvidenceFrames>=6u){
                struct FinishArgs{uint32_t width,height;};
                FinishArgs a{outWidth,outHeight};
                static_assert(sizeof(FinishArgs)==8u,"26887 finalize push ABI");
                commands.execute([&](VkCommandBuffer cmd){
                    iris26864::BoundResource b{};b.binding=0u;
                    b.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;b.imageView=state.view;
                    bOffFinish->record(cmd,{b},&a,sizeof(a),outWidth,outHeight);
                });
                bOffWitnessReady=true;
            }
        }
        // If frame filtering leaves too few independent observations, the
        // optional evidence will never be read by the AMaZE path. Retire its
        // kernels and release its 48-MiB sidecar NOW, not after AMaZE/JPEG.
        // CommandSubmissionOwner::execute synchronously waits every preceding
        // optional compute submission's fence before reaching this block.
        // Never destroy a descriptor/image while a submitted command is live.
        if(bOffWitnessAllocated && !bOffWitnessReady){
            bOffFinish.reset();bOffAcc.reset();bOffTile.reset();bOffReconcile.reset();
            bOffArena.reset();
            bOffWitnessSlot=SIZE_MAX;bOffShiftSlot=SIZE_MAX;
            bOffWitnessAllocated=false;
            __android_log_print(ANDROID_LOG_INFO,"Iris26887",
                "B_OFF_RAW_WITNESS_INSUFFICIENT_LOCAL_SUPPORT optional GPU memory released before AMaZE");
        }
        __android_log_print(ANDROID_LOG_INFO,"Iris26887",
            "B_OFF_PIXEL_RAW_WITNESS prepared=%d sourceFrames=%u selectedFrames=%zu",
            int(bOffWitnessReady),bOffEvidenceFrames,original.normals.size());
        amaze::LinearRgbImage output{};
        output.image=rgb.image();output.view=rgb.view();
        output.format=VK_FORMAT_R16G16B16A16_SFLOAT;
        output.layout=VK_IMAGE_LAYOUT_GENERAL;
        output.width=outWidth;output.height=outHeight;
        auto release=ScopeVkSemaphore(ctx.device,createGlExportableSemaphore(ctx.device));
        commands.execute([&](VkCommandBuffer cmd) {
            // Match the exact successful 26863 AHB foreign-queue acquire
            // before any compute imageStore. First initialization released
            // these new AHBs; the final barrier below releases them to GLES.
            for (VkImage image : {rgb.image(),clip.image()})
                imageBarrier(cmd,image,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_GENERAL,
                    VK_QUEUE_FAMILY_FOREIGN_EXT,ctx.queueFamilyIndex,0,
                    VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                    VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            surfaces.recordInitialGeneralTransitions(cmd);
            if(sr){
                iris26864::wronski2x::SingleOwner2xFrames f{};
                f.geometry={uint32_t(rawWidth),uint32_t(rawHeight),outWidth,outHeight,
                    uint32_t(physicalCfa),uint32_t(cropX),uint32_t(cropY),
                    uint32_t(fullSensorWidth),uint32_t(fullSensorHeight),
                    whites[size_t(referenceIndex)],0.995f,
                    {blacks[size_t(referenceIndex)*4],blacks[size_t(referenceIndex)*4+1],
                     blacks[size_t(referenceIndex)*4+2],blacks[size_t(referenceIndex)*4+3]}};
                f.lsc.width=uint32_t(lscWidth);f.lsc.height=uint32_t(lscHeight);
                for(size_t j=0;j<lensVec.size();j+=4u)
                    f.lsc.texels.push_back({lensVec[j],lensVec[j+1],lensVec[j+2],lensVec[j+3]});
                f.mergedCameraRgb={uint64_t(result.output),uint64_t(result.outputView),
                    outWidth,outHeight,uint32_t(VK_FORMAT_R16G16B16A16_SFLOAT)};
                const auto reference=original.normals[size_t(referenceIndex)].borrowedRaw;
                f.originalReferenceRaw={uint64_t(reference.image),uint64_t(reference.view),
                    uint32_t(rawWidth),uint32_t(rawHeight),uint32_t(VK_FORMAT_R16_UINT)};
                f.packedCfa={uint64_t(packed.image),uint64_t(packed.view),outWidth/2u,
                    outHeight/2u,uint32_t(VK_FORMAT_R16G16B16A16_SFLOAT)};
                f.sensorClip={uint64_t(rawClip.image),uint64_t(rawClip.view),outWidth/2u,
                    outHeight/2u,uint32_t(VK_FORMAT_R16_UINT)};
                f.amazeRgb={uint64_t(output.image),uint64_t(output.view),outWidth,outHeight,
                            uint32_t(VK_FORMAT_R16G16B16A16_SFLOAT)};
                f.lscBuffer=lsc.buffer;f.lscBytes=lsc.bytes;
                f.whiteBalance={gainsVec[0],gainsVec[1],gainsVec[2]};
                f.rawrBurstNoiseFitted=result.noiseEstimated;
                f.burstNormalCount=result.frameCount;
                // Original pinned RAWR MfsrCaptureJob: use fitted RAW
                // variance at the two GREEN Bayer sites, then divide by
                // the NORMAL burst frame count actually merged. Its wavelet
                // accepts a camera-linear, pre-white-balance noise model.
                if(result.noiseEstimated && result.frameCount>0u){
                    const auto& noise=result.estimatedNoise;
                    const uint32_t green0=(localCfa==1u||localCfa==2u)?0u:1u;
                    const uint32_t green1=(localCfa==1u||localCfa==2u)?3u:2u;
                    const float invCount=1.f/float(result.frameCount);
                    f.burstGreenNoisePerMergedSample={
                        .5f*(noise.slopeBySite[green0]+noise.slopeBySite[green1])*invCount,
                        .5f*(noise.offsetBySite[green0]+noise.offsetBySite[green1])*invCount};
                }
                const auto receipt=iris26864::wronski2x::recordWronski2xToAmaze(
                    cmd,f,*wronskiShader,*bOnChromaEvidence,amaze);
                if(!bOnChromaEvidence||!receipt.preAmazeLscStageComplete||receipt.legacyPostAmazeLscPermitted||
                   receipt.legacyIrisChromaDenoisePermitted||!receipt.image)
                    throw std::runtime_error("26864 Wronski LSC/clip ownership receipt incomplete");
                // RAWR MfsrCaptureJob pre-WB wavelet: AMaZE export shader
                // DIVIDES by its internal WB gain and therefore outputs
                // camera-linear RGB into the native-owned RGB AHB. Keep that
                // exact camera domain; never reapply WB or denoise luminance.
                // RAWR merge scratch (output) has completed both earlier
                // consumers (CFA packer and 26885 B-ON chroma guide). Reuse it as denoised destination:
                // no second 50MP RGBA16F Vulkan allocation. Never alias
                // source and dest; both are RGBA16F storage GENERAL images.
                // RAWR's original MfsrCaptureJob expressly refuses the
                // seven-scale VST when the burst fit is absent, a<=0 or b<0.
                // Calling it with zero a divides by sqrt(a) in the ORIGINAL
                // precondition shader, contaminating the entire 50MP output
                // with invalid pixels. Preserve the completed original
                // Wronski fallback-chroma/merge path rather than inventing a
                // Camera2 noise profile, dropping the capture or generating
                // NaNs. A single capture-level warning makes the bypass
                // explicit (no silent fallback/no new denoiser).
                const bool measuredWaveletNoise = f.rawrBurstNoiseFitted &&
                    f.burstNormalCount>0u &&
                    std::isfinite(f.burstGreenNoisePerMergedSample[0]) &&
                    f.burstGreenNoisePerMergedSample[0]>0.f &&
                    std::isfinite(f.burstGreenNoisePerMergedSample[1]) &&
                    f.burstGreenNoisePerMergedSample[1]>=0.f;
                if(measuredWaveletNoise){
                    // Only instantiate the optional original GPU wavelet after a
                    // valid measured RAW-burst fit. Missing-fit Wronski
                    // fallback must never be blocked by unused wavelet setup.
                    auto pinnedSpv=[](const unsigned char* data,size_t size)->raw_denoise::DenoiseSpirv{
                        if(!data||size<84u||(size%4u)!=0u||
                           (reinterpret_cast<uintptr_t>(data)%alignof(uint32_t))!=0u||
                           reinterpret_cast<const uint32_t*>(data)[0]!=0x07230203u)
                            throw std::runtime_error("26880 pinned RAWR wavelet real SPIR-V missing or invalid");
                        return {reinterpret_cast<const uint32_t*>(data),size/sizeof(uint32_t)};
                    };
                    raw_denoise::DenoiseShaders sh{};
                    sh.precondition=pinnedSpv(iris26880_wavelet_precondition_spv,
                                             iris26880_wavelet_precondition_spv_size);
                    sh.atrous=pinnedSpv(iris26880_wavelet_atrous_spv,
                                        iris26880_wavelet_atrous_spv_size);
                    sh.threshold=pinnedSpv(iris26880_wavelet_threshold_spv,
                                           iris26880_wavelet_threshold_spv_size);
                    sh.backtransform=pinnedSpv(iris26880_wavelet_backtransform_spv,
                                               iris26880_wavelet_backtransform_spv_size);
                    bWavelet.reset(new raw_denoise::DenoisePipeline(ctx.physicalDevice,ctx.device,sh));
                    const auto copy=pinnedSpv(iris26880_wavelet_copy_spv,iris26880_wavelet_copy_spv_size);
                    iris26864::ShaderBinary program{};
                    program.words=copy.words;program.wordCount=copy.wordCount;
                    program.workgroupX=16u;program.workgroupY=16u;program.workgroupZ=1u;
                    bWaveletCopy.reset(new iris26864::VulkanKernelExecutor(ctx.device,
                        program,std::vector<iris26864::ComputeBinding>{
                            {0,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE},{1,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}},
                        8u,1u));

                if(!bWavelet||!bWaveletCopy||!result.output||!result.outputView||
                   result.output==rgb.image()||result.outputView==rgb.view()||
                   result.outputFormat!=VK_FORMAT_R16G16B16A16_SFLOAT||
                   result.outputExtent.width!=outWidth||result.outputExtent.height!=outHeight)
                    throw std::runtime_error("26880 real pre-WB RAWR wavelet output ownership invalid");
                VkMemoryBarrier waveletRead{};
                waveletRead.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
                waveletRead.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
                waveletRead.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
                vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                    VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&waveletRead,0,nullptr,0,nullptr);
                raw_denoise::DenoiseParams params{};
                params.strength=1.f;
                params.shadows=1.f;
                params.noiseA=f.burstGreenNoisePerMergedSample[0];
                params.noiseB=f.burstGreenNoisePerMergedSample[1];
                // RAWR WB-adaptive Y0U0V0 transform expects normalized
                // gains green=1; the source remains camera-linear/un-WBed.
                params.whiteBalance={gainsVec[0]/gainsVec[1],1.f,
                                     gainsVec[2]/gainsVec[1]};
                params.maxScale=7;
                params.forceY=0.f; // Chroma-only; preserve fine luminance
                params.forceUv=.75f;
                params.tileSize=1536u;
                bWavelet->record(cmd,rgb.view(),result.outputView,outWidth,outHeight,params);
                // The original wavelet writes output into RAWR's merged
                // scratch. Transfer it to Iris's existing RGB AHB with an
                // explicit storage-image compute copy (AHB lacks TRANSFER_DST).
                VkMemoryBarrier copyRead{};
                copyRead.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
                copyRead.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT|VK_ACCESS_TRANSFER_WRITE_BIT;
                copyRead.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
                vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT|
                    VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                    0,1,&copyRead,0,nullptr,0,nullptr);
                std::vector<iris26864::BoundResource> rb;
                for(const auto pair: {std::pair<uint32_t,VkImageView>{0u,result.outputView},
                                      {1u,rgb.view()}}){
                    iris26864::BoundResource b{};
                    b.binding=pair.first;b.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
                    b.imageView=pair.second;rb.push_back(b);
                }
                const uint32_t copyExtent[2]{outWidth,outHeight};
                bWaveletCopy->record(cmd,rb,copyExtent,sizeof(copyExtent),outWidth,outHeight);
                } else {
                    __android_log_print(ANDROID_LOG_WARN,"Iris26880",
                        "B_WAVELET_BURST_FIT_UNAVAILABLE active original RAWR Wronski merge/fallback; "
                        "no valid wavelet noise fit (estimated=%d, frames=%u, a=%g, b=%g)",
                        int(f.rawrBurstNoiseFitted),f.burstNormalCount,
                        double(f.burstGreenNoisePerMergedSample[0]),
                        double(f.burstGreenNoisePerMergedSample[1]));
                }
            }else{
                iris26864::HdrqCanonicalGpuFrame f{};
                f.cfg.width=uint32_t(rawWidth);f.cfg.height=uint32_t(rawHeight);
                f.cfg.originX=uint32_t(cropX);f.cfg.originY=uint32_t(cropY);
                f.cfg.fullSensorWidth=uint32_t(fullSensorWidth);
                f.cfg.fullSensorHeight=uint32_t(fullSensorHeight);
                f.cfg.pattern=localCfa;f.cfg.lscWidth=uint32_t(lscWidth);
                f.cfg.lscHeight=uint32_t(lscHeight);f.cfg.clippingThreshold=0.995f;
                for(uint32_t j=0;j<4u;++j){
                    const auto b=blacks[size_t(referenceIndex)*4u+j];
                    f.cfg.blackPhase[j]=b;f.cfg.inverseRangePhase[j]=1.f/(whites[size_t(referenceIndex)]-b);
                }
                f.physicalSensorPattern=uint32_t(physicalCfa);
                f.r32CfaImage=result.cfaImage;f.r32CfaView=result.cfaView;
                f.rawReferenceR16uView=original.normals[size_t(referenceIndex)].borrowedRaw.view;
                f.packedRgba16fImage=packed.image;f.packedRgba16fView=packed.view;
                f.clipR16uView=rawClip.view;
                f.camera2LscBuffer=lsc.buffer;f.camera2LscBytes=lsc.bytes;
                iris26864::recordCanonicalCfaForAmaze(cmd,*hdrqShader,f);
                amaze::PackedCfaImageView packedInput{};
                packedInput.image=packed.image;packedInput.view=packed.view;
                packedInput.width=outWidth/2u;packedInput.height=outHeight/2u;
                packedInput.rawWidth=outWidth;packedInput.rawHeight=outHeight;
                packedInput.pattern=static_cast<amaze::BayerPattern>(localCfa);
                packedInput.format=VK_FORMAT_R16G16B16A16_SFLOAT;
                packedInput.layout=VK_IMAGE_LAYOUT_GENERAL;
                amaze.record(cmd,packedInput,output,{gainsVec[0],gainsVec[1],gainsVec[2]});
                if(bOffWitnessReady){
                    // Strict color-only reconciliation from physically measured
                    // R/G/B at the SAME sensor scene point, repeated twice.
                    // The R32UI marker is 0 for any unverified pixel, so no
                    // color is modified there. No extra 50MP RGB allocation.
                    VkMemoryBarrier ready{};
                    ready.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
                    ready.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
                    ready.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
                    vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1u,&ready,
                        0,nullptr,0,nullptr);
                    struct alignas(16) ReconcileArgs {
                        uint32_t imageAndLsc[4];uint32_t geometry[4];
                        uint32_t flags[4];float wb[4];
                    } a{};
                    static_assert(sizeof(ReconcileArgs)==64u,"26887 WB witness push ABI");
                    a.imageAndLsc[0]=outWidth;a.imageAndLsc[1]=outHeight;
                    a.imageAndLsc[2]=uint32_t(lscWidth);a.imageAndLsc[3]=uint32_t(lscHeight);
                    a.geometry[0]=uint32_t(fullSensorWidth);
                    a.geometry[1]=uint32_t(fullSensorHeight);
                    a.geometry[2]=uint32_t(cropX);a.geometry[3]=uint32_t(cropY);
                    a.flags[0]=1u;
                    for(uint32_t j=0;j<3u;++j)a.wb[j]=gainsVec[j];
                    a.wb[3]=1.f;
                    std::vector<iris26864::BoundResource> b;
                    for(const auto& [slot,imageView]:{
                            std::pair<uint32_t,VkImageView>{0u,rgb.view()},
                            {1u,bOffArena->at(bOffWitnessSlot).view}}){
                        iris26864::BoundResource d{};d.binding=slot;
                        d.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;d.imageView=imageView;
                        b.push_back(d);
                    }
                    iris26864::BoundResource l{};l.binding=2u;
                    l.type=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;l.buffer=lsc.buffer;
                    l.bufferRange=lsc.bytes;b.push_back(l);
                    bOffReconcile->record(cmd,b,&a,sizeof(a),outWidth,outHeight);
                }
            }
            // The sidecar is computed from ORIGINAL sensor clip bits before
            // pre-AMaZE LSC. Expand into the full-resolution Iris clip-owner
            // surface rather than silently discarding its 4 CFA bits.
            struct ClipArgs{uint32_t width,height,cfa,strict;};
            const ClipArgs args{outWidth,outHeight,localCfa,1u};
            static_assert(sizeof(ClipArgs)==16u, "26864 sensor clip real SPIR-V push ABI");
            // Complete the original packed-sensor-clip producer before any
            // Vulkan compute invocation reads it. This is not a demosaic or
            // post-LSC saturation-derived mask.
            VkMemoryBarrier clipRead{};
            clipRead.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            clipRead.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
            clipRead.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;
            vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&clipRead,0,nullptr,0,nullptr);
            std::vector<iris26864::BoundResource> bindings;
            for(auto [slot,view]:{std::pair<uint32_t,VkImageView>{0u,rawClip.view},
                    {1u,clip.view()}}){
                iris26864::BoundResource b{};b.binding=slot;
                b.type=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;b.imageView=view;
                bindings.push_back(b);
            }
            clipShader->record(cmd,bindings,&args,sizeof(args),outWidth,outHeight);
            for(VkImage img:{rgb.image(),clip.image()})
                imageBarrier(cmd,img,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_GENERAL,
                    ctx.queueFamilyIndex,VK_QUEUE_FAMILY_FOREIGN_EXT,
                    VK_ACCESS_SHADER_WRITE_BIT,0,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                    VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
        },VK_NULL_HANDLE,release.semaphore);
        ScopedNativeFd glFence=exportVulkanFenceToGl(ctx.device,release.semaphore);
        waitCurrentGlOnVulkanFence(std::move(glFence));
        publishedClip=true;
    });
    if(!publishedClip)throw std::runtime_error("26864 original sensor clip not GPU-generated/GL-published");
    GlBufferImage glRgb(rgbAhb.get());GlBufferImage glClip(clipAhb.get());
    blitTexture(glRgb.texture,GLuint(outputRgbTexture),outWidth,outHeight);
    blitTexture(glClip.texture,GLuint(outputClipTexture),outWidth,outHeight);
    glFlush();glFinish();
}
} // namespace
extern "C" JNIEXPORT void JNICALL
Java_com_hinnka_mycamera_processor_GlesIris26864NativeRawr_nativeExecuteGpu(
    JNIEnv* env,jclass,jobject javaAssets,jobjectArray normals,
    jintArray strides,jfloatArray exposures,jlongArray timestamps,
    jfloatArray blacks,jfloatArray whites,jfloatArray wb,
    jfloatArray lsc,jint lscWidth,jint lscHeight,
    jint rawWidth,jint rawHeight,jint physicalCfa,jint cropX,jint cropY,
    jint fullSensorWidth,jint fullSensorHeight,jint referenceIndex,
    jboolean sr,jint outputRgbTexture,jint outputClipTexture,
    jlong physicalLensIdentity){
    try {
        AAssetManager* assets=javaAssets?AAssetManager_fromJava(env,javaAssets):nullptr;
        iris26864RunRealBGl(env,assets,normals,strides,exposures,timestamps,
            blacks,whites,wb,lsc,lscWidth,lscHeight,rawWidth,rawHeight,
            physicalCfa,cropX,cropY,fullSensorWidth,fullSensorHeight,
            referenceIndex,sr,outputRgbTexture,outputClipTexture,physicalLensIdentity);
    }catch(const std::exception& error){
        if(env->ExceptionCheck())return;
        const auto cl=env->FindClass("java/lang/IllegalStateException");
        if(cl)env->ThrowNew(cl,error.what());
    }
}
