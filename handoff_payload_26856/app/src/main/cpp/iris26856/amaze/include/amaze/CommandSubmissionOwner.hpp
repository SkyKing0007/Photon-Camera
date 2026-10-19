// IRIS_26856_VULKAN_COMMAND_SUBMISSION_OWNER
// Narrow, fail-closed caller-owned Vulkan queue submission for AMaZE.
// Cross-API acquire/release MUST be completed by the caller before/after submit.
#pragma once
#include <vulkan/vulkan.h>
#include <functional>

namespace amaze {
class CommandSubmissionOwner final {
public:
    CommandSubmissionOwner(VkPhysicalDevice physical, VkDevice device,
                           VkQueue queue, uint32_t familyIndex);
    ~CommandSubmissionOwner();
    CommandSubmissionOwner(const CommandSubmissionOwner&) = delete;
    CommandSubmissionOwner& operator=(const CommandSubmissionOwner&) = delete;

    // Records and submits one entire frame, then waits for completion before
    // permitting source/output lifetimes to end. No queue-idle or CPU pixels.
    // Caller owns external GLES->Vulkan and Vulkan->GLES synchronization.
    void execute(const std::function<void(VkCommandBuffer)>& record,
                 VkSemaphore glAcquire = VK_NULL_HANDLE,
                 VkSemaphore glRelease = VK_NULL_HANDLE);
private:
    VkDevice device_ = VK_NULL_HANDLE;
    VkQueue queue_ = VK_NULL_HANDLE;
    VkCommandPool pool_ = VK_NULL_HANDLE;
    VkCommandBuffer command_ = VK_NULL_HANDLE;
    VkFence fence_ = VK_NULL_HANDLE;
    // A failed fence wait must not free an in-flight command pool or imported image.
    bool submitted_ = false;
    bool poisoned_ = false;
};
} // namespace amaze
