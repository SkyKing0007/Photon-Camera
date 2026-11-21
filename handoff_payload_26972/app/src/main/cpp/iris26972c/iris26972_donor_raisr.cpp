#include "iris26972_donor_raisr.h"
#include "iris26972_raisr_2x_to_native.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <mutex>
#include <new>
#include <vector>

#include <dlfcn.h>

namespace iris26972c {
namespace {
constexpr int kDonorHaloNative = 16;
constexpr int kNativeDecimationHalo = 3;
constexpr int kMaxCoreEdge = 256;
constexpr int kMaxSourceEdge = 1024;
constexpr float kRealRaisrRate = 2.0f;
#if defined(__aarch64__)
constexpr const char* kPinName = "libiris26972c129.so";
constexpr const char* kPinSymbol = "photon_mgc_raisr_upscale_rgba8";
#endif

bool Covers(int first, int extent, int neededFirst, int neededEnd) {
    return first <= neededFirst && extent >= 0 &&
           static_cast<int64_t>(first) + extent >= neededEnd;
}

bool Valid(const DonorRaisrTile& a, const uint8_t* out, size_t outCapacity,
           int outStride) {
    if (!a.encodedSrgbRgba || !out || a.nativeFullWidth < 16 ||
        a.nativeFullHeight < 16 || a.nativeFullWidth > 20000 ||
        a.nativeFullHeight > 20000 || a.nativeCoreLeft < 0 ||
        a.nativeCoreTop < 0 || a.nativeCoreWidth < 1 || a.nativeCoreHeight < 1 ||
        a.nativeCoreWidth > kMaxCoreEdge || a.nativeCoreHeight > kMaxCoreEdge ||
        a.nativeCoreLeft > a.nativeFullWidth - a.nativeCoreWidth ||
        a.nativeCoreTop > a.nativeFullHeight - a.nativeCoreHeight ||
        a.sourceGlobalLeft < 0 || a.sourceGlobalTop < 0 ||
        (a.sourceGlobalLeft % 2) || (a.sourceGlobalTop % 2) ||
        a.sourceWidth < 16 || a.sourceHeight < 16 ||
        a.sourceWidth > kMaxSourceEdge || a.sourceHeight > kMaxSourceEdge ||
        a.sourceGlobalLeft > a.nativeFullWidth - a.sourceWidth ||
        a.sourceGlobalTop > a.nativeFullHeight - a.sourceHeight ||
        a.sourceRowStrideBytes < a.sourceWidth * 16 ||
        outStride < a.nativeCoreWidth * 4) return false;

    const int xl = std::max(0, a.nativeCoreLeft - kNativeDecimationHalo);
    const int yt = std::max(0, a.nativeCoreTop - kNativeDecimationHalo);
    const int xr = std::min(a.nativeFullWidth,
                             a.nativeCoreLeft + a.nativeCoreWidth + kNativeDecimationHalo);
    const int yb = std::min(a.nativeFullHeight,
                             a.nativeCoreTop + a.nativeCoreHeight + kNativeDecimationHalo);
    // The donor RAISR/DOG/composite chain's source halo is distinct from
    // the final 12-tap 2x-to-1x halo. Never let the library invent boundary context.
    if (!Covers(a.sourceGlobalLeft, a.sourceWidth,
                std::max(0, xl-kDonorHaloNative),
                std::min(a.nativeFullWidth, xr+kDonorHaloNative)) ||
        !Covers(a.sourceGlobalTop, a.sourceHeight,
                std::max(0, yt-kDonorHaloNative),
                std::min(a.nativeFullHeight, yb+kDonorHaloNative))) return false;
    const size_t rows = static_cast<size_t>(a.sourceHeight-1);
    const size_t sourceLast = static_cast<size_t>(a.sourceWidth)*16;
    if (rows > (std::numeric_limits<size_t>::max() - sourceLast) /
                   static_cast<size_t>(a.sourceRowStrideBytes) ||
        a.sourceCapacityBytes < rows*static_cast<size_t>(a.sourceRowStrideBytes)+sourceLast)
        return false;
    const size_t last = static_cast<size_t>(a.nativeCoreWidth)*4;
    if (static_cast<size_t>(a.nativeCoreHeight-1) >
        (std::numeric_limits<size_t>::max()-last) / static_cast<size_t>(outStride) ||
        outCapacity < static_cast<size_t>(a.nativeCoreHeight-1)*outStride+last) return false;
    return true;
}

DonorRaisr2x LoadVerifiedArm64Donor() {
#if defined(__aarch64__)
    // Lazy dlopen deliberately does NOT call the donor's JNI_OnLoad. Its exported
    // RAISR C entry is all Experiment C uses. The file is a separately named,
    // SONAME-rewritten exact 1.29.0 Actions native; the Android loader must not
    // confuse it with the A/B libmy-native-lib.so.
    static std::once_flag once;
    static DonorRaisr2x fn = nullptr;
    static void* keepForProcessLifetime = nullptr;
    std::call_once(once, [] {
        keepForProcessLifetime = dlopen(kPinName, RTLD_NOW | RTLD_LOCAL);
        if (keepForProcessLifetime)
            fn = reinterpret_cast<DonorRaisr2x>(dlsym(keepForProcessLifetime,kPinSymbol));
    });
    return fn;
#else
    return nullptr; // The donor publishes no 32-bit RAISR AOT. No substitution.
#endif
}
}  // namespace

bool ProcessRaisrTileWithFunction(const DonorRaisrTile& a,
                                  uint8_t* output, size_t capacity, int stride,
                                  DonorRaisr2x donor) {
    if (!donor || !Valid(a,output,capacity,stride)) return false;
    const int left=std::max(0,a.nativeCoreLeft-kNativeDecimationHalo);
    const int top=std::max(0,a.nativeCoreTop-kNativeDecimationHalo);
    const int right=std::min(a.nativeFullWidth,a.nativeCoreLeft+a.nativeCoreWidth+kNativeDecimationHalo);
    const int bottom=std::min(a.nativeFullHeight,a.nativeCoreTop+a.nativeCoreHeight+kNativeDecimationHalo);
    const int coreW=right-left,coreH=bottom-top;
    try {
        std::vector<float> packed(static_cast<size_t>(a.sourceWidth)*a.sourceHeight*4);
        const auto* bytes = reinterpret_cast<const uint8_t*>(a.encodedSrgbRgba);
        for(int y=0;y<a.sourceHeight;y++) {
            const auto* src=bytes+static_cast<size_t>(y)*a.sourceRowStrideBytes;
            float* dst=packed.data()+static_cast<size_t>(y)*a.sourceWidth*4;
            std::memcpy(dst,src,static_cast<size_t>(a.sourceWidth)*16);
        }
        // This ABI quantizes sRGB float to U8. Passing RAW linear or HDR overrange
        // here is a color-domain error; reject rather than quietly clamp it.
        for(float v: packed)
            if (!std::isfinite(v) || v < 0.0f || v > 1.0f) return false;
        const size_t doubledW=static_cast<size_t>(coreW)*2;
        const size_t doubledH=static_cast<size_t>(coreH)*2;
        std::vector<uint8_t> doubled(doubledW*doubledH*4);
        const int status=donor(packed.data(),a.sourceWidth,a.sourceHeight,
                                doubled.data(),left-a.sourceGlobalLeft,
                                top-a.sourceGlobalTop,coreW,coreH,kRealRaisrRate);
        if (status!=0) return false;
        const Raisr2xTile input{doubled.data(),static_cast<int>(doubledW),
            static_cast<int>(doubledH),static_cast<int>(doubledW*4),
            left*2,top*2,a.nativeFullWidth*2,a.nativeFullHeight*2};
        std::vector<uint8_t> final(static_cast<size_t>(a.nativeCoreWidth)*a.nativeCoreHeight*4);
        if(!downsampleRaisr2xToNative(input,a.nativeCoreLeft,a.nativeCoreTop,
                                     a.nativeCoreWidth,a.nativeCoreHeight,
                                     final.data(),a.nativeCoreWidth*4)) return false;
        for(int y=0;y<a.nativeCoreHeight;y++)
            std::memcpy(output+static_cast<size_t>(y)*stride,
                        final.data()+static_cast<size_t>(y)*a.nativeCoreWidth*4,
                        static_cast<size_t>(a.nativeCoreWidth)*4);
        return true;
    } catch(const std::bad_alloc&) { return false; }
}

bool ProcessRealDonorRaisrTile(const DonorRaisrTile& tile, uint8_t* output,
                              size_t capacity, int stride) {
    // The donor AOT owns a process-wide OpenMP worker pool and dynamic profile
    // state; serializing only C-only invocations avoids overlapping full-frame
    // allocations and unknown native parallel calls during a burst. Host-injected
    // geometry tests above do not exercise this Android-only lifetime guarantee.
    static std::mutex donorInvocationMutex;
    if (!Valid(tile, output, capacity, stride)) return false;
    std::lock_guard<std::mutex> guard(donorInvocationMutex);
    return ProcessRaisrTileWithFunction(tile,output,capacity,stride,LoadVerifiedArm64Donor());
}
} // namespace iris26972c
