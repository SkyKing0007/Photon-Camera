// IRIS_26864_REAL_PINNED_B_GL_VULKAN_NATIVE_JNI_INTEROP
// This is included by the exact successful 26863 AMaZE JNI implementation,
// preserving its existing GL/AHB/fence helpers and original JNI entry point.
#include "Iris26864FrozenDirectRawrRunner.hpp"
#include "Iris26864NativeBridgeShaders.hpp"
#include "bridge/Iris26864HdrqCanonicalGpuBridge.hpp"
#include "Iris26864Wronski2xSingleOwnerBridge.hpp"
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
    iris26864::VulkanImageArena surfaces(ctx.physicalDevice,ctx.device,
                                VkDeviceSize(outWidth)*outHeight*12ull+(16ull<<20u));
    surfaces.allocate(outWidth/2u,outHeight/2u,VK_FORMAT_R16G16B16A16_SFLOAT,
                      VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    surfaces.allocate(outWidth/2u,outHeight/2u,VK_FORMAT_R16_UINT,
                      VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_SAMPLED_BIT);
    const auto packed=surfaces.at(0), rawClip=surfaces.at(1);
    auto hdrqShader=sr?nullptr:iris26864::makeRealHdrqCfaBridge(ctx.device);
    auto wronskiShader=sr?iris26864::makeRealWronskiCfaBridge(ctx.device):nullptr;
    auto clipShader=iris26864::makeRealSensorClipToGlBridge(ctx.device);
    bool publishedClip=false;
    // This callback executes while RAWR still owns the exact completed GPU
    // merge scratch. The B engines cannot return an alias of inherited A RGB.
    iris26864::runRealRawrFromFrozenDirectNormals(req,commands,[&](
        const rawr::raw_gpu_pipeline::BurstRunResult& result,
        const iris26864::RealRawrRunRequest& original){
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
                const auto receipt=iris26864::wronski2x::recordWronski2xToAmaze(
                    cmd,f,*wronskiShader,amaze);
                if(!receipt.preAmazeLscStageComplete||receipt.legacyPostAmazeLscPermitted||
                   receipt.legacyIrisChromaDenoisePermitted||!receipt.image)
                    throw std::runtime_error("26864 Wronski LSC/clip ownership receipt incomplete");
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
