// IRIS_26856_B_ONLY_EGL_VULKAN_NATIVE_FENCE_OWNER
#pragma once
#include <vulkan/vulkan.h>
namespace amaze {
// Each EGL fence fd is owned exactly once. A Vulkan import consumes the fd.
// Vulkan->EGL export produces a new fd consumed by the EGL import.
class ScopedNativeFd final {
public:
    explicit ScopedNativeFd(int fd = -1) noexcept : fd_(fd) {}
    ~ScopedNativeFd();
    ScopedNativeFd(const ScopedNativeFd&) = delete;
    ScopedNativeFd& operator=(const ScopedNativeFd&) = delete;
    ScopedNativeFd(ScopedNativeFd&& other) noexcept;
    ScopedNativeFd& operator=(ScopedNativeFd&& other) noexcept;
    int get() const noexcept { return fd_; }
    int release() noexcept;
private:
    int fd_;
};
// Must run on the caller's current GLES/EGL context after the CFA write.
ScopedNativeFd createCurrentGlReleaseFence();
// Creates a temporary binary Vulkan semaphore importing an EGL sync fd.
// Does not wait: pass semaphore to CommandSubmissionOwner::execute.
VkSemaphore importGlFenceToVulkan(VkDevice device, ScopedNativeFd&& fence);
// Creates a Vulkan semaphore whose SYNC_FD can later be exported for GL.
VkSemaphore createGlExportableSemaphore(VkDevice device);
// Requires a signal submitted on this semaphore. Consumes the signal payload.
ScopedNativeFd exportVulkanFenceToGl(VkDevice device, VkSemaphore semaphore);
// Must run on the caller's current GLES/EGL context before reading RGB.
void waitCurrentGlOnVulkanFence(ScopedNativeFd&& fence);
} // namespace amaze
