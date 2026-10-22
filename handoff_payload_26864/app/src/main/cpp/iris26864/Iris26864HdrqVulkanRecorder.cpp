#include "Iris26864HdrqVulkanRecorder.hpp"
#include <stdexcept>
#include <unordered_map>
#include <utility>
namespace iris26864 {
void recordHdrqVulkanExpandedSchedule(const Plan& plan, VkCommandBuffer cmd,
                                      const HdrqExpandedBindingProvider& bind) {
    if(cmd==VK_NULL_HANDLE || !bind)
        throw std::invalid_argument("26864 HDRq Vulkan command/provider missing");
    // makeHdrqSchedule performs all B frequency owner/path/normal validation.
    const auto stages=makeHdrqSchedule(plan);
    verifyHdrqSchedule(plan, stages);
    // If any stage is missing, throw BEFORE recording GPU commands. A half-
    // recorded GPU sequence is forbidden even if the caller would discard it.
    // BindingProvider MUST only resolve/validate ownership, not update GPU state.
    std::vector<HdrqKernelInvocation> jobs;
    jobs.reserve(stages.size());
    for(const auto& stage:stages) {
        std::vector<HdrqKernelInvocation> expanded=bind(stage);
        if(expanded.empty() || expanded.size()>128u)
            throw std::invalid_argument("26864 HDRq empty/oversized expanded GPU stage");
        const bool alignment=stage.step==HdrqStep::ReferenceAlignPrepare ||
                             stage.step==HdrqStep::CompanionAlignCoarse ||
                             stage.step==HdrqStep::CompanionAlignFinest;
        if(!alignment && expanded.size()!=1u)
            throw std::invalid_argument("26864 non-alignment stage illegally expanded");
        bool seenFill=false,seenCopy=false;
        for(size_t n=0;n<expanded.size();++n) {
            auto& job=expanded[n];
            if(job.ownership.step!=stage.step || job.ownership.pass!=stage.pass ||
               job.ownership.normalIndex!=stage.normalIndex)
                throw std::invalid_argument("26864 expanded GPU stage owner mismatch");
            if(job.kind==HdrqRecordedKind::Kernel) {
                if(job.clearImage!=VK_NULL_HANDLE || job.transferSrc!=VK_NULL_HANDLE ||
                   job.transferDst!=VK_NULL_HANDLE ||job.transferBytes ||
                   !job.kernel || !job.width || !job.height || !job.depth ||
                   job.pushWords.size()>32u || stage.step==HdrqStep::ClearTileMismatch)
                    throw std::invalid_argument("26864 invalid composite compute invocation");
            }else if(job.kind==HdrqRecordedKind::ClearTileMismatch) {
                if(stage.step!=HdrqStep::ClearTileMismatch || n!=0u ||
                   stage.normalIndex!=UINT32_MAX || job.clearImage==VK_NULL_HANDLE ||
                   job.kernel || !job.resources.empty() || !job.pushWords.empty() ||
                   job.transferSrc!=VK_NULL_HANDLE || job.transferDst!=VK_NULL_HANDLE)
                    throw std::invalid_argument("26864 invalid real Vulkan mismatch clear");
            }else if(job.kind==HdrqRecordedKind::FillAlignmentZero) {
                if(stage.step!=HdrqStep::CompanionAlignCoarse || seenFill ||
                   n==0u || job.transferDst==VK_NULL_HANDLE ||job.transferSrc!=VK_NULL_HANDLE ||
                   job.transferBytes!=8u || job.transferDstOffset ||job.transferSrcOffset ||
                   job.kernel || !job.resources.empty() || !job.pushWords.empty())
                    throw std::invalid_argument("26864 invalid coarsest align initialization");
                seenFill=true;
            }else if(job.kind==HdrqRecordedKind::CopyAlignmentSlot) {
                if(stage.step!=HdrqStep::CompanionAlignFinest || seenCopy ||
                   n+1u!=expanded.size() || job.transferSrc==VK_NULL_HANDLE ||
                   job.transferDst==VK_NULL_HANDLE || !job.transferBytes ||
                   (job.transferBytes&3u) ||(job.transferDstOffset&3u) ||
                   job.transferSrcOffset ||job.kernel||!job.resources.empty() ||
                   !job.pushWords.empty())
                    throw std::invalid_argument("26864 invalid align-once SSBO transfer");
                seenCopy=true;
            }else throw std::invalid_argument("26864 unknown GPU invocation type");
            jobs.push_back(std::move(job));
        }
        if(stage.step==HdrqStep::CompanionAlignCoarse && !seenFill)
            throw std::invalid_argument("26864 missing coarsest alignment zero initialization");
    }
    // Preflight EVERY binding and the projected per-kernel descriptor-pool
    // capacity before vkAllocateDescriptorSets/vkCmdDispatch touches the GPU.
    // This also detects a late invalid companion slot before pass zero runs.
    std::unordered_map<const VulkanKernelExecutor*,uint32_t> reserved;
    for(const auto& job:jobs) {
        if(job.kind!=HdrqRecordedKind::Kernel)continue;
        const uint32_t soFar=reserved[job.kernel];
        job.kernel->preflight(job.resources,job.pushWords.size()*sizeof(uint32_t),
                              job.width,job.height,job.depth,soFar);
        reserved[job.kernel]=soFar+1u;
    }
    // Device-level resources and foreign queue ownership are outside this
    // layer. Kernels are synchronous recording only, descriptor sets unique.
    // Caller must finish GPU submission before destroying these kernels.
    bool writes=false;
    for(auto& job:jobs) {
        if(job.kind==HdrqRecordedKind::ClearTileMismatch) {
            // Pinned RAWR source: compute-write -> transfer-clear -> compute.
            // This cannot be implemented by a placeholder compute shader.
            VkMemoryBarrier toTransfer{};
            toTransfer.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            toTransfer.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
            toTransfer.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
            vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                                 VK_PIPELINE_STAGE_TRANSFER_BIT,0,1,&toTransfer,
                                 0,nullptr,0,nullptr);
            const VkClearColorValue zero{};
            const VkImageSubresourceRange range{VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
            vkCmdClearColorImage(cmd,job.clearImage,VK_IMAGE_LAYOUT_GENERAL,&zero,1,&range);
            VkMemoryBarrier toCompute{};
            toCompute.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            toCompute.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
            toCompute.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
            vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,
                                 VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&toCompute,
                                 0,nullptr,0,nullptr);
            writes=true;
            continue;
        }
        if(job.kind==HdrqRecordedKind::FillAlignmentZero ||
           job.kind==HdrqRecordedKind::CopyAlignmentSlot) {
            VkMemoryBarrier toTransfer{};
            toTransfer.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            toTransfer.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;
            toTransfer.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT|
                                     VK_ACCESS_TRANSFER_READ_BIT;
            vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                                 VK_PIPELINE_STAGE_TRANSFER_BIT,0,1,&toTransfer,
                                 0,nullptr,0,nullptr);
            if(job.kind==HdrqRecordedKind::FillAlignmentZero)
                vkCmdFillBuffer(cmd,job.transferDst,0u,job.transferBytes,0u);
            else {
                const VkBufferCopy region{job.transferSrcOffset,job.transferDstOffset,
                                          job.transferBytes};
                vkCmdCopyBuffer(cmd,job.transferSrc,job.transferDst,1u,&region);
            }
            VkMemoryBarrier toCompute{};
            toCompute.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;
            toCompute.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
            toCompute.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|
                                    VK_ACCESS_SHADER_WRITE_BIT;
            vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,
                                 VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&toCompute,
                                 0,nullptr,0,nullptr);
            writes=true;
            continue;
        }
        job.kernel->record(cmd, job.resources,
                           job.pushWords.empty()?nullptr:job.pushWords.data(),
                           job.pushWords.size()*sizeof(uint32_t),
                           job.width,job.height,job.depth,writes);
        writes=true;
    }
}
void recordHdrqVulkanSchedule(const Plan& p,VkCommandBuffer cmd,
                              const HdrqBindingProvider& bind) {
    if(!bind)throw std::invalid_argument("26864 legacy single-stage binder missing");
    recordHdrqVulkanExpandedSchedule(p,cmd,[&](const HdrqDispatch& stage) {
        return std::vector<HdrqKernelInvocation>{bind(stage)};
    });
}
} // namespace iris26864
