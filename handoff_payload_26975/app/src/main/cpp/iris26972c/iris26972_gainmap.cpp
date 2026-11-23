#include "iris26972_gainmap.h"

#include <algorithm>
#include <cmath>
#include <csetjmp>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

#include <cerrno>
#include <fcntl.h>
#include <unistd.h>

extern "C" {
#include <jpeglib.h>
}

namespace iris26972c {
namespace {

bool HasCapacity(size_t capacity, int height, int stride, size_t lastRowBytes) {
    if (height < 1 || stride < 1 || lastRowBytes > static_cast<size_t>(stride))
        return false;
    const size_t rows = static_cast<size_t>(height - 1);
    if (rows > (std::numeric_limits<size_t>::max() - lastRowBytes) / static_cast<size_t>(stride))
        return false;
    return capacity >= rows * static_cast<size_t>(stride) + lastRowBytes;
}

// Input views can be slices of the same direct ByteBuffer. The gainmap result
// must never alias the image signal being sampled: writes across tile rows can
// otherwise contaminate later blocks and violate the fail-before-write contract.
bool Overlaps(const void* lhs, size_t lhsBytes, const void* rhs, size_t rhsBytes) {
    if (!lhsBytes || !rhsBytes) return false;
    const auto left = reinterpret_cast<uintptr_t>(lhs);
    const auto right = reinterpret_cast<uintptr_t>(rhs);
    const auto maxAddress = std::numeric_limits<uintptr_t>::max();
    if (lhsBytes > maxAddress - left || rhsBytes > maxAddress - right) return true;
    return left < right + rhsBytes && right < left + lhsBytes;
}

float SrgbToLinear(float v) {
    // The pinned donor's GLES30.GL_LINEAR source texture first interpolates
    // encoded sRGB at the 2x output-grid center, THEN applies the transfer
    // function. Linearizing each source texel before averaging is different.
    v = std::clamp(v, 0.0f, 1.0f);
    if (v <= 0.04045f) return v / 12.92f;
    return std::pow((v + 0.055f) / 1.055f, 2.4f);
}

float Luma(float r, float g, float b) {
    return r * 0.2126f + g * 0.7152f + b * 0.0722f;
}

struct JpegError {
    jpeg_error_mgr base;
    jmp_buf target;
};

void FailJpeg(j_common_ptr p) {
    longjmp(reinterpret_cast<JpegError*>(p->err)->target, 1);
}

}  // namespace

bool WriteGainmapTile(const GainmapTile& a, uint8_t* dst, size_t capacity,
                      int dstStride, float strength) {
    if (!a.sdrRGBA || !a.hdrLinearRGB || !dst ||
        a.fullWidth < 2 || a.fullHeight < 2 || a.fullWidth > 20000 ||
        a.fullHeight > 20000 || a.left < 0 || a.top < 0 ||
        a.width < 1 || a.height < 1 || a.left > a.fullWidth - a.width ||
        a.top > a.fullHeight - a.height ||
        a.left % 2 || a.top % 2 ||
        ((a.width % 2) && (a.left + a.width != a.fullWidth)) ||
        ((a.height % 2) && (a.top + a.height != a.fullHeight)) ||
        // Match bjzhou HdrGainmapStrength.coerce: the adjustment is a linear
        // gain-ratio multiplier, valid only on its donor setting domain.
        !std::isfinite(strength) || strength < 0.25f || strength > 2.0f ||
        a.width > std::numeric_limits<int>::max() / 4 ||
        a.width > std::numeric_limits<int>::max() / 12 ||
        !HasCapacity(a.sdrCapacityBytes, a.height, a.sdrRowStrideBytes,
                     static_cast<size_t>(a.width) * 4) ||
        !HasCapacity(a.hdrCapacityBytes, a.height, a.hdrRowStrideBytes,
                     static_cast<size_t>(a.width) * 3 * sizeof(float)) ||
        Overlaps(dst,capacity,a.sdrRGBA,a.sdrCapacityBytes) ||
        Overlaps(dst,capacity,a.hdrLinearRGB,a.hdrCapacityBytes)) return false;

    const int targetW = (a.fullWidth + 1) / 2;
    const int targetH = (a.fullHeight + 1) / 2;
    if (!HasCapacity(capacity, targetH, dstStride, targetW)) return false;

    // Validation pass before any write, including all finite registered HDR pixels.
    // Avoid partly written maps if Camera2 metadata/buffers are corrupt.
    for (int y = 0; y < a.height; ++y) {
        const uint8_t* hrow = reinterpret_cast<const uint8_t*>(a.hdrLinearRGB) +
                              static_cast<size_t>(y) * a.hdrRowStrideBytes;
        for (int x = 0; x < a.width; ++x) {
            float rgb[3];
            std::memcpy(rgb, hrow + static_cast<size_t>(x) * 12, sizeof(rgb));
            for (float value : rgb)
                if (!std::isfinite(value) || value < 0.0f || value > 65504.0f)
                    return false;
        }
    }

    const float logMin = std::log(kGainmapMinRatio);
    const float logRange = std::log(kGainmapMaxRatio) - logMin;
    const int tileW2 = (a.width + 1) / 2;
    const int tileH2 = (a.height + 1) / 2;
    for (int gy = 0; gy < tileH2; ++gy) {
        const int outY = a.top / 2 + gy;
        uint8_t* outRow = dst + static_cast<size_t>(outY) * dstStride;
        for (int gx = 0; gx < tileW2; ++gx) {
            float encodedR = 0.0f, encodedG = 0.0f, encodedB = 0.0f;
            float hdrLuma = 0.0f;
            int count = 0;
            for (int yy = gy * 2; yy < std::min(a.height, gy * 2 + 2); ++yy) {
                const uint8_t* sdrRow = a.sdrRGBA + static_cast<size_t>(yy) * a.sdrRowStrideBytes;
                const uint8_t* hdrRow = reinterpret_cast<const uint8_t*>(a.hdrLinearRGB) +
                                        static_cast<size_t>(yy) * a.hdrRowStrideBytes;
                for (int xx = gx * 2; xx < std::min(a.width, gx * 2 + 2); ++xx) {
                    const uint8_t* s = sdrRow + static_cast<size_t>(xx) * 4;
                    float h[3];
                    std::memcpy(h, hdrRow + static_cast<size_t>(xx) * 12, sizeof(h));
                    encodedR += static_cast<float>(s[0]);
                    encodedG += static_cast<float>(s[1]);
                    encodedB += static_cast<float>(s[2]);
                    hdrLuma += Luma(h[0], h[1], h[2]);
                    ++count;
                }
            }
            // Donor GpuReferenceGainmapProducer samples GL_LINEAR encoded SDR
            // and linear HDR at the 2x gainmap pixel center. For an even-sized
            // output grid, that equals 2x2 bilinear averaging in each *input*
            // encoding; the sRGB transfer comes after the encoded average.
            // The old per-texel sRGB-to-linear conversion overestimated SDR
            // luminance at black/white edges and invented a dark HDR border.
            const float invEncoded = 1.0f / (255.0f * count);
            const float sdrLuma = Luma(
                SrgbToLinear(encodedR * invEncoded),
                SrgbToLinear(encodedG * invEncoded),
                SrgbToLinear(encodedB * invEncoded));
            hdrLuma /= count;
            const float ratio = std::clamp((hdrLuma + kGainmapOffset) /
                                           (sdrLuma + kGainmapOffset),
                                           kGainmapMinRatio, kGainmapMaxRatio);
            // Pinned bjzhou RawGainmapMath / GpuReferenceGainmapProducer:
            // strengthRatio = clamp(1 + (candidateRatio - 1) * strength).
            // Multiplying log2(candidateRatio) by strength is a different
            // transfer function, especially for shadow gains and strength != 1.
            const float strengthRatio = std::clamp(
                1.0f + (ratio - 1.0f) * strength,
                kGainmapMinRatio, kGainmapMaxRatio);
            const float encoded = std::clamp(
                (std::log(strengthRatio) - logMin) / logRange, 0.0f, 1.0f);
            outRow[a.left / 2 + gx] = static_cast<uint8_t>(std::lround(255.0f * encoded));
        }
    }
    return true;
}

bool WriteGainmapJpeg(const uint8_t* gray, size_t capacity, int width,
                      int height, int stride, const char* path) {
    if (!gray || !path || !*path || width < 1 || height < 1 ||
        width > 10000 || height > 10000 ||
        !HasCapacity(capacity, height, stride, width) ||
        access(path, F_OK) == 0) return false;
    const std::string name(path);
    if (name.size() > 4000) return false;
    std::string tmp = name + ".iris26972c.gain.XXXXXX";
    std::vector<char> tempName(tmp.begin(), tmp.end());
    tempName.push_back('\0');
    const int fd = mkstemp(tempName.data());
    if (fd < 0) return false;
    FILE* file = fdopen(fd, "wb");
    if (!file) { close(fd); unlink(tempName.data()); return false; }
    jpeg_compress_struct c{};
    JpegError err{};
    c.err = jpeg_std_error(&err.base);
    err.base.error_exit = FailJpeg;
    volatile bool created = false, okay = false;
    if (setjmp(err.target) == 0) {
        jpeg_create_compress(&c);
        created = true;
        jpeg_stdio_dest(&c, file);
        c.image_width = static_cast<JDIMENSION>(width);
        c.image_height = static_cast<JDIMENSION>(height);
        c.input_components = 1;
        c.in_color_space = JCS_GRAYSCALE;
        jpeg_set_defaults(&c);
        jpeg_set_quality(&c, kGainmapQuality, TRUE);
        c.optimize_coding = TRUE;
        jpeg_start_compress(&c, TRUE);
        okay = true;
        while (c.next_scanline < c.image_height) {
            JSAMPROW row = const_cast<JSAMPROW>(gray +
                static_cast<size_t>(c.next_scanline) * stride);
            if (jpeg_write_scanlines(&c, &row, 1) != 1) {
                okay = false;
                break;
            }
        }
        if (okay) jpeg_finish_compress(&c);
    }
    if (created) jpeg_destroy_compress(&c);
    if (okay && fflush(file) != 0) okay = false;
    if (okay && fsync(fd) != 0) okay = false;
    if (fclose(file) != 0) okay = false;
    if (okay && link(tempName.data(), path) != 0) okay = false;
    unlink(tempName.data());
    return okay;
}

}  // namespace iris26972c
