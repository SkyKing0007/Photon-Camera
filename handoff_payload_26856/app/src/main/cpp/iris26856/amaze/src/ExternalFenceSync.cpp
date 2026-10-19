// IRIS_26856_B_ONLY_EGL_VULKAN_NATIVE_FENCE_OWNER
#include "amaze/ExternalFenceSync.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <unistd.h>
#include <cstring>
#include <stdexcept>
#include <utility>

namespace amaze {
namespace {
struct EglSyncFunctions {
    PFNEGLCREATESYNCKHRPROC create;
    PFNEGLDESTROYSYNCKHRPROC destroy;
    PFNEGLDUPNATIVEFENCEFDANDROIDPROC dup;
    PFNEGLWAITSYNCKHRPROC wait;
};
EglSyncFunctions requireEglFenceFunctions(EGLDisplay display) {
    if (display == EGL_NO_DISPLAY || eglGetCurrentContext() == EGL_NO_CONTEXT)
        throw std::runtime_error("26856 GL/Vulkan: no current EGL context");
    const char* extensions = eglQueryString(display, EGL_EXTENSIONS);
    if (!extensions || !std::strstr(extensions, "EGL_ANDROID_native_fence_sync") ||
        !std::strstr(extensions, "EGL_KHR_fence_sync") ||
        !std::strstr(extensions, "EGL_KHR_wait_sync"))
        throw std::runtime_error("26856 GL/Vulkan: required native fence extensions absent");
    EglSyncFunctions f{};
    f.create = reinterpret_cast<PFNEGLCREATESYNCKHRPROC>(eglGetProcAddress("eglCreateSyncKHR"));
    f.destroy = reinterpret_cast<PFNEGLDESTROYSYNCKHRPROC>(eglGetProcAddress("eglDestroySyncKHR"));
    f.dup = reinterpret_cast<PFNEGLDUPNATIVEFENCEFDANDROIDPROC>(eglGetProcAddress("eglDupNativeFenceFDANDROID"));
    f.wait = reinterpret_cast<PFNEGLWAITSYNCKHRPROC>(eglGetProcAddress("eglWaitSyncKHR"));
    if (!f.create || !f.destroy || !f.dup || !f.wait)
        throw std::runtime_error("26856 GL/Vulkan: native EGL fence functions unavailable");
    return f;
}
}
ScopedNativeFd::~ScopedNativeFd() { if (fd_ >= 0) ::close(fd_); }
ScopedNativeFd::ScopedNativeFd(ScopedNativeFd&& other) noexcept : fd_(other.release()) {}
ScopedNativeFd& ScopedNativeFd::operator=(ScopedNativeFd&& other) noexcept {
    if (this != &other) { if (fd_ >= 0) ::close(fd_); fd_ = other.release(); }
    return *this;
}
int ScopedNativeFd::release() noexcept { const int old = fd_; fd_ = -1; return old; }

ScopedNativeFd createCurrentGlReleaseFence() {
    EGLDisplay display = eglGetCurrentDisplay();
    auto f = requireEglFenceFunctions(display);
    const EGLint attrs[] = {EGL_NONE};
    EGLSyncKHR sync = f.create(display, EGL_SYNC_NATIVE_FENCE_ANDROID, attrs);
    if (sync == EGL_NO_SYNC_KHR)
        throw std::runtime_error("26856 GL/Vulkan: cannot create GLES release fence");
    glFlush();
    const int fd = f.dup(display, sync);
    f.destroy(display, sync);
    if (fd < 0) throw std::runtime_error("26856 GL/Vulkan: cannot duplicate GLES fence fd");
    return ScopedNativeFd(fd);
}
VkSemaphore importGlFenceToVulkan(VkDevice device, ScopedNativeFd&& fence) {
    if (!device || fence.get() < 0)
        throw std::runtime_error("26856 GL/Vulkan: invalid GL fence import");
    auto importer = reinterpret_cast<PFN_vkImportSemaphoreFdKHR>(
        vkGetDeviceProcAddr(device, "vkImportSemaphoreFdKHR"));
    if (!importer) throw std::runtime_error("26856 GL/Vulkan: missing semaphore FD importer");
    VkSemaphoreCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    VkSemaphore sem = VK_NULL_HANDLE;
    if (vkCreateSemaphore(device, &ci, nullptr, &sem) != VK_SUCCESS)
        throw std::runtime_error("26856 GL/Vulkan: cannot allocate import semaphore");
    VkImportSemaphoreFdInfoKHR ii{};
    ii.sType = VK_STRUCTURE_TYPE_IMPORT_SEMAPHORE_FD_INFO_KHR;
    ii.semaphore = sem;
    ii.flags = VK_SEMAPHORE_IMPORT_TEMPORARY_BIT;
    ii.handleType = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT;
    ii.fd = fence.get();
    if (importer(device, &ii) != VK_SUCCESS) {
        vkDestroySemaphore(device, sem, nullptr);
        throw std::runtime_error("26856 GL/Vulkan: GL fence FD import failed");
    }
    fence.release();  // Vulkan takes ownership of the imported fd on success.
    return sem;
}
VkSemaphore createGlExportableSemaphore(VkDevice device) {
    VkExportSemaphoreCreateInfo exportInfo{};
    exportInfo.sType = VK_STRUCTURE_TYPE_EXPORT_SEMAPHORE_CREATE_INFO;
    exportInfo.handleTypes = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT;
    VkSemaphoreCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    ci.pNext = &exportInfo;
    VkSemaphore s = VK_NULL_HANDLE;
    if (vkCreateSemaphore(device, &ci, nullptr, &s) != VK_SUCCESS)
        throw std::runtime_error("26856 GL/Vulkan: exportable fence semaphore creation failed");
    return s;
}
ScopedNativeFd exportVulkanFenceToGl(VkDevice device, VkSemaphore semaphore) {
    if (!device || !semaphore) throw std::runtime_error("26856 GL/Vulkan: missing Vulkan signal");
    auto exporter = reinterpret_cast<PFN_vkGetSemaphoreFdKHR>(
        vkGetDeviceProcAddr(device, "vkGetSemaphoreFdKHR"));
    if (!exporter) throw std::runtime_error("26856 GL/Vulkan: missing semaphore FD exporter");
    VkSemaphoreGetFdInfoKHR info{};
    info.sType = VK_STRUCTURE_TYPE_SEMAPHORE_GET_FD_INFO_KHR;
    info.semaphore = semaphore;
    info.handleType = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT;
    int fd = -1;
    if (exporter(device, &info, &fd) != VK_SUCCESS || fd < 0)
        throw std::runtime_error("26856 GL/Vulkan: Vulkan signal fd export failed");
    return ScopedNativeFd(fd);
}
void waitCurrentGlOnVulkanFence(ScopedNativeFd&& fence) {
    if (fence.get() < 0) throw std::runtime_error("26856 GL/Vulkan: missing RGB completion fd");
    EGLDisplay display = eglGetCurrentDisplay();
    auto f = requireEglFenceFunctions(display);
    const EGLint attrs[] = {EGL_SYNC_NATIVE_FENCE_FD_ANDROID, fence.get(), EGL_NONE};
    EGLSyncKHR sync = f.create(display, EGL_SYNC_NATIVE_FENCE_ANDROID, attrs);
    if (sync == EGL_NO_SYNC_KHR)
        throw std::runtime_error("26856 GL/Vulkan: cannot import Vulkan completion fd");
    fence.release(); // EGL takes ownership after successful native-fence import.
    const EGLBoolean ok = f.wait(display, sync, 0);
    f.destroy(display, sync);
    if (ok != EGL_TRUE) throw std::runtime_error("26856 GL/Vulkan: GLES wait on Vulkan fence failed");
}
} // namespace amaze
