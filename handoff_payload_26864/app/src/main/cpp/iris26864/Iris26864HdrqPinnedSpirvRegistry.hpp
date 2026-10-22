#pragma once
// IRIS_26864_HDRQ_EXACT_SHADER_REGISTRY_NO_FALLBACK_NOT_RUNTIME
// Immutable manifest of pinned RAWR 16.5.0 Vulkan source kernel interfaces.
// The compiled binaries do not exist in this isolated development checkpoint.
// They MUST be built by pinned real glslangValidator, verified, shipped as one
// matched SPIR-V set, and must pass verifyPinnedSpirv before pipeline creation.
#include "Iris26864PinnedSpirvAbi.hpp"
#include <functional>
#include <stdexcept>
#include <vector>
#include <cstring>
namespace iris26864 {
inline const std::vector<PinnedSpirvContract>& pinnedHdrqContracts(){
 using B=PinnedSpirvBinding;
 constexpr VkDescriptorType I=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, S=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
 static const std::vector<PinnedSpirvContract> entries{
  {"hdrp_prepare",16,16,1,60,{{0,I},{1,I}}},
  {"hdrp_avg_pool",16,16,1,12,{{0,I},{1,I}}},
  {"hdrp_blur",16,16,1,40,{{0,I},{1,I}}},
  {"hdrp_upsample_align",16,16,1,24,{{0,S},{1,S}}},
  {"hdrp_correct_upsampling",64,1,1,32,{{0,I},{1,I},{2,S},{3,S}}},
  {"hdrp_tile_diff",256,1,1,32,{{0,I},{1,I},{2,S},{3,S}}},
  {"hdrp_best_tile",16,16,1,12,{{0,S},{1,S},{2,S}}},
  {"hdrq_shift_table",64,1,1,0,{{0,S}}},
  {"hdrq_to_rgba",16,16,1,32,{{0,I},{1,I}}},
  {"hdrq_rms",16,16,1,8,{{0,I},{1,I}}},
  {"hdrq_seed_dft",8,8,1,8,{{0,I},{1,I},{2,I}}},
  {"hdrq_forward_dft",8,8,1,8,{{0,I},{1,I}}},
  {"hdrq_warp_rgba",16,16,1,68,{{0,I},{1,I},{2,S},{3,I}}},
  {"hdrq_mismatch",16,16,1,20,{{0,I},{1,I},{2,I},{3,I}}},
  {"hdrq_region_mean",256,1,1,16,{{0,I},{1,S}}},
  {"hdrq_mismatch_norm",16,16,1,12,{{0,I},{1,I},{2,S}}},
  {"hdrq_highlights_norm",16,16,1,20,{{0,I},{1,I}}},
  {"hdrq_merge",8,8,1,28,{{0,I},{1,I},{2,I},{3,I},{4,I},{5,S},{6,I},{7,I}}},
  {"hdrq_deconvolute",8,8,1,8,{{0,I},{1,I}}},
  {"hdrq_backward_dft",8,8,1,12,{{0,I},{1,I}}},
  {"hdrq_border",16,16,1,12,{{0,I},{1,I}}},
  {"hdrq_accumulate",16,16,1,20,{{0,I},{1,I}}},
  {"hdrp_finalize",16,16,1,32,{{0,I},{1,I},{2,I}}}
 };
 (void)sizeof(B);
 return entries;
}
using PinnedSpirvBytesProvider=std::function<std::vector<uint8_t>(const std::string& exactPath)>;
struct NamedSpirv {std::string name;std::vector<uint32_t> words;};
inline std::vector<NamedSpirv> requireCompletePinnedHdrqSpirv(const PinnedSpirvBytesProvider& provider){
 if(!provider)throw std::invalid_argument("26864 missing compiled RAWR shader provider");
 std::vector<NamedSpirv> out;
 const auto& list=pinnedHdrqContracts();
 std::set<std::string> names;
 for(const auto& c:list){
  if(!names.insert(c.assetStem).second)
   throw std::runtime_error("26864 duplicate pinned shader in registry");
  const std::string path="iris26864/rawr/hdrq/spv/"+c.assetStem+".spv";
  const auto bytes=provider(path);
  if(bytes.size()<84u || bytes.size()>2097152u || bytes.size()%4u)
   throw std::runtime_error("26864 missing/incomplete SPIR-V (no shader fallback): "+path);
  std::vector<uint32_t> words(bytes.size()/4u);
  std::memcpy(words.data(),bytes.data(),bytes.size());
  verifyPinnedSpirv(words,c);
  out.push_back({c.assetStem,std::move(words)});
 }
 if(out.size()!=23u)throw std::logic_error("26864 incomplete HDRq pinned shader list");
 return out;
}
} // namespace iris26864
