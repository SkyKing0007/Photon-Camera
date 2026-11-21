#include "iris26972_raisr_2x_to_native.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace iris26972c {
namespace {
constexpr int kPhaseTaps = 12;
// At exact 2x -> 1x, every output sample is centered halfway between input
// samples; a 12-tap Lanczos-3 (source-grid radius 6) has ONE global phase.
std::array<double, kPhaseTaps> weights() {
    constexpr double pi = 3.14159265358979323846;
    auto sinc = [](double x) -> double {
        return x == 0.0 ? 1.0 : std::sin(pi * x) / (pi * x);
    };
    std::array<double, kPhaseTaps> w{};
    double sum = 0.0;
    for (int i = 0; i < kPhaseTaps; i++) {
        const double delta = static_cast<double>(i) - 5.5;
        // The input image is twice as dense; decimation cutoff is 1/2.
        w[i] = sinc(delta * 0.5) * sinc(delta / 6.0);
        sum += w[i];
    }
    for (auto& v : w) v /= sum;
    return w;
}

bool valid(const Raisr2xTile& a, int x, int y, int w, int h, int outStride) {
    if (!a.rgba || !a.width || !a.height || !w || !h || !a.fullWidth || !a.fullHeight) return false;
    if (a.width < 0 || a.height < 0 || x < 0 || y < 0 || w < 0 || h < 0 ||
        a.globalX < 0 || a.globalY < 0 || a.fullWidth % 2 || a.fullHeight % 2) return false;
    if (a.width > a.fullWidth || a.height > a.fullHeight ||
        a.globalX > a.fullWidth - a.width || a.globalY > a.fullHeight - a.height ||
        x > a.fullWidth / 2 - w || y > a.fullHeight / 2 - h) return false;
    if (a.width > INT32_MAX / 4 || w > INT32_MAX / 4 ||
        a.rowStrideBytes < a.width * 4 || outStride < w * 4) return false;
    if (static_cast<std::int64_t>(a.rowStrideBytes) * a.height > INT32_MAX * 2LL ||
        static_cast<std::int64_t>(outStride) * h > INT32_MAX * 2LL) return false;
    // Require exact input halo in global pixels, including at clipped image edges.
    for (int yy : {y, y + h - 1}) {
        const int first = std::max(0, yy * 2 - 5);
        const int last = std::min(a.fullHeight - 1, yy * 2 + 6);
        if (first < a.globalY || last >= a.globalY + a.height) return false;
    }
    for (int xx : {x, x + w - 1}) {
        const int first = std::max(0, xx * 2 - 5);
        const int last = std::min(a.fullWidth - 1, xx * 2 + 6);
        if (first < a.globalX || last >= a.globalX + a.width) return false;
    }
    return true;
}

inline uint8_t byte(double v) {
    return static_cast<uint8_t>(std::clamp(std::lround(v), 0L, 255L));
}
} // namespace

bool downsampleRaisr2xToNative(const Raisr2xTile& a,
                              int dstX, int dstY, int dstWidth, int dstHeight,
                              uint8_t* output, int outStride) {
    if (!output || !valid(a,dstX,dstY,dstWidth,dstHeight,outStride)) return false;
    static const std::array<double, kPhaseTaps> weights_ = weights();
    const auto& w = weights_;
    // Bounded scratch: 12 source rows x output width x RGB. One output row
    // at a time, so no full 2x frame allocation or hidden tile resampling.
    std::vector<double> horizontal;
    try { horizontal.resize(static_cast<size_t>(kPhaseTaps) * dstWidth * 3); }
    catch (...) { return false; }
    for (int outY = 0; outY < dstHeight; ++outY) {
        const int y = dstY + outY;
        for (int ky = 0; ky < kPhaseTaps; ++ky) {
            const int srcY = std::clamp(2 * y - 5 + ky, 0, a.fullHeight - 1) - a.globalY;
            const uint8_t* sourceRow = a.rgba + static_cast<size_t>(srcY) * a.rowStrideBytes;
            for (int outX = 0; outX < dstWidth; ++outX) {
                const int x = dstX + outX;
                double rgb[3] = {0.0, 0.0, 0.0};
                for (int kx = 0; kx < kPhaseTaps; ++kx) {
                    const int srcX = std::clamp(2 * x - 5 + kx, 0, a.fullWidth - 1) - a.globalX;
                    const uint8_t* src = sourceRow + static_cast<size_t>(srcX) * 4;
                    for (int c = 0; c < 3; c++) rgb[c] += w[kx] * src[c];
                }
                const size_t base = (static_cast<size_t>(ky) * dstWidth + outX) * 3;
                for (int c = 0; c < 3; c++) horizontal[base + c] = rgb[c];
            }
        }
        uint8_t* target = output + static_cast<size_t>(outY) * outStride;
        for (int outX = 0; outX < dstWidth; outX++) {
            double rgb[3] = {0.0, 0.0, 0.0};
            for (int ky = 0; ky < kPhaseTaps; ky++) {
                const size_t base = (static_cast<size_t>(ky) * dstWidth + outX) * 3;
                for (int c = 0; c < 3; c++) rgb[c] += w[ky] * horizontal[base + c];
            }
            for (int c = 0; c < 3; c++) target[outX * 4 + c] = byte(rgb[c]);
            target[outX * 4 + 3] = 255;
        }
    }
    return true;
}
} // namespace iris26972c
