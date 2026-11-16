#pragma once
// IRIS_26943_OPTIONAL_CAMERA_TO_VULKAN_ZSL_RING
// The existing Camera2 ZSL ring is authoritative. These are only OPTIONAL
// GPU copies of its RAW16 images. No ImageReader slot, shutter timestamp,
// exposure or selected burst is ever owned/changed here.
#include "Iris26864TwoSlotRaw16Uploader.hpp"
#include "amaze/VulkanDeviceOwner.hpp"
#include <android/hardware_buffer.h>
#include <cstdint>
#include <memory>
#include <vector>

namespace iris26864 {
class Iris26943GpuZslRing final {
public:
    Iris26943GpuZslRing(amaze::VulkanDeviceOwner& device, uint32_t width,
                       uint32_t height, uint32_t capacity, uint64_t lens,
                       uint64_t cameraGeneration);
    ~Iris26943GpuZslRing();
    Iris26943GpuZslRing(const Iris26943GpuZslRing&) = delete;
    Iris26943GpuZslRing& operator=(const Iris26943GpuZslRing&) = delete;
    // Called only by the private worker while the B cache mutex is held.
    // Upload finishes on a real Vulkan fence before a slot becomes ready.
    void stage(AHardwareBuffer* image, int cameraFenceFd,
               uint64_t timestamp, uint64_t lens, uint64_t generation);
    // Called only at the shutter's already-frozen immutable JPEG handoff,
    // with the SAME B cache mutex. All N selected frames must match exactly,
    // otherwise no partial resident subset is ever used.
    bool select(const std::vector<uint64_t>& timestamps, uint64_t lens,
                std::vector<TransientImageView>& views);
    // The writer's queue and merge queue are same-family. If distinct, the
    // returned binary semaphore is signaled by ingress AFTER all prior copies,
    // and the first merge submit waits on it. Owned until last merge fence.
    VkSemaphore bridgeForMerge();
    uint32_t capacity() const noexcept { return capacity_; }
    uint32_t readyCount() const noexcept;
    uint64_t generation() const noexcept { return generation_; }
    uint64_t lens() const noexcept { return lens_; }
    uint32_t width() const noexcept { return width_; }
    uint32_t height() const noexcept { return height_; }
private:
    struct Frame { uint64_t timestamp=0; bool ready=false; };
    amaze::VulkanDeviceOwner& owner_;
    VkDevice device_{};
    uint32_t family_=0;
    uint32_t width_=0,height_=0,capacity_=0;
    uint64_t lens_=0,generation_=0;
    uint32_t next_=0;
    std::unique_ptr<amaze::CommandSubmissionOwner> uploads_;
    std::unique_ptr<TwoSlotRaw16Uploader> images_;
    std::vector<Frame> frames_;
    VkSemaphore bridge_{};
};
} // namespace iris26864
