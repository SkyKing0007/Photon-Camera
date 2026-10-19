// IRIS_26856_VULKAN_COMMAND_SUBMISSION_OWNER
#include "amaze/CommandSubmissionOwner.hpp"
#include <stdexcept>
#include <vector>

namespace amaze {
namespace {
void check(VkResult result, const char* reason) {
    if (result != VK_SUCCESS) throw std::runtime_error(reason);
}
}
CommandSubmissionOwner::CommandSubmissionOwner(VkPhysicalDevice physical,
        VkDevice device, VkQueue queue, uint32_t familyIndex)
        : device_(device), queue_(queue) {
    if (!physical || !device_ || !queue_)
        throw std::runtime_error("AMaZE submission: missing Vulkan owner");
    uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &count, nullptr);
    if (familyIndex >= count) throw std::runtime_error("AMaZE submission: queue family out of bounds");
    // Query full array to avoid writing past a single VkQueueFamilyProperties.
    // Vulkan queue-family lists can have multiple entries.
    std::vector<VkQueueFamilyProperties> families(count);
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &count, families.data());
    if (familyIndex >= count || !(families[familyIndex].queueFlags & VK_QUEUE_COMPUTE_BIT))
        throw std::runtime_error("AMaZE submission: queue family lacks compute");
    try {
        VkCommandPoolCreateInfo pci{};
        pci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        pci.queueFamilyIndex = familyIndex;
        pci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        check(vkCreateCommandPool(device_, &pci, nullptr, &pool_), "AMaZE submission: command pool");
        VkCommandBufferAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        ai.commandPool = pool_;
        ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        ai.commandBufferCount = 1;
        check(vkAllocateCommandBuffers(device_, &ai, &command_), "AMaZE submission: command allocation");
        VkFenceCreateInfo fi{};
        fi.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        check(vkCreateFence(device_, &fi, nullptr, &fence_), "AMaZE submission: fence");
    } catch (...) {
        if (fence_) vkDestroyFence(device_, fence_, nullptr);
        if (pool_) vkDestroyCommandPool(device_, pool_, nullptr);
        throw;
    }
}
CommandSubmissionOwner::~CommandSubmissionOwner() {
    // A failed fence wait leaves completion unknown. Never free the command
    // pool while GPU work may still reference it. A device-lost result can
    // prevent a successful idle wait; in that case retain driver-owned state
    // instead of manufacturing a completed fence (device owner tears down).
    if (submitted_ && queue_) {
        const VkResult idle = vkQueueWaitIdle(queue_);
        if (idle != VK_SUCCESS) return; // fail closed: driver-owned handles remain
        submitted_ = false;
    }
    if (fence_) vkDestroyFence(device_, fence_, nullptr);
    if (pool_) vkDestroyCommandPool(device_, pool_, nullptr);
}
void CommandSubmissionOwner::execute(const std::function<void(VkCommandBuffer)>& record,
                                     VkSemaphore glAcquire, VkSemaphore glRelease) {
    if (!record) throw std::runtime_error("AMaZE submission: missing record callback");
    if (poisoned_ || submitted_) throw std::runtime_error("AMaZE submission: unresolved prior GPU work");
    check(vkResetCommandBuffer(command_, 0), "AMaZE submission: command reset");
    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    check(vkBeginCommandBuffer(command_, &bi), "AMaZE submission: begin");
    try { record(command_); }
    catch (...) {
        // Nothing was submitted: safe to reset before a later attempt.
        vkResetCommandBuffer(command_, 0);
        throw;
    }
    check(vkEndCommandBuffer(command_), "AMaZE submission: end");
    check(vkResetFences(device_, 1, &fence_), "AMaZE submission: fence reset");
    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &command_;
    const VkPipelineStageFlags waitStage = VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT;
    if (glAcquire != VK_NULL_HANDLE) {
        si.waitSemaphoreCount = 1;
        si.pWaitSemaphores = &glAcquire;
        si.pWaitDstStageMask = &waitStage;
    }
    if (glRelease != VK_NULL_HANDLE) {
        si.signalSemaphoreCount = 1;
        si.pSignalSemaphores = &glRelease;
    }
    const VkResult submitResult = vkQueueSubmit(queue_, 1, &si, fence_);
    if (submitResult != VK_SUCCESS) {
        poisoned_ = true;
        throw std::runtime_error("AMaZE submission: failed Vulkan queue submit");
    }
    submitted_ = true;
    const VkResult waited = vkWaitForFences(device_, 1, &fence_, VK_TRUE, UINT64_MAX);
    if (waited != VK_SUCCESS) {
        // Do not reuse the command buffer or release GPU resources after a
        // failed wait. Destructor must settle the queue before destroying it.
        poisoned_ = true;
        throw std::runtime_error("AMaZE submission: GPU fence wait failed; queue ownership unresolved");
    }
    submitted_ = false;
}
} // namespace amaze
