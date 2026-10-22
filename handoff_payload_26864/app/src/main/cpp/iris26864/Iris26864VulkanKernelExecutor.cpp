// IRIS_26864_NATIVE_VK_KERNEL_RECORDING_ONLY_NOT_FULL_HDRQ_WRONSKI
#include "Iris26864VulkanKernelExecutor.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace iris26864 {
namespace {
void requireVk(VkResult result, const char* step) {
    if (result != VK_SUCCESS) throw std::runtime_error(
        std::string("26864 Vulkan compute ") + step + " failed: " + std::to_string(int(result)));
}
bool isAllowed(VkDescriptorType kind) {
    return kind == VK_DESCRIPTOR_TYPE_STORAGE_IMAGE ||
           kind == VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE ||
           kind == VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER ||
           kind == VK_DESCRIPTOR_TYPE_STORAGE_BUFFER ||
           kind == VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
}
uint32_t groups(uint32_t extent, uint32_t local) {
    return extent / local + uint32_t(extent % local != 0u); // overflow-safe
}
}
VulkanKernelExecutor::VulkanKernelExecutor(VkDevice device, ShaderBinary shader,
    const std::vector<ComputeBinding>& bindings, uint32_t pushConstantSize,
    uint32_t maxDispatches)
    : device_(device), bindings_(bindings), pushConstantSize_(pushConstantSize),
      groupX_(shader.workgroupX), groupY_(shader.workgroupY), groupZ_(shader.workgroupZ),
      maxDispatches_(maxDispatches) {
    if (device == VK_NULL_HANDLE || shader.words == nullptr || shader.wordCount < 5u ||
        shader.wordCount > std::numeric_limits<size_t>::max() / sizeof(uint32_t) ||
        shader.words[0] != 0x07230203u ||
        !groupX_ || !groupY_ || !groupZ_ || groupX_ > 1024u || groupY_ > 1024u ||
        groupZ_ > 64u || bindings.size() > 32u || pushConstantSize > 128u ||
        maxDispatches < 1u || maxDispatches > 8192u ||
        (pushConstantSize & 3u) != 0u)
        throw std::invalid_argument("26864 invalid Vulkan shader/binding/workgroup contract");
    std::sort(bindings_.begin(), bindings_.end(), [](const ComputeBinding& a,const ComputeBinding& b) {
        return a.binding < b.binding;
    });
    for (size_t i = 0; i < bindings_.size(); ++i) {
        if (!isAllowed(bindings_[i].type) || bindings_[i].binding >= 64u ||
            (i && bindings_[i].binding == bindings_[i-1].binding))
            throw std::invalid_argument("26864 duplicate/unsupported Vulkan descriptor binding");
    }
    try {
        VkShaderModuleCreateInfo shaderInfo{};
        shaderInfo.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        shaderInfo.codeSize = shader.wordCount * sizeof(uint32_t);
        shaderInfo.pCode = shader.words;
        requireVk(vkCreateShaderModule(device_, &shaderInfo, nullptr, &shaderModule_), "shader-module");
        std::vector<VkDescriptorSetLayoutBinding> descriptorBindings;
        descriptorBindings.reserve(bindings_.size());
        std::array<uint32_t, 5> poolCounts{};
        constexpr std::array<VkDescriptorType, 5> types{
            VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE,
            VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
            VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER};
        for (const auto& b : bindings_) {
            VkDescriptorSetLayoutBinding out{};
            out.binding = b.binding;
            out.descriptorType = b.type;
            out.descriptorCount = 1u;
            out.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
            descriptorBindings.push_back(out);
            const auto it = std::find(types.begin(), types.end(), b.type);
            ++poolCounts[size_t(it - types.begin())];
        }
        VkDescriptorSetLayoutCreateInfo layoutInfo{};
        layoutInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
        layoutInfo.bindingCount = uint32_t(descriptorBindings.size());
        layoutInfo.pBindings = descriptorBindings.empty() ? nullptr : descriptorBindings.data();
        requireVk(vkCreateDescriptorSetLayout(device_, &layoutInfo, nullptr, &setLayout_),
                  "descriptor-set-layout");
        VkPushConstantRange push{};
        push.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        push.size = pushConstantSize_;
        VkPipelineLayoutCreateInfo pipelineLayoutInfo{};
        pipelineLayoutInfo.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        pipelineLayoutInfo.setLayoutCount = 1;
        pipelineLayoutInfo.pSetLayouts = &setLayout_;
        pipelineLayoutInfo.pushConstantRangeCount = pushConstantSize_ ? 1u : 0u;
        pipelineLayoutInfo.pPushConstantRanges = pushConstantSize_ ? &push : nullptr;
        requireVk(vkCreatePipelineLayout(device_, &pipelineLayoutInfo, nullptr, &pipelineLayout_),
                  "pipeline-layout");
        VkPipelineShaderStageCreateInfo stage{};
        stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
        stage.module = shaderModule_;
        stage.pName = "main";
        VkComputePipelineCreateInfo pipelineInfo{};
        pipelineInfo.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
        pipelineInfo.stage = stage;
        pipelineInfo.layout = pipelineLayout_;
        requireVk(vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1u, &pipelineInfo,
                                           nullptr, &pipeline_), "compute-pipeline");
        // Even zero-binding kernels use one compatible set, no hidden stale set.
        std::vector<VkDescriptorPoolSize> poolSizes;
        for (size_t i = 0; i < types.size(); ++i) {
            if (poolCounts[i]) poolSizes.push_back({types[i], poolCounts[i] * maxDispatches_});
        }
        if (poolSizes.empty()) {
            // Empty layouts do not require a bound descriptor set.
            return;
        }
        VkDescriptorPoolCreateInfo poolInfo{};
        poolInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        poolInfo.maxSets = maxDispatches_;
        poolInfo.poolSizeCount = uint32_t(poolSizes.size());
        poolInfo.pPoolSizes = poolSizes.data();
        requireVk(vkCreateDescriptorPool(device_, &poolInfo, nullptr, &descriptorPool_),
                  "descriptor-pool");
    } catch (...) {
        cleanup();
        throw;
    }
}
void VulkanKernelExecutor::cleanup() noexcept {
    if (device_ == VK_NULL_HANDLE) return;
    if (pipeline_ != VK_NULL_HANDLE) vkDestroyPipeline(device_, pipeline_, nullptr);
    if (descriptorPool_ != VK_NULL_HANDLE) vkDestroyDescriptorPool(device_, descriptorPool_, nullptr);
    if (pipelineLayout_ != VK_NULL_HANDLE) vkDestroyPipelineLayout(device_, pipelineLayout_, nullptr);
    if (setLayout_ != VK_NULL_HANDLE) vkDestroyDescriptorSetLayout(device_, setLayout_, nullptr);
    if (shaderModule_ != VK_NULL_HANDLE) vkDestroyShaderModule(device_, shaderModule_, nullptr);
    pipeline_ = VK_NULL_HANDLE; descriptorPool_ = VK_NULL_HANDLE;
    pipelineLayout_ = VK_NULL_HANDLE; setLayout_ = VK_NULL_HANDLE;
    shaderModule_ = VK_NULL_HANDLE;
}
VulkanKernelExecutor::~VulkanKernelExecutor() { cleanup(); }
void VulkanKernelExecutor::preflight(const std::vector<BoundResource>& resources,
        size_t pushByteCount,uint32_t width,uint32_t height,uint32_t depth,
        uint32_t additionalReserved) const {
    if (!width || !height || !depth || pushByteCount != pushConstantSize_ ||
        resources.size() != bindings_.size() ||
        additionalReserved >= maxDispatches_ ||
        recordedDispatches_ > maxDispatches_ - 1u - additionalReserved)
        throw std::invalid_argument("26864 Vulkan compute preflight dispatch contract violation");
    if (groups(width,groupX_)>65535u || groups(height,groupY_)>65535u ||
        groups(depth,groupZ_)>65535u)
        throw std::invalid_argument("26864 Vulkan dispatch grid exceeds portable device limit");
    auto sorted=resources;
    std::sort(sorted.begin(),sorted.end(),[](const BoundResource& a,const BoundResource& b){
        return a.binding<b.binding;
    });
    for(size_t i=0;i<sorted.size();++i) {
        const auto& r=sorted[i];
        if(r.binding!=bindings_[i].binding || r.type!=bindings_[i].type)
            throw std::invalid_argument("26864 Vulkan preflight descriptor layout mismatch");
        if(r.type==VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER || r.type==VK_DESCRIPTOR_TYPE_STORAGE_BUFFER) {
            if(r.buffer==VK_NULL_HANDLE || !r.bufferRange ||
               r.bufferRange==VK_WHOLE_SIZE || r.bufferOffset>VK_WHOLE_SIZE-r.bufferRange)
                throw std::invalid_argument("26864 Vulkan preflight SSBO range invalid");
        } else if(r.imageView==VK_NULL_HANDLE ||
                  (r.type==VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER && r.sampler==VK_NULL_HANDLE))
            throw std::invalid_argument("26864 Vulkan preflight image/sampler invalid");
    }
}
void VulkanKernelExecutor::record(VkCommandBuffer cmd,
        const std::vector<BoundResource>& resources, const void* pushConstants,
        size_t pushByteCount, uint32_t width, uint32_t height, uint32_t depth,
        bool previousComputeWrites) const {
    if(cmd==VK_NULL_HANDLE || (pushByteCount && !pushConstants))
        throw std::invalid_argument("26864 Vulkan recording command/push values missing");
    preflight(resources,pushByteCount,width,height,depth);
    const auto gx=groups(width,groupX_),gy=groups(height,groupY_),gz=groups(depth,groupZ_);
    // One immutable descriptor set per command recording; reusing a set here
    // would corrupt earlier dispatches in the same command buffer. The owner
    // waits for completion before destroying the kernel and descriptor pool.
    std::vector<BoundResource> sorted = resources;
    std::sort(sorted.begin(), sorted.end(), [](const BoundResource& a,const BoundResource& b){
        return a.binding < b.binding;
    });
    VkDescriptorSet currentSet = VK_NULL_HANDLE;
    if (!bindings_.empty()) {
        VkDescriptorSetAllocateInfo allocate{};
        allocate.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        allocate.descriptorPool = descriptorPool_;
        allocate.descriptorSetCount = 1u;
        allocate.pSetLayouts = &setLayout_;
        requireVk(vkAllocateDescriptorSets(device_, &allocate, &currentSet),
                  "per-dispatch immutable descriptor set");
    }
    std::vector<VkDescriptorImageInfo> images(sorted.size());
    std::vector<VkDescriptorBufferInfo> buffers(sorted.size());
    std::vector<VkWriteDescriptorSet> writes(sorted.size());
    for (size_t i = 0; i < sorted.size(); ++i) {
        const auto& res = sorted[i];
        if (res.binding != bindings_[i].binding || res.type != bindings_[i].type)
            throw std::invalid_argument("26864 Vulkan descriptor index/type mismatch");
        VkWriteDescriptorSet write{};
        write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        write.dstSet = currentSet;
        write.dstBinding = res.binding;
        write.descriptorCount = 1u;
        write.descriptorType = res.type;
        if (res.type == VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER ||
            res.type == VK_DESCRIPTOR_TYPE_STORAGE_BUFFER) {
            if (res.buffer == VK_NULL_HANDLE || !res.bufferRange ||
                res.bufferRange == VK_WHOLE_SIZE)
                throw std::invalid_argument("26864 Vulkan buffer descriptor invalid");
            buffers[i] = {res.buffer, res.bufferOffset, res.bufferRange};
            write.pBufferInfo = &buffers[i];
        } else {
            if (res.imageView == VK_NULL_HANDLE ||
                (res.type == VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER &&
                 res.sampler == VK_NULL_HANDLE))
                throw std::invalid_argument("26864 Vulkan image/sampler descriptor invalid");
            images[i].imageView = res.imageView;
            images[i].sampler = res.sampler;
            images[i].imageLayout = VK_IMAGE_LAYOUT_GENERAL;
            write.pImageInfo = &images[i];
        }
        writes[i] = write;
    }
    if (!writes.empty()) vkUpdateDescriptorSets(device_, uint32_t(writes.size()), writes.data(), 0, nullptr);
    if (previousComputeWrites) {
        VkMemoryBarrier barrier{};
        barrier.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
        barrier.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT;
        vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                             VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0,
                             1u, &barrier, 0, nullptr, 0, nullptr);
    }
    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline_);
    if (currentSet != VK_NULL_HANDLE)
        vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE,
                                pipelineLayout_, 0, 1, &currentSet, 0, nullptr);
    if (pushConstantSize_)
        vkCmdPushConstants(cmd, pipelineLayout_, VK_SHADER_STAGE_COMPUTE_BIT,
                           0, pushConstantSize_, pushConstants);
    vkCmdDispatch(cmd, gx, gy, gz);
    ++recordedDispatches_;
}
} // namespace iris26864
