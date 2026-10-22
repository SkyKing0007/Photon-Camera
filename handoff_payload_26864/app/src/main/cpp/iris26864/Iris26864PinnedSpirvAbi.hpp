#pragma once
// IRIS_26864_HDRQ_SPIRV_ABI_FAIL_CLOSED_NOT_ANDROID_RUNTIME
// A source-level GPU ABI gate. Unlike five-word host fake modules, shipping
// assets must contain an actual compute entry point, execution mode, typed
// set-0 resources, and push-constant layout. Does NOT replace spirv-val or
// pinned glslangValidator; both are still mandatory before handoff.
#include <vulkan/vulkan.h>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace iris26864 {
struct PinnedSpirvBinding {
 uint32_t binding=0;
 VkDescriptorType descriptor=VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
};
struct PinnedSpirvContract {
 std::string assetStem;
 uint32_t localX=0,localY=0,localZ=1;
 uint32_t pushBytes=0;
 std::vector<PinnedSpirvBinding> bindings;
};
namespace spvabi {
inline void require(bool condition,const char* reason){
 if(!condition)throw std::runtime_error(std::string("26864 pinned SPIR-V rejected: ")+reason);
}
inline std::string decodeString(const uint32_t* w,size_t len) {
 std::string out;
 for(size_t i=0;i<len;++i){
  for(unsigned j=0;j<4;++j){
   char c=char((w[i]>>(8u*j))&0xffu);
   if(c==0)return out;
   out+=c;
  }
 }
 return out;
}
}
// SPIR-V 1.0..1.6 (actual binary, not a GLSL/text or an unverified header).
// Checks instruction length and ID bounds and matches the compiled interface
// to the RAWR shader-specific manifest. No shader-name fallback is allowed.
inline void verifyPinnedSpirv(const std::vector<uint32_t>& w,const PinnedSpirvContract& expected) {
 using spvabi::require;
 require(w.size()>20 && w.size()<=524288u,"not a complete compute binary");
 require(w[0]==0x07230203u,"invalid SPIR-V magic/endianness");
 require((w[1]>>16)==1u && ((w[1]>>8)&255u)<=6u,"unsupported SPIR-V version");
 require(w[3]>4u && w[3]<=0x00100000u && w[4]==0u,"invalid ID bound or schema");
 require(!expected.assetStem.empty() && expected.assetStem.find('/')==std::string::npos &&
         expected.assetStem.find('\\')==std::string::npos &&
         expected.localX>0 && expected.localY>0 && expected.localZ>0,
         "missing pinned shader contract");
 struct Pointer {uint32_t storage=0,pointed=0;};
 struct Type {uint32_t opcode=0;std::vector<uint32_t> arg;};
 struct Variable {uint32_t type=0,storage=0;};
 struct Decoration {int set=-1,binding=-1;};
 std::map<uint32_t,Pointer> ptr;
 std::map<uint32_t,Type> types;
 std::map<uint32_t,Variable> vars;
 std::map<uint32_t,Decoration> dec;
 std::map<std::pair<uint32_t,uint32_t>,uint32_t> memberOffsets;
 std::set<uint32_t> entryIds;
 std::map<uint32_t,std::vector<uint32_t>> localModes;
 bool hasMemoryModel=false;
 uint32_t functionCount=0u, functionEndCount=0u;
 uint32_t lastOp=0u;
 for(size_t i=5;i<w.size();){
  const uint32_t op=w[i]&0xffffu, count=w[i]>>16;
  require(count>0 && count<=w.size()-i,"invalid or truncated instruction");
  const uint32_t* a=w.data()+i+1;
  const size_t n=count-1;
  if(op==14){require(n>=2,"bad memory model");hasMemoryModel=true;}
  if(op==15){
   require(n>=3,"bad compute entry point");
   if(a[0]==5u && spvabi::decodeString(a+2,n-2)=="main")entryIds.insert(a[1]);
  }
  if(op==16){
   require(n>=2,"bad execution mode");
   if(a[1]==17u){require(n==5,"bad LocalSize mode");localModes[a[0]]={a[2],a[3],a[4]};}
  }
  if(op==71){
   require(n>=2,"bad decoration");
   if(a[1]==33u || a[1]==34u){
    require(n>=3 && a[0]<w[3],"invalid descriptor decoration");
    auto& d=dec[a[0]];
    if(a[1]==33u){require(d.binding<0,"repeated binding");d.binding=int(a[2]);}
    else {require(d.set<0,"repeated set");d.set=int(a[2]);}
   }
  }
  if(op==72 && n>=4 && a[2]==35u) {
   require(a[0]<w[3],"invalid push struct ID");
   const auto k=std::make_pair(a[0],a[1]);
   require(memberOffsets.emplace(k,a[3]).second,"duplicate push offset");
  }
  if(op==32){require(n==3 && a[0]<w[3] && a[2]<w[3],"bad pointer type");ptr[a[0]]={a[1],a[2]};}
  if(op==21 || op==22 || op==23 || op==25 || op==27 || op==30) {
   require(n>=1 && a[0]<w[3],"invalid type ID");
   types[a[0]]={op,std::vector<uint32_t>(a+1,a+n)};
  }
  if(op==59) {require(n>=3 && a[0]<w[3] && a[1]<w[3],"bad variable declaration");vars[a[1]]={a[0],a[2]};}
  if(op==54)++functionCount;
  if(op==56)++functionEndCount;
  lastOp=op;
  i+=count;
 }
 require(hasMemoryModel && functionCount>0 && functionCount==functionEndCount && lastOp==56u,
         "fake, truncated or unbalanced executable shader body");
 require(entryIds.size()==1u && localModes.count(*entryIds.begin())==1u,"missing/ambiguous compute main/local size");
 const auto& local=localModes.at(*entryIds.begin());
 require(local.size()==3u && local[0]==expected.localX && local[1]==expected.localY && local[2]==expected.localZ,
         "local workgroup dimensions differ from pinned source");
 std::map<uint32_t,VkDescriptorType> reflected;
 uint32_t pushStruct=0;
 for(const auto& [id,v]:vars){
  const auto p=ptr.find(v.type);
  require(p!=ptr.end() && p->second.storage==v.storage,"variable/pointer storage mismatch");
  if(v.storage==9u){require(pushStruct==0u,"multiple push blocks");pushStruct=p->second.pointed;}
  const auto d=dec.find(id);
  if(d==dec.end() || (d->second.binding<0 && d->second.set<0))continue;
  require(d->second.set==0 && d->second.binding>=0 && d->second.binding<64,"invalid descriptor set/binding");
  VkDescriptorType kind=static_cast<VkDescriptorType>(-1);
  if(v.storage==12u)kind=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
  else if(v.storage==2u)kind=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
  else if(v.storage==0u){
   const auto t=types.find(p->second.pointed);
   require(t!=types.end(),"unknown uniform-constant type");
   const Type* image=&t->second;
   const bool combined=(image->opcode==27u);
   if(combined){
    require(image->arg.size()==1u,"malformed sampled-image type");
    const auto underlying=types.find(image->arg[0]);
    require(underlying!=types.end(),"missing combined-image type");
    image=&underlying->second;
   }
   require(image->opcode==25u && image->arg.size()>=7u,
           "unsupported uniform-constant descriptor kind");
   // OpTypeImage arguments: sampledType, dim, depth, arrayed, ms, sampled, imageFormat
   require(image->arg[1]==1u && image->arg[3]==0u && image->arg[4]==0u &&
           image->arg[5]==(combined?1u:2u), "unexpected image dimension/sample mode");
   kind=combined?VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER:VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
  }
  require(kind!=static_cast<VkDescriptorType>(-1),"unsupported descriptor storage class");
  const uint32_t b=uint32_t(d->second.binding);
  require(reflected.emplace(b,kind).second,"duplicate descriptor location");
 }
 require(reflected.size()==expected.bindings.size(),"descriptor count differs from pinned shader");
 for(const auto& b:expected.bindings){
  const auto it=reflected.find(b.binding);
  require(it!=reflected.end() && it->second==b.descriptor,"descriptor kind/binding differs from pinned shader");
 }
 // Only scalar/vec32 push members are used by the pinned hdrp/hdrq shaders.
 // Reject more complex unproven layouts instead of guessing their ABI.
 uint32_t pushSize=0;
 if(pushStruct!=0){
  const auto st=types.find(pushStruct);
  require(st!=types.end() && st->second.opcode==30u,"invalid push struct");
  for(size_t m=0;m<st->second.arg.size();++m){
   const auto off=memberOffsets.find({pushStruct,uint32_t(m)});
   require(off!=memberOffsets.end(),"push field missing explicit byte offset");
   const auto field=types.find(st->second.arg[m]);
   require(field!=types.end(),"unknown push field type");
   uint32_t bytes=0;
   if(field->second.opcode==21u || field->second.opcode==22u){
    require(!field->second.arg.empty() && field->second.arg[0]==32u,"non-32-bit push scalar");bytes=4;
   } else if(field->second.opcode==23u){
    require(field->second.arg.size()>=2 && field->second.arg[1]>=2u && field->second.arg[1]<=4u,
            "unhandled push vector");
    const auto elem=types.find(field->second.arg[0]);
    require(elem!=types.end() && (elem->second.opcode==21u || elem->second.opcode==22u) &&
            !elem->second.arg.empty() && elem->second.arg[0]==32u,"non-32-bit push vector");
    bytes=4u*field->second.arg[1];
   } else require(false,"complex push member requires audited ABI support");
   require(off->second<=128u && bytes<=128u-off->second,"push field exceeds 128 bytes");
   pushSize=std::max(pushSize,off->second+bytes);
  }
 }
 require(pushSize==expected.pushBytes,"push size/offset differs from pinned RAWR source");
}
} // namespace iris26864
