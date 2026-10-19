// IRIS_26856_B_ONLY_GL_VULKAN_AMAZE_JNI_OWNER
// Single GL-thread ownership boundary. No CPU pixel mapping or fallback.
#include "amaze/Amaze.hpp"
#include "amaze/CommandSubmissionOwner.hpp"
#include "amaze/ExternalFenceSync.hpp"
#include "amaze/HardwareBufferImport.hpp"
#include "amaze/PinnedSpirvAssets.hpp"
#include "amaze/VulkanDeviceOwner.hpp"

#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/api-level.h>
#include <android/hardware_buffer.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <GLES2/gl2ext.h>
#include <array>
#include <cmath>
#include <utility>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
using namespace amaze;
struct ScopedAHB {
    AHardwareBuffer* buffer = nullptr;
    ~ScopedAHB() { if (buffer) AHardwareBuffer_release(buffer); }
    ScopedAHB(const ScopedAHB&) = delete;
    ScopedAHB& operator=(const ScopedAHB&) = delete;
    ScopedAHB() = default;
    ScopedAHB(ScopedAHB&& from) noexcept : buffer(from.buffer) { from.buffer = nullptr; }
    ScopedAHB& operator=(ScopedAHB&& from) noexcept {
        if (this != &from) {
            if (buffer) AHardwareBuffer_release(buffer);
            buffer = from.buffer; from.buffer = nullptr;
        }
        return *this;
    }
    AHardwareBuffer* get() const noexcept { return buffer; }
};
ScopedAHB createAhb(uint32_t w, uint32_t h, bool storage) {
    if (android_get_device_api_level() < 29)
        throw std::runtime_error("26856 Vulkan AHB usage requires Android API 29+");
    AHardwareBuffer_Desc desc{};
    desc.width = w; desc.height = h; desc.layers = 1;
    desc.format = AHARDWAREBUFFER_FORMAT_R16G16B16A16_FLOAT;
    desc.usage = AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE |
                 AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT |
                 (storage ? AHARDWAREBUFFER_USAGE_GPU_DATA_BUFFER : 0ull);
    // AHardwareBuffer_isSupported is API 29 and unavailable when this app's
    // native minSdk is API 26. The API-26 allocation is the authoritative
    // capability/availability check, and does not require a second AHB.
    // Keep the existing runtime API 29 guard, exact RGBA16F descriptor,
    // GPU-only ownership, and fail-closed behavior on allocation failure.
    ScopedAHB owned;
    if (AHardwareBuffer_allocate(&desc, &owned.buffer) != 0 || !owned.buffer)
        throw std::runtime_error("26856 exact RGBA16F AHB allocation unsupported or failed");
    return owned;
}
// AHardwareBuffer is already refcounted; use a move-only scope wrapper.
struct ScopeVkSemaphore {
    VkDevice device = VK_NULL_HANDLE;
    VkSemaphore semaphore = VK_NULL_HANDLE;
    ScopeVkSemaphore(VkDevice d, VkSemaphore s) : device(d), semaphore(s) {}
    ~ScopeVkSemaphore() { if (semaphore) vkDestroySemaphore(device, semaphore, nullptr); }
    ScopeVkSemaphore(const ScopeVkSemaphore&) = delete;
    ScopeVkSemaphore& operator=(const ScopeVkSemaphore&) = delete;
};
void imageBarrier(VkCommandBuffer cmd, VkImage image,
                  VkImageLayout oldLayout, VkImageLayout newLayout,
                  uint32_t from, uint32_t to,
                  VkAccessFlags sourceAccess, VkAccessFlags targetAccess,
                  VkPipelineStageFlags sourceStage, VkPipelineStageFlags targetStage) {
    VkImageMemoryBarrier b{};
    b.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    b.oldLayout = oldLayout;
    b.newLayout = newLayout;
    b.srcQueueFamilyIndex = from;
    b.dstQueueFamilyIndex = to;
    b.srcAccessMask = sourceAccess;
    b.dstAccessMask = targetAccess;
    b.image = image;
    b.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cmd, sourceStage, targetStage, 0, 0, nullptr, 0, nullptr, 1, &b);
}
struct GlBufferImage final {
    EGLDisplay display = EGL_NO_DISPLAY;
    EGLImageKHR image = EGL_NO_IMAGE_KHR;
    GLuint texture = 0;
    PFNEGLDESTROYIMAGEKHRPROC destroyImage = nullptr;
    GlBufferImage(AHardwareBuffer* ahb) {
        display = eglGetCurrentDisplay();
        if (display == EGL_NO_DISPLAY || eglGetCurrentContext() == EGL_NO_CONTEXT)
            throw std::runtime_error("26856 AHB->GL requires current EGL context");
        auto getClient = reinterpret_cast<PFNEGLGETNATIVECLIENTBUFFERANDROIDPROC>(
            eglGetProcAddress("eglGetNativeClientBufferANDROID"));
        auto createImage = reinterpret_cast<PFNEGLCREATEIMAGEKHRPROC>(
            eglGetProcAddress("eglCreateImageKHR"));
        destroyImage = reinterpret_cast<PFNEGLDESTROYIMAGEKHRPROC>(
            eglGetProcAddress("eglDestroyImageKHR"));
        auto targetImage = reinterpret_cast<PFNGLEGLIMAGETARGETTEXTURE2DOESPROC>(
            eglGetProcAddress("glEGLImageTargetTexture2DOES"));
        if (!getClient || !createImage || !destroyImage || !targetImage)
            throw std::runtime_error("26856 AHB->GL EGLImage import functions unavailable");
        EGLClientBuffer client = getClient(ahb);
        if (!client) throw std::runtime_error("26856 AHB->GL client buffer invalid");
        const EGLint attrs[] = {EGL_IMAGE_PRESERVED_KHR, EGL_TRUE, EGL_NONE};
        image = createImage(display, EGL_NO_CONTEXT, EGL_NATIVE_BUFFER_ANDROID, client, attrs);
        if (image == EGL_NO_IMAGE_KHR)
            throw std::runtime_error("26856 AHB->GL EGLImage creation failed");
        GLint former = 0;
        glGetIntegerv(GL_TEXTURE_BINDING_2D, &former);
        try {
            glGenTextures(1, &texture);
            if (!texture) throw std::runtime_error("26856 AHB->GL texture allocation failed");
            glBindTexture(GL_TEXTURE_2D, texture);
            targetImage(GL_TEXTURE_2D, image);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
            if (glGetError() != GL_NO_ERROR)
                throw std::runtime_error("26856 AHB->GL EGLImage texture binding failed");
            glBindTexture(GL_TEXTURE_2D, static_cast<GLuint>(former));
        } catch (...) {
            glBindTexture(GL_TEXTURE_2D, static_cast<GLuint>(former));
            if (texture) { glDeleteTextures(1, &texture); texture = 0; }
            if (image != EGL_NO_IMAGE_KHR) { destroyImage(display, image); image = EGL_NO_IMAGE_KHR; }
            throw;
        }
    }
    ~GlBufferImage() {
        if (texture) glDeleteTextures(1, &texture);
        if (image != EGL_NO_IMAGE_KHR && destroyImage) destroyImage(display, image);
    }
    GlBufferImage(const GlBufferImage&) = delete;
    GlBufferImage& operator=(const GlBufferImage&) = delete;
};
void blitTexture(GLuint source, GLuint destination, uint32_t width, uint32_t height) {
    GLint previousRead = 0, previousDraw = 0;
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &previousRead);
    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &previousDraw);
    // glBlitFramebuffer obeys GL_SCISSOR_TEST. A user-visible crop or an
    // inherited thumbnail scissor must never truncate the camera-linear CFA
    // input or AMaZE RGB result. Restore the caller's state on every exit.
    const GLboolean previousScissor = glIsEnabled(GL_SCISSOR_TEST);
    if (previousScissor) glDisable(GL_SCISSOR_TEST);
    GLuint fbos[2]{};
    glGenFramebuffers(2, fbos);
    if (!fbos[0] || !fbos[1]) {
        glDeleteFramebuffers(2, fbos);
        if (previousScissor) glEnable(GL_SCISSOR_TEST);
        throw std::runtime_error("26856 GL copy framebuffer allocation failed");
    }
    bool good = false;
    glBindFramebuffer(GL_READ_FRAMEBUFFER, fbos[0]);
    glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                           GL_TEXTURE_2D, source, 0);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbos[1]);
    glFramebufferTexture2D(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                           GL_TEXTURE_2D, destination, 0);
    if (glCheckFramebufferStatus(GL_READ_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE &&
        glCheckFramebufferStatus(GL_DRAW_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE) {
        glReadBuffer(GL_COLOR_ATTACHMENT0);
        const GLenum drawAttachment = GL_COLOR_ATTACHMENT0;
        glDrawBuffers(1, &drawAttachment);
        glBlitFramebuffer(0, 0, width, height, 0, 0, width, height, GL_COLOR_BUFFER_BIT, GL_NEAREST);
        good = glGetError() == GL_NO_ERROR;
    }
    glBindFramebuffer(GL_READ_FRAMEBUFFER, static_cast<GLuint>(previousRead));
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, static_cast<GLuint>(previousDraw));
    glDeleteFramebuffers(2, fbos);
    if (previousScissor) glEnable(GL_SCISSOR_TEST);
    if (!good) throw std::runtime_error("26856 RGBA16F GPU framebuffer copy failed");
}
void runAmazeGlFrame(AAssetManager* assets, GLuint packedGlTexture, GLuint outputGlTexture,
                     uint32_t width, uint32_t height, BayerPattern pattern,
                     const std::array<float,3>& gains) {
    if (!assets || !packedGlTexture || !outputGlTexture || packedGlTexture == outputGlTexture ||
        width < 32u || height < 32u || (width & 1u) || (height & 1u) ||
        width > 16384u || height > 16384u)
        throw std::runtime_error("26856 B invalid AMaZE frame geometry/texture ownership");
    for (float gain : gains) if (!(gain > 0.0f) || !std::isfinite(gain))
        throw std::runtime_error("26856 B invalid white balance");
    VulkanDeviceOwner device;
    const VulkanContext ctx = device.context();
    ScopedAHB inputAhb = createAhb(width / 2, height / 2, false);
    ScopedAHB outputAhb = createAhb(width, height, true);
    HardwareBufferImport input(ctx.physicalDevice, ctx.device, inputAhb.get(), width / 2, height / 2,
                               VK_IMAGE_USAGE_SAMPLED_BIT);
    HardwareBufferImport output(ctx.physicalDevice, ctx.device, outputAhb.get(), width, height,
                                VK_IMAGE_USAGE_STORAGE_BIT);
    CommandSubmissionOwner commands(ctx.physicalDevice, ctx.device, device.queue(), ctx.queueFamilyIndex);
    // Images were newly created with UNDEFINED layout. Initialize and transfer
    // ownership BEFORE GLES writes packed temporal CFA; changing from UNDEFINED
    // after GLES writes would discard that CFA and is forbidden.
    commands.execute([&](VkCommandBuffer cmd) {
        for (VkImage image : {input.image(), output.image()})
            imageBarrier(cmd, image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL,
                         ctx.queueFamilyIndex, VK_QUEUE_FAMILY_FOREIGN_EXT,
                         0, 0, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
    });
    GlBufferImage glIn(inputAhb.get());
    GlBufferImage glOut(outputAhb.get());
    blitTexture(packedGlTexture, glIn.texture, width/2, height/2);
    ScopedNativeFd glCfaFence = createCurrentGlReleaseFence();
    ScopeVkSemaphore acquire(ctx.device, importGlFenceToVulkan(ctx.device, std::move(glCfaFence)));
    ScopeVkSemaphore release(ctx.device, createGlExportableSemaphore(ctx.device));
    PipelineConfig cfg{};
    cfg.width = width; cfg.height = height; cfg.pattern = pattern;
    cfg.inputMode = InputMode::PackedCfaRgba16fImage;
    cfg.tileSlots = 16;
    auto provider = makePinnedSpirvProvider(assets);
    AmazePipeline pipeline(ctx, std::move(provider), cfg);
    PackedCfaImageView packed{};
    packed.image = input.image(); packed.view = input.view();
    packed.width = width/2; packed.height = height/2;
    packed.rawWidth = width; packed.rawHeight = height; packed.pattern = pattern;
    packed.format = VK_FORMAT_R16G16B16A16_SFLOAT;
    packed.layout = VK_IMAGE_LAYOUT_GENERAL;
    LinearRgbImage rgb{};
    rgb.image = output.image(); rgb.view = output.view();
    rgb.width = width; rgb.height = height;
    rgb.format = VK_FORMAT_R16G16B16A16_SFLOAT;
    rgb.layout = VK_IMAGE_LAYOUT_GENERAL;
    commands.execute([&](VkCommandBuffer cmd) {
        imageBarrier(cmd, input.image(), VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
                     VK_QUEUE_FAMILY_FOREIGN_EXT, ctx.queueFamilyIndex, 0,
                     VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                     VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
        imageBarrier(cmd, output.image(), VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
                     VK_QUEUE_FAMILY_FOREIGN_EXT, ctx.queueFamilyIndex, 0,
                     VK_ACCESS_SHADER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                     VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
        pipeline.record(cmd, packed, rgb, gains);
        imageBarrier(cmd, input.image(), VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
                     ctx.queueFamilyIndex, VK_QUEUE_FAMILY_FOREIGN_EXT,
                     VK_ACCESS_SHADER_READ_BIT, 0, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                     VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
        imageBarrier(cmd, output.image(), VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL,
                     ctx.queueFamilyIndex, VK_QUEUE_FAMILY_FOREIGN_EXT,
                     VK_ACCESS_SHADER_WRITE_BIT, 0, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                     VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
    }, acquire.semaphore, release.semaphore);
    ScopedNativeFd gpuRgbFence = exportVulkanFenceToGl(ctx.device, release.semaphore);
    waitCurrentGlOnVulkanFence(std::move(gpuRgbFence));
    blitTexture(glOut.texture, outputGlTexture, width, height);
    glFlush();
    // Current GL frame still owns glOut; completion is mandatory before AHB
    // import destructors can reclaim the backing allocations.
    glFinish();
}
} // namespace
extern "C" JNIEXPORT void JNICALL
Java_com_hinnka_mycamera_processor_GlesIris26856AmazeNative_nativeExecute(
        JNIEnv* env, jclass, jobject javaAssets, jint packedTexture, jint outputTexture,
        jint width, jint height, jint bayerPattern, jfloatArray whiteBalance) {
    try {
        if (!javaAssets || !whiteBalance || env->GetArrayLength(whiteBalance) != 3 ||
            bayerPattern < 0 || bayerPattern > 3)
            throw std::runtime_error("26856 JNI: invalid AssetManager or Bayer/WB values");
        AAssetManager* assets = AAssetManager_fromJava(env, javaAssets);
        if (!assets) throw std::runtime_error("26856 JNI: inaccessible Android assets");
        std::array<float,3> gains{};
        env->GetFloatArrayRegion(whiteBalance, 0, 3, gains.data());
        if (env->ExceptionCheck()) return;
        runAmazeGlFrame(assets, static_cast<GLuint>(packedTexture),
                        static_cast<GLuint>(outputTexture),
                        static_cast<uint32_t>(width), static_cast<uint32_t>(height),
                        static_cast<amaze::BayerPattern>(bayerPattern), gains);
    } catch (const std::exception& error) {
        jclass klass = env->FindClass("java/lang/IllegalStateException");
        if (klass) env->ThrowNew(klass, error.what());
    }
}
