#pragma once
/* IRIS_26915_TELEPHOTO_ROW_STRIDE_GUIDE
 * CPU-only 1x RGBA16F guide packer. Testable without Android headers.
 * Inputs: camera-linear 1x post-denoise RGBA16F and unmodified R16F sensor
 * clipping evidence. The final true-2x reconstruction remains GPU-resident.
 */
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace iris26915guide {
constexpr size_t kPixelBytes = 8u;
constexpr size_t kMaskBytes = 2u;

inline bool sizes(int width, int height, size_t stridePixels,
                  size_t* rgbBytes, size_t* maskBytes, size_t* strideBytes) {
    if (width <= 0 || height <= 0 || stridePixels < static_cast<size_t>(width) ||
        stridePixels > std::numeric_limits<size_t>::max() / kPixelBytes) return false;
    const size_t w = static_cast<size_t>(width);
    const size_t h = static_cast<size_t>(height);
    if (w > std::numeric_limits<size_t>::max() / h ||
        w * h > std::numeric_limits<size_t>::max() / kPixelBytes ||
        h > std::numeric_limits<size_t>::max() / (stridePixels * kPixelBytes)) return false;
    *rgbBytes = w * h * kPixelBytes;
    *maskBytes = w * h * kMaskBytes;
    *strideBytes = stridePixels * kPixelBytes;
    return true;
}

inline bool validMask(const uint8_t* mask, size_t pixels) {
    if (!mask) return false;
    for (size_t i = 0; i < pixels; ++i) {
        uint16_t half = 0;
        std::memcpy(&half, mask + i * kMaskBytes, kMaskBytes);
        // Reject Inf/NaN, negatives other than -0, and values greater than +1.
        if ((half & 0x7c00u) == 0x7c00u ||
            ((half & 0x8000u) && half != 0x8000u) ||
            (!(half & 0x8000u) && half > 0x3c00u)) return false;
    }
    return true;
}

inline bool pack(uint8_t* mapped, size_t stridePixels,
                 int width, int height,
                 const uint8_t* rgba, size_t rgbaCapacity,
                 const uint8_t* mask, size_t maskCapacity) {
    size_t rgbBytes=0,maskBytes=0,strideBytes=0;
    if (!mapped || !rgba || !mask ||
        !sizes(width,height,stridePixels,&rgbBytes,&maskBytes,&strideBytes) ||
        rgbaCapacity != rgbBytes || maskCapacity != maskBytes ||
        !validMask(mask,static_cast<size_t>(width) * static_cast<size_t>(height))) return false;
    const size_t rowBytes=static_cast<size_t>(width)*kPixelBytes;
    for (int y=0;y<height;++y) {
        uint8_t* dst=mapped+static_cast<size_t>(y)*strideBytes;
        const uint8_t* src=rgba+static_cast<size_t>(y)*rowBytes;
        std::memcpy(dst,src,rowBytes);
        for (int x=0;x<width;++x) {
            const size_t pixel=static_cast<size_t>(y)*static_cast<size_t>(width)+static_cast<size_t>(x);
            // memcpy preserves every original half bit, including signed zero.
            std::memcpy(dst+static_cast<size_t>(x)*kPixelBytes+6u,
                        mask+pixel*kMaskBytes,kMaskBytes);
        }
    }
    return true;
}
} // namespace iris26915guide
