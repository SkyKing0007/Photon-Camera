#include "Iris26943GpuZslRing.hpp"
#include <android/log.h>
#include <stdexcept>
#include <string>
#include <unordered_set>
namespace iris26864 {
Iris26943GpuZslRing::Iris26943GpuZslRing(amaze::VulkanDeviceOwner& owner,
        uint32_t width,uint32_t height,uint32_t capacity,uint64_t lens,uint64_t generation)
    : owner_(owner), width_(width), height_(height), capacity_(capacity),
      lens_(lens), generation_(generation), frames_(capacity) {
    if (!lens||!generation||!width||!height||capacity<2u||capacity>30u)
        throw std::invalid_argument("26943 invalid raw ring capacity/provenance");
    const auto c=owner.context();
    device_=c.device; family_=c.queueFamilyIndex;
    uploads_=std::make_unique<amaze::CommandSubmissionOwner>(c.physicalDevice,
        c.device,owner.ingressQueue(),family_);
    images_=std::make_unique<TwoSlotRaw16Uploader>(c.physicalDevice,c.device,
        *uploads_,width,height,capacity);
}
Iris26943GpuZslRing::~Iris26943GpuZslRing() {
    // All ring uploads were individually fence-complete, but the merge
    // possibly read these images from another same-family queue. The owner
    // must have settled the *whole device* before destroying this ring.
    if (bridge_) vkDestroySemaphore(device_,bridge_,nullptr);
}
void Iris26943GpuZslRing::stage(AHardwareBuffer* ahb,int cameraFenceFd,
                               uint64_t timestamp,uint64_t lens,uint64_t generation) {
    if (lens!=lens_ || generation!=generation_ || !timestamp)
        throw std::invalid_argument("26943 stale camera generation/lens/raw timestamp");
    for (const auto& f:frames_) if (f.ready && f.timestamp==timestamp) return;
    const uint32_t slot=next_;
    // No selected frames are overwritten during a shutter/merge: JNI holds
    // the same B cache mutex from snapshot through final AMaZE GPU fence.
    frames_[slot].ready=false;
    frames_[slot].timestamp=0;
    try {images_->uploadHardwareBufferInto(slot,ahb,cameraFenceFd,family_);}
    catch (...) {frames_[slot]={};throw;}
    frames_[slot]={timestamp,true};
    next_=(next_+1u)%capacity_;
}
bool Iris26943GpuZslRing::select(const std::vector<uint64_t>& timestamps,
                                 uint64_t lens,std::vector<TransientImageView>& views) {
    views.clear();
    if (lens!=lens_ || timestamps.size()<2u || timestamps.size()>capacity_)return false;
    std::unordered_set<uint64_t> seen;
    for (const auto ts:timestamps) {
        if (!ts || !seen.insert(ts).second) {views.clear();return false;}
        bool found=false;
        for (uint32_t i=0;i<capacity_;++i) {
            if (frames_[i].ready && frames_[i].timestamp==ts) {
                views.push_back(images_->imageAt(i));found=true;break;
            }
        }
        if (!found){views.clear();return false;}
    }
    return true;
}
VkSemaphore Iris26943GpuZslRing::bridgeForMerge() {
    if (!owner_.hasSeparateIngressQueue())return VK_NULL_HANDLE;
    if (bridge_) {vkDestroySemaphore(device_,bridge_,nullptr);bridge_=VK_NULL_HANDLE;}
    VkSemaphoreCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    if (vkCreateSemaphore(device_,&ci,nullptr,&bridge_)!=VK_SUCCESS)
        throw std::runtime_error("26943 RAW ring cross-queue semaphore allocation failed");
    // Completing the signal submit's fence is not enough for cross-queue
    // memory visibility. The FIRST merge submit MUST explicitly wait on
    // this semaphore at COMPUTE_SHADER stage. No queue-idle shortcut.
    uploads_->execute([](VkCommandBuffer) {},VK_NULL_HANDLE,bridge_);
    return bridge_;
}
uint32_t Iris26943GpuZslRing::readyCount() const noexcept {
    uint32_t n=0;for(const auto& f:frames_)if(f.ready)++n;return n;
}
} // namespace iris26864
