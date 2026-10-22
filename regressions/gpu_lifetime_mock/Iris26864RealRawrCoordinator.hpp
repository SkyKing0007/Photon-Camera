#pragma once
#include <array>
#include <cstdint>
#include <functional>
#include <vector>
#include <stdexcept>
using VkPhysicalDevice = uintptr_t;
using VkDevice = uintptr_t;
using VkQueue = uintptr_t;
using VkImage = uintptr_t;
using VkImageView = uintptr_t;
using VkFence = uintptr_t;
using VkFormat = int;
using VkResult = int;
constexpr VkFormat VK_FORMAT_R16_UINT=1;
constexpr VkResult VK_SUCCESS=0;
constexpr uintptr_t VK_NULL_HANDLE=0;
struct VkSubmitInfo {};
namespace test {inline int mode=0, idle=0, idleCalls=0, destructorCalls=0, destructorBeforeIdle=0, preparedCalls=0;}
inline VkResult vkQueueSubmit(VkQueue,unsigned,const VkSubmitInfo*,VkFence) {return VK_SUCCESS;}
inline VkResult vkQueueWaitIdle(VkQueue) {++test::idleCalls; return test::idle;}
namespace rawr {
namespace zsl_ring {
struct RawRef {uint64_t timestampNs=0;uint32_t width=0,height=0;};
struct GpuRawImageView { RawRef ref{}; VkImage image=0;VkImageView view=0;VkFormat format=VK_FORMAT_R16_UINT;};
}
namespace raw_merge_wronski_gpu {
enum class CfaPattern {RGGB,GRBG,GBRG,BGGR};
struct Config{CfaPattern cfa{}; bool estimateNoiseFromBurst=false;};
}
namespace raw_merge_hdrplus_gpu {struct Config {};}
namespace raw_gpu_pipeline {
enum class MergeAlgorithm {Wronski, HdrPlusSpatial, HdrPlusFrequency};
struct ParamsNorm {std::array<float,4> blackByPhase{};float whiteLevel=0;};
struct Params {ParamsNorm normalization{};std::array<float,3> whiteBalance{};};
struct BurstFrame {zsl_ring::GpuRawImageView raw{};Params parameters{};float exposure=0;};
struct Extent {uint32_t width=0,height=0;};
struct BurstRunResult {VkImage output=11;VkImageView outputView=12;unsigned frameCount=2,referenceIndex=0;bool noiseEstimated=true;Extent outputExtent{};VkImage cfaImage=41;VkImageView cfaView=42;};
struct AndroidBurstCoordinator {
using Submit=std::function<void(const VkSubmitInfo&,VkFence)>;
using FramePrepared=std::function<void(uint32_t)>;
uint32_t width=0,height=0;MergeAlgorithm algorithm=MergeAlgorithm::Wronski;
~AndroidBurstCoordinator(){++test::destructorCalls;if(test::mode==1 && !test::idleCalls)++test::destructorBeforeIdle;}
void initialize(VkPhysicalDevice,VkDevice,unsigned,Submit,uint32_t w,uint32_t h,float, std::function<void()>, std::array<int,0>,raw_merge_wronski_gpu::Config,MergeAlgorithm a, raw_merge_hdrplus_gpu::Config){width=w;height=h;algorithm=a;}
BurstRunResult run(const std::vector<BurstFrame>& frames,uint32_t ref,std::nullptr_t,FramePrepared prepare){
 if(prepare){prepare(ref);for(size_t i=0;i<frames.size();i++)if(i!=ref)prepare((uint32_t)i);}
 if(test::mode==1)throw std::runtime_error("mock fence not completed");
 BurstRunResult r{};r.frameCount=frames.size();r.referenceIndex=ref;
 r.outputExtent={algorithm==MergeAlgorithm::Wronski?width*2u:width,algorithm==MergeAlgorithm::Wronski?height*2u:height};
 if(test::mode==2)r.noiseEstimated=false;
 if(test::mode==3)r.outputExtent.width=2;
 return r;
}
};
}
}
namespace iris26864 {
enum class RealBEngine {HdrPlusFrequency,WronskiTrue2x};
struct RealRawrNormal {
rawr::zsl_ring::GpuRawImageView borrowedRaw{};uint64_t timestampNs=0,physicalLensIdentity=1;
float exposureProduct=1,sensorWhite=1023;std::array<float,4> phaseBlack{{64,64,64,64}};
std::array<float,3> whiteBalance{{1,1,1}};
};
struct RealRawrRunRequest {
VkPhysicalDevice physical=1;VkDevice device=2;VkQueue inheritedQueue=3;
uint32_t queueFamily=0,width=32,height=32,effectiveCfa=0,referenceIndex=0;
RealBEngine algorithm=RealBEngine::WronskiTrue2x;
std::vector<RealRawrNormal> normals;
rawr::raw_gpu_pipeline::AndroidBurstCoordinator::FramePrepared prepareNormal;
};
using ConsumePinnedRawrGpuResult=std::function<void(const rawr::raw_gpu_pipeline::BurstRunResult&,const RealRawrRunRequest&)>;
void runRealPinnedRawrB(const RealRawrRunRequest&,const ConsumePinnedRawrGpuResult&);
}
