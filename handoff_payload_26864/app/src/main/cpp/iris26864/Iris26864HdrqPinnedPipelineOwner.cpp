// IRIS_26864_HDRQ_PINNED_ALL_OR_NOTHING_PIPELINE_COMPOSITION_NOT_ANDROID
#include "Iris26864HdrqPinnedPipelineOwner.hpp"
#include <set>
#include <stdexcept>
#include <utility>
namespace iris26864 {
HdrqPinnedPipelineOwner::HdrqPinnedPipelineOwner(
        VkDevice device, const PinnedSpirvBytesProvider& provider,
        const std::map<std::string,uint32_t>& maxUses) {
    if(device==VK_NULL_HANDLE)
        throw std::invalid_argument("26864 B HDRq Vulkan device missing");
    const auto& contracts=pinnedHdrqContracts();
    if(contracts.size()!=23u || maxUses.size()!=contracts.size())
        throw std::invalid_argument("26864 B HDRq dispatch budgets incomplete");
    std::set<std::string> expected;
    for(const auto& c:contracts){
        if(!expected.insert(c.assetStem).second)
            throw std::logic_error("26864 duplicate source-locked kernel");
        const auto cap=maxUses.find(c.assetStem);
        if(cap==maxUses.end() || cap->second==0u || cap->second>8192u)
            throw std::invalid_argument("26864 missing/invalid per-kernel dispatch budget");
    }
    // Critically, reject ALL invalid, incomplete and substituted shaders
    // before GPU objects or descriptor pools are created.
    auto validated=requireCompletePinnedHdrqSpirv(provider);
    if(validated.size()!=contracts.size())
        throw std::logic_error("26864 source-locked SPIR-V count mismatch");
    for(size_t i=0;i<contracts.size();++i){
        const auto& c=contracts[i];
        const auto& binary=validated[i];
        if(binary.name!=c.assetStem)
            throw std::logic_error("26864 SPIR-V entry ordering changed");
        std::vector<ComputeBinding> b;
        b.reserve(c.bindings.size());
        for(const auto& d:c.bindings)b.push_back({d.binding,d.descriptor});
        const ShaderBinary shader{binary.words.data(),binary.words.size(),
                                  c.localX,c.localY,c.localZ};
        // VulkanKernelExecutor destructor is noexcept and releases all
        // objects if a later pipeline fails. No fallback kernel permitted.
        auto kernel=std::make_unique<VulkanKernelExecutor>(
            device,shader,b,c.pushBytes,maxUses.at(c.assetStem));
        if(!kernels_.emplace(c.assetStem,std::move(kernel)).second)
            throw std::logic_error("26864 duplicate instantiated pipeline");
    }
    if(kernels_.size()!=23u)
        throw std::logic_error("26864 incomplete GPU pipeline registry");
}
bool HdrqPinnedPipelineOwner::owns(const VulkanKernelExecutor* kernel) const noexcept {
    if(!kernel)return false;
    for(const auto& entry:kernels_)
        if(entry.second.get()==kernel)return true;
    return false;
}
VulkanKernelExecutor& HdrqPinnedPipelineOwner::require(const std::string& name) const {
    const auto it=kernels_.find(name);
    if(it==kernels_.end() || !it->second)
        throw std::invalid_argument("26864 unregistered B HDRq pipeline, no A/AMaZE fallback");
    return *it->second;
}
} // namespace iris26864
