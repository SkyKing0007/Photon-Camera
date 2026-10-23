#pragma once
// IRIS_26864_NATIVE_REAL_TWO_SLOT_RAW16_TRANSFER
// Borrowed immutable direct JNI RAW16 planes. The upload is synchronous and
// GPU-fenced using unchanged successful 26863 CommandSubmissionOwner. Neither
// reference nor companion image may be freed while RAWR/AMaZE consumes them.
#include "Iris26864VulkanImageArena.hpp"
#include "amaze/CommandSubmissionOwner.hpp"
#include <cstdint>
#include <cstddef>
#include <memory>
#include <vector>
namespace iris26864 {
struct Raw16PlaneBorrow final {
    const unsigned char* source = nullptr;
    size_t bytes = 0;
    uint32_t rowStride = 0;
    uint32_t width = 0,height = 0;
    uint64_t timestamp = 0;
};
class TwoSlotRaw16Uploader final {
public:
    TwoSlotRaw16Uploader(VkPhysicalDevice, VkDevice, amaze::CommandSubmissionOwner&,
                         uint32_t width, uint32_t height, uint32_t slots=2u);
    ~TwoSlotRaw16Uploader();
    TwoSlotRaw16Uploader(const TwoSlotRaw16Uploader&)=delete;
    TwoSlotRaw16Uploader& operator=(const TwoSlotRaw16Uploader&)=delete;
    TransientImageView referenceImage() const;
    TransientImageView companionImage() const;
    TransientImageView imageAt(uint32_t index) const;
    void uploadInto(uint32_t index, uint32_t slot, const std::vector<Raw16PlaneBorrow>& frames);
    void upload(uint32_t index, uint32_t referenceIndex,
                const std::vector<Raw16PlaneBorrow>& frames);
    // If a queue/fence failure prevents demonstrating completion, allow the
    // Vulkan device owner to reclaim resources at device teardown rather than
    // freeing a possibly still-in-use VkImage allocation.
    void quarantineUnresolved() noexcept;
private:
    VkPhysicalDevice physical_=VK_NULL_HANDLE;
    VkDevice device_=VK_NULL_HANDLE;
    amaze::CommandSubmissionOwner& submit_;
    std::unique_ptr<VulkanImageArena> images_;
    VkBuffer staging_=VK_NULL_HANDLE;
    VkDeviceMemory stagingMemory_=VK_NULL_HANDLE;
    void* stagingMapped_=nullptr;
    uint32_t width_=0,height_=0,slots_=2;
    uint64_t stagingBytes_=0;
    bool quarantined_=false;
};
} // namespace iris26864
