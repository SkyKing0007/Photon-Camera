#include "SpektraRawVulkanOwner.h"
#include "SpektraEmbeddedShaders.h"

#include <vulkan/vulkan.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstring>
#include <mutex>
#include <sstream>
#include <vector>

namespace iris_spektra {
namespace {

constexpr uint32_t kParamWords = 42u;
constexpr const char* kRawShaderName = "SpektraRawDevelop.comp.spv";

uint32_t floatBits(float v) {
    uint32_t u = 0;
    static_assert(sizeof(u) == sizeof(v), "float bits");
    std::memcpy(&u, &v, sizeof(u));
    return u;
}

std::string vkError(const char* where, VkResult result) {
    std::ostringstream out;
    out << where << " failed VkResult=" << static_cast<int>(result);
    return out.str();
}

struct Buffer {
    VkBuffer buffer = VK_NULL_HANDLE;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    void* mapped = nullptr;
    VkDeviceSize capacity = 0;
};

} // namespace

struct SpektraRawVulkanOwner::Impl {
    std::mutex workMutex;
    std::atomic<bool> savedWaiting{false};
    VkInstance instance = VK_NULL_HANDLE;
    VkPhysicalDevice physical = VK_NULL_HANDLE;
    VkDevice device = VK_NULL_HANDLE;
    uint32_t queueFamily = UINT32_MAX;
    VkQueue queue = VK_NULL_HANDLE;
    VkDescriptorSetLayout descriptorLayout = VK_NULL_HANDLE;
    VkPipelineLayout pipelineLayout = VK_NULL_HANDLE;
    VkPipeline pipeline = VK_NULL_HANDLE;
    VkDescriptorPool descriptorPool = VK_NULL_HANDLE;
    VkDescriptorSet descriptorSet = VK_NULL_HANDLE;
    VkCommandPool commandPool = VK_NULL_HANDLE;
    VkCommandBuffer command = VK_NULL_HANDLE;
    VkFence fence = VK_NULL_HANDLE;
    Buffer raw, params, lsc, output;
    bool initialized = false;
    uint64_t previewProcessed = 0;
    uint64_t previewDropped = 0;
    uint64_t previewMicrosTotal = 0;
    uint64_t lastStillMicros = 0;

    ~Impl() { destroy(); }

    void destroyBuffer(Buffer& b) {
        if (device != VK_NULL_HANDLE && b.memory != VK_NULL_HANDLE && b.mapped) vkUnmapMemory(device, b.memory);
        if (device != VK_NULL_HANDLE && b.buffer != VK_NULL_HANDLE) vkDestroyBuffer(device, b.buffer, nullptr);
        if (device != VK_NULL_HANDLE && b.memory != VK_NULL_HANDLE) vkFreeMemory(device, b.memory, nullptr);
        b = Buffer{};
    }

    void destroy() {
        if (device != VK_NULL_HANDLE) vkDeviceWaitIdle(device);
        destroyBuffer(output); destroyBuffer(lsc); destroyBuffer(params); destroyBuffer(raw);
        if (device != VK_NULL_HANDLE && fence != VK_NULL_HANDLE) vkDestroyFence(device, fence, nullptr);
        if (device != VK_NULL_HANDLE && commandPool != VK_NULL_HANDLE) vkDestroyCommandPool(device, commandPool, nullptr);
        if (device != VK_NULL_HANDLE && descriptorPool != VK_NULL_HANDLE) vkDestroyDescriptorPool(device, descriptorPool, nullptr);
        if (device != VK_NULL_HANDLE && pipeline != VK_NULL_HANDLE) vkDestroyPipeline(device, pipeline, nullptr);
        if (device != VK_NULL_HANDLE && pipelineLayout != VK_NULL_HANDLE) vkDestroyPipelineLayout(device, pipelineLayout, nullptr);
        if (device != VK_NULL_HANDLE && descriptorLayout != VK_NULL_HANDLE) vkDestroyDescriptorSetLayout(device, descriptorLayout, nullptr);
        if (device != VK_NULL_HANDLE) vkDestroyDevice(device, nullptr);
        if (instance != VK_NULL_HANDLE) vkDestroyInstance(instance, nullptr);
        instance = VK_NULL_HANDLE; physical = VK_NULL_HANDLE; device = VK_NULL_HANDLE; queue = VK_NULL_HANDLE;
        descriptorLayout = VK_NULL_HANDLE; pipelineLayout = VK_NULL_HANDLE; pipeline = VK_NULL_HANDLE;
        descriptorPool = VK_NULL_HANDLE; descriptorSet = VK_NULL_HANDLE; commandPool = VK_NULL_HANDLE;
        command = VK_NULL_HANDLE; fence = VK_NULL_HANDLE; queueFamily = UINT32_MAX; initialized = false;
    }

    bool memoryType(uint32_t typeBits, VkMemoryPropertyFlags required, uint32_t* out) const {
        VkPhysicalDeviceMemoryProperties props{};
        vkGetPhysicalDeviceMemoryProperties(physical, &props);
        for (uint32_t i = 0; i < props.memoryTypeCount; ++i) {
            if ((typeBits & (1u << i)) != 0u && (props.memoryTypes[i].propertyFlags & required) == required) {
                *out = i; return true;
            }
        }
        return false;
    }

    bool ensureBuffer(Buffer& b, VkDeviceSize needed, std::string* error) {
        needed = std::max<VkDeviceSize>(needed, 16u);
        if (b.buffer != VK_NULL_HANDLE && b.capacity >= needed) return true;
        destroyBuffer(b);
        VkDeviceSize capacity = 4096u;
        while (capacity < needed) capacity = std::max(capacity * 2u, needed);
        VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bi.size = capacity;
        bi.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
        bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        VkResult r = vkCreateBuffer(device, &bi, nullptr, &b.buffer);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateBuffer", r); return false; }
        VkMemoryRequirements req{};
        vkGetBufferMemoryRequirements(device, b.buffer, &req);
        uint32_t memoryIndex = 0;
        if (!memoryType(req.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, &memoryIndex)) {
            if (error) *error = "No HOST_VISIBLE|HOST_COHERENT Vulkan memory type for Spektra RAW buffers";
            return false;
        }
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = memoryIndex;
        r = vkAllocateMemory(device, &ai, nullptr, &b.memory);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkAllocateMemory", r); return false; }
        r = vkBindBufferMemory(device, b.buffer, b.memory, 0);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkBindBufferMemory", r); return false; }
        r = vkMapMemory(device, b.memory, 0, capacity, 0, &b.mapped);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkMapMemory", r); return false; }
        b.capacity = capacity;
        return true;
    }

    bool updateDescriptors(std::string* error) {
        Buffer* buffers[4] = {&raw, &params, &lsc, &output};
        VkDescriptorBufferInfo infos[4]{};
        VkWriteDescriptorSet writes[4]{};
        for (uint32_t i = 0; i < 4; ++i) {
            infos[i].buffer = buffers[i]->buffer;
            infos[i].offset = 0;
            infos[i].range = buffers[i]->capacity;
            writes[i] = VkWriteDescriptorSet{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
            writes[i].dstSet = descriptorSet;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            writes[i].pBufferInfo = &infos[i];
        }
        if (descriptorSet == VK_NULL_HANDLE) { if (error) *error = "Spektra descriptor set missing"; return false; }
        vkUpdateDescriptorSets(device, 4, writes, 0, nullptr);
        return true;
    }

    bool initialize(std::string* error) {
        if (initialized) return true;
        destroy();
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        app.pApplicationName = "IrisSpektraRaw";
        app.applicationVersion = 26686;
        app.pEngineName = "IrisSpektraRaw";
        app.engineVersion = 1;
        app.apiVersion = VK_API_VERSION_1_0;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo = &app;
        VkResult r = vkCreateInstance(&ici, nullptr, &instance);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateInstance", r); destroy(); return false; }
        uint32_t physicalCount = 0;
        r = vkEnumeratePhysicalDevices(instance, &physicalCount, nullptr);
        if (r != VK_SUCCESS || physicalCount == 0) { if (error) *error = "No Vulkan physical device"; destroy(); return false; }
        std::vector<VkPhysicalDevice> physicals(physicalCount);
        vkEnumeratePhysicalDevices(instance, &physicalCount, physicals.data());
        physical = physicals[0];
        uint32_t familyCount = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(physical, &familyCount, nullptr);
        std::vector<VkQueueFamilyProperties> families(familyCount);
        vkGetPhysicalDeviceQueueFamilyProperties(physical, &familyCount, families.data());
        for (uint32_t i = 0; i < familyCount; ++i) {
            if ((families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) != 0u) { queueFamily = i; break; }
        }
        if (queueFamily == UINT32_MAX) { if (error) *error = "No Vulkan compute queue"; destroy(); return false; }
        float priority = 1.0f;
        VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qci.queueFamilyIndex = queueFamily; qci.queueCount = 1; qci.pQueuePriorities = &priority;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount = 1; dci.pQueueCreateInfos = &qci;
        r = vkCreateDevice(physical, &dci, nullptr, &device);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateDevice", r); destroy(); return false; }
        vkGetDeviceQueue(device, queueFamily, 0, &queue);

        VkDescriptorSetLayoutBinding bindings[4]{};
        for (uint32_t i = 0; i < 4; ++i) {
            bindings[i].binding = i;
            bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            bindings[i].descriptorCount = 1;
            bindings[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        }
        VkDescriptorSetLayoutCreateInfo dl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        dl.bindingCount = 4; dl.pBindings = bindings;
        r = vkCreateDescriptorSetLayout(device, &dl, nullptr, &descriptorLayout);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateDescriptorSetLayout", r); destroy(); return false; }
        VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pli.setLayoutCount = 1; pli.pSetLayouts = &descriptorLayout;
        r = vkCreatePipelineLayout(device, &pli, nullptr, &pipelineLayout);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreatePipelineLayout", r); destroy(); return false; }

        size_t shaderCount = 0;
        const EmbeddedShader* shaders = embeddedShaders(&shaderCount);
        const EmbeddedShader* rawShader = nullptr;
        for (size_t i = 0; i < shaderCount; ++i) {
            if (shaders[i].name && std::strcmp(shaders[i].name, kRawShaderName) == 0) { rawShader = &shaders[i]; break; }
        }
        if (!rawShader || rawShader->bytes == 0 || (rawShader->bytes & 3u) != 0u) {
            if (error) *error = "Embedded SpektraRawDevelop.comp.spv missing or malformed"; destroy(); return false;
        }
        std::vector<uint32_t> code(rawShader->bytes / 4u);
        std::memcpy(code.data(), rawShader->data, rawShader->bytes);
        VkShaderModuleCreateInfo sm{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
        sm.codeSize = rawShader->bytes; sm.pCode = code.data();
        VkShaderModule module = VK_NULL_HANDLE;
        r = vkCreateShaderModule(device, &sm, nullptr, &module);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateShaderModule", r); destroy(); return false; }
        VkPipelineShaderStageCreateInfo stage{VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};
        stage.stage = VK_SHADER_STAGE_COMPUTE_BIT; stage.module = module; stage.pName = "main";
        VkComputePipelineCreateInfo cp{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
        cp.stage = stage; cp.layout = pipelineLayout;
        r = vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &cp, nullptr, &pipeline);
        vkDestroyShaderModule(device, module, nullptr);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateComputePipelines", r); destroy(); return false; }

        VkDescriptorPoolSize ps{}; ps.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER; ps.descriptorCount = 4;
        VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        dpi.maxSets = 1; dpi.poolSizeCount = 1; dpi.pPoolSizes = &ps;
        r = vkCreateDescriptorPool(device, &dpi, nullptr, &descriptorPool);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateDescriptorPool", r); destroy(); return false; }
        VkDescriptorSetAllocateInfo dai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        dai.descriptorPool = descriptorPool; dai.descriptorSetCount = 1; dai.pSetLayouts = &descriptorLayout;
        r = vkAllocateDescriptorSets(device, &dai, &descriptorSet);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkAllocateDescriptorSets", r); destroy(); return false; }
        VkCommandPoolCreateInfo cpi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        cpi.queueFamilyIndex = queueFamily; cpi.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        r = vkCreateCommandPool(device, &cpi, nullptr, &commandPool);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateCommandPool", r); destroy(); return false; }
        VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        cai.commandPool = commandPool; cai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; cai.commandBufferCount = 1;
        r = vkAllocateCommandBuffers(device, &cai, &command);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkAllocateCommandBuffers", r); destroy(); return false; }
        VkFenceCreateInfo fi{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        r = vkCreateFence(device, &fi, nullptr, &fence);
        if (r != VK_SUCCESS) { if (error) *error = vkError("vkCreateFence", r); destroy(); return false; }
        initialized = true;
        return true;
    }

    bool validate(const RawDevelopRequest& q, std::string* error) const {
        auto fail = [&](const char* m){ if(error)*error=m; return false; };
        if (!q.source || q.sourceBytes == 0 || q.sourceWidth <= 1 || q.sourceHeight <= 1 || q.rowStride <= 0) return fail("Invalid packed RAW input");
        if (q.format != 32 && q.format != 37 && q.format != 38) return fail("Unsupported packed RAW format");
        const int minRow = q.format == 37 ? ((q.sourceWidth + 3) / 4) * 5
                : q.format == 38 ? ((q.sourceWidth + 1) / 2) * 3
                : q.sourceWidth * std::max(2, q.pixelStride);
        const uint64_t requiredBytes = static_cast<uint64_t>(q.sourceHeight - 1)
                * static_cast<uint64_t>(q.rowStride) + static_cast<uint64_t>(minRow);
        if (q.rowStride < minRow || requiredBytes > q.sourceBytes) return fail("Packed RAW row-stride/buffer contract mismatch");
        if (q.cfaArrangement < 0 || q.cfaArrangement > 3 || q.bayerOffset < 0 || q.bayerOffset > 3) return fail("Unresolved CFA/Bayer origin");
        if (q.whiteLevel <= 0 || q.outputWidth <= 0 || q.outputHeight <= 0) return fail("Invalid RAW/output levels");
        if (q.rawBounds[0] < 0 || q.rawBounds[1] < 0 || q.rawBounds[2] > q.sourceWidth || q.rawBounds[3] > q.sourceHeight
                || q.rawBounds[2] <= q.rawBounds[0] || q.rawBounds[3] <= q.rawBounds[1]) return fail("Invalid RAW bounds");
        const int* domains[2] = {q.sourceCrop, q.activeRawDomain};
        for (const int* r : domains) {
            if (r[0] < q.rawBounds[0] || r[1] < q.rawBounds[1] || r[2] > q.rawBounds[2] || r[3] > q.rawBounds[3]
                    || r[2] <= r[0] || r[3] <= r[1]) return fail("RAW domains disagree");
        }
        if (q.activeRawDomain[2] - q.activeRawDomain[0] < 2
                || q.activeRawDomain[3] - q.activeRawDomain[1] < 2) return fail("Active RAW domain cannot preserve CFA phase");
        if (q.lensShading && (q.lensShadingRows <= 0 || q.lensShadingCols <= 0)) return fail("Invalid lens shading dimensions");
        return true;
    }

    bool run(const RawDevelopRequest& q, std::vector<uint8_t>* rgba16f, std::string* error) {
        if (!validate(q, error) || !initialize(error)) return false;
        const size_t rawPadded = (q.sourceBytes + 3u) & ~size_t(3u);
        const size_t lscFloats = q.lensShading && q.lensShadingRows > 0 && q.lensShadingCols > 0
                ? static_cast<size_t>(q.lensShadingRows) * q.lensShadingCols * 4u : 4u;
        const size_t lscBytes = lscFloats * sizeof(float);
        const size_t outputBytes = static_cast<size_t>(q.outputWidth) * q.outputHeight * 8u;
        if (!ensureBuffer(raw, rawPadded, error) || !ensureBuffer(params, kParamWords * sizeof(uint32_t), error)
                || !ensureBuffer(lsc, lscBytes, error) || !ensureBuffer(output, outputBytes, error)) return false;
        std::memcpy(raw.mapped, q.source, q.sourceBytes);
        if (rawPadded > q.sourceBytes) {
            std::memset(static_cast<uint8_t*>(raw.mapped) + q.sourceBytes, 0, rawPadded - q.sourceBytes);
        }
        std::vector<uint32_t> words(kParamWords, 0u);
        words[0]=q.sourceWidth; words[1]=q.sourceHeight; words[2]=q.rowStride; words[3]=q.pixelStride;
        words[4]=q.format; words[5]=static_cast<uint32_t>(q.sourceBytes);
        for(int i=0;i<4;i++){ words[6+i]=static_cast<uint32_t>(q.sourceCrop[i]); words[10+i]=static_cast<uint32_t>(q.rawBounds[i]); words[14+i]=static_cast<uint32_t>(q.activeRawDomain[i]); }
        words[18]=static_cast<uint32_t>(q.cfaArrangement); words[19]=static_cast<uint32_t>(q.bayerOffset); words[20]=static_cast<uint32_t>(q.whiteLevel);
        for(int i=0;i<4;i++) words[21+i]=static_cast<uint32_t>(std::max(0,q.blackLevel4[i]));
        words[25]=static_cast<uint32_t>(std::max(0,q.lensShadingCols)); words[26]=static_cast<uint32_t>(std::max(0,q.lensShadingRows));
        words[27]=q.lensShading ? 1u : 0u; words[28]=q.outputWidth; words[29]=q.outputHeight; words[30]=q.savedPhoto?1u:0u;
        words[31]=floatBits(q.chromaDenoiseStrength); words[32]=floatBits(q.sensorClipThreshold);
        for(int i=0;i<9;i++) words[33+i]=floatBits(q.sensorToLinearSrgb[i]);
        std::memcpy(params.mapped, words.data(), words.size()*sizeof(uint32_t));
        if (q.lensShading) std::memcpy(lsc.mapped, q.lensShading, lscBytes);
        else { float unity[4]={1.f,1.f,1.f,1.f}; std::memcpy(lsc.mapped, unity, sizeof(unity)); }
        if (!updateDescriptors(error)) return false;
        vkResetFences(device,1,&fence);
        vkResetCommandBuffer(command,0);
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        VkResult r=vkBeginCommandBuffer(command,&bi);
        if(r!=VK_SUCCESS){if(error)*error=vkError("vkBeginCommandBuffer",r);return false;}
        vkCmdBindPipeline(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
        vkCmdBindDescriptorSets(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipelineLayout,0,1,&descriptorSet,0,nullptr);
        vkCmdDispatch(command,(static_cast<uint32_t>(q.outputWidth)+7u)/8u,(static_cast<uint32_t>(q.outputHeight)+7u)/8u,1u);
        VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        barrier.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT; barrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
        vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&barrier,0,nullptr,0,nullptr);
        r=vkEndCommandBuffer(command);
        if(r!=VK_SUCCESS){if(error)*error=vkError("vkEndCommandBuffer",r);return false;}
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO}; si.commandBufferCount=1; si.pCommandBuffers=&command;
        r=vkQueueSubmit(queue,1,&si,fence);
        if(r!=VK_SUCCESS){if(error)*error=vkError("vkQueueSubmit",r);return false;}
        r=vkWaitForFences(device,1,&fence,VK_TRUE,UINT64_MAX);
        if(r!=VK_SUCCESS){if(error)*error=vkError("vkWaitForFences",r);return false;}
        rgba16f->resize(outputBytes);
        std::memcpy(rgba16f->data(),output.mapped,outputBytes);
        return true;
    }
};

SpektraRawVulkanOwner& SpektraRawVulkanOwner::instance() {
    static SpektraRawVulkanOwner owner;
    return owner;
}

SpektraRawVulkanOwner::SpektraRawVulkanOwner() : impl_(new Impl()) {}
SpektraRawVulkanOwner::~SpektraRawVulkanOwner() { delete impl_; }

bool SpektraRawVulkanOwner::process(const RawDevelopRequest& request, std::vector<uint8_t>* rgba16f,
        bool* previewDropped, double* elapsedMicros, std::string* error) {
    if (previewDropped) *previewDropped=false;
    const auto start=std::chrono::steady_clock::now();
    std::unique_lock<std::mutex> lock(impl_->workMutex,std::defer_lock);
    if (request.savedPhoto) {
        impl_->savedWaiting.store(true,std::memory_order_release);
        lock.lock();
        impl_->savedWaiting.store(false,std::memory_order_release);
    } else {
        if (impl_->savedWaiting.load(std::memory_order_acquire) || !lock.try_lock()) {
            impl_->previewDropped++;
            if (previewDropped) *previewDropped=true;
            return true;
        }
    }
    bool ok=impl_->run(request,rgba16f,error);
    const auto stop=std::chrono::steady_clock::now();
    const uint64_t micros=static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::microseconds>(stop-start).count());
    if (elapsedMicros) *elapsedMicros=static_cast<double>(micros);
    if (request.savedPhoto) impl_->lastStillMicros=micros;
    else if (ok) { impl_->previewProcessed++; impl_->previewMicrosTotal+=micros; }
    return ok;
}

void SpektraRawVulkanOwner::release() {
    std::lock_guard<std::mutex> lock(impl_->workMutex);
    impl_->destroy();
}

void SpektraRawVulkanOwner::stats(uint64_t out[6]) {
    std::lock_guard<std::mutex> lock(impl_->workMutex);
    out[0]=impl_->previewProcessed;
    out[1]=impl_->previewDropped;
    out[2]=impl_->previewProcessed ? impl_->previewMicrosTotal/impl_->previewProcessed : 0;
    out[3]=impl_->lastStillMicros;
    out[4]=impl_->initialized ? 1u : 0u;
    out[5]=impl_->initialized ? 4u : 0u;
}

} // namespace iris_spektra
