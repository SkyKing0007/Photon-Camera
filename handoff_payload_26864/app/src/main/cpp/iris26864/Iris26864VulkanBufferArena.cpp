#include "Iris26864VulkanBufferArena.hpp"
#include <stdexcept>
#include <string>
namespace iris26864 {
namespace {
void requireVk(VkResult r,const char* step) {
    if(r!=VK_SUCCESS)throw std::runtime_error(std::string("26864 HDRq Vulkan buffer ")+step+
                                               " failed: "+std::to_string(int(r)));
}
}
VulkanBufferArena::VulkanBufferArena(VkPhysicalDevice physical,VkDevice device,VkDeviceSize budget)
 :device_(device),budgetBytes_(budget) {
    if(physical==VK_NULL_HANDLE||device==VK_NULL_HANDLE||budget==0)
        throw std::invalid_argument("26864 missing GPU buffer device/budget");
    vkGetPhysicalDeviceMemoryProperties(physical,&memoryProperties_);
    if(!memoryProperties_.memoryTypeCount || memoryProperties_.memoryTypeCount>VK_MAX_MEMORY_TYPES)
        throw std::runtime_error("26864 GPU buffer memory types invalid");
}
VulkanBufferArena::~VulkanBufferArena() {for(auto& e:entries_)release(e);}
void VulkanBufferArena::release(Entry& e) noexcept {
    if(e.buffer!=VK_NULL_HANDLE)vkDestroyBuffer(device_,e.buffer,nullptr);
    if(e.memory!=VK_NULL_HANDLE)vkFreeMemory(device_,e.memory,nullptr);
    e=Entry{};
}
size_t VulkanBufferArena::allocate(VkDeviceSize bytes,VkBufferUsageFlags usage) {
    if(!bytes||entries_.size()>=256 || !(usage&VK_BUFFER_USAGE_STORAGE_BUFFER_BIT) ||
       (usage&~(VK_BUFFER_USAGE_STORAGE_BUFFER_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT|
                VK_BUFFER_USAGE_TRANSFER_SRC_BIT)))
        throw std::invalid_argument("26864 invalid scratch buffer/usage");
    Entry e{};e.size=bytes;
    try {
        VkBufferCreateInfo c{};
        c.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        c.size=bytes;c.usage=usage;c.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        requireVk(vkCreateBuffer(device_,&c,nullptr,&e.buffer),"create");
        VkMemoryRequirements req{};
        vkGetBufferMemoryRequirements(device_,e.buffer,&req);
        if(!req.size||req.size>budgetBytes_-allocatedBytes_)
            throw std::runtime_error("26864 HDRq buffer allocation exceeds hard memory budget");
        uint32_t type=UINT32_MAX;
        for(uint32_t i=0;i<memoryProperties_.memoryTypeCount;++i) {
            if((req.memoryTypeBits&(1u<<i)) &&
               (memoryProperties_.memoryTypes[i].propertyFlags&VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)) {
                type=i;break;
            }
        }
        if(type==UINT32_MAX)throw std::runtime_error("26864 scratch buffer not device-local");
        VkMemoryAllocateInfo a{};a.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        a.allocationSize=req.size;a.memoryTypeIndex=type;
        requireVk(vkAllocateMemory(device_,&a,nullptr,&e.memory),"allocate");
        requireVk(vkBindBufferMemory(device_,e.buffer,e.memory,0),"bind");
        e.bytes=req.size;
        entries_.push_back(e);
        allocatedBytes_+=e.bytes;
        return entries_.size()-1;
    }catch(...){release(e);throw;}
}
TransientBuffer VulkanBufferArena::at(size_t index) const {
    if(index>=entries_.size())throw std::out_of_range("26864 scratch buffer index");
    return {entries_[index].buffer,entries_[index].size};
}
} // namespace iris26864
