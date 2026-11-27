// SPDX-FileCopyrightText: 2026 RawLens contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Exact rawdn_estimate_noise body from RawLens 2.4.58, commit 969d2098ca374690e2646f3ca53ec01a54d7c686,
// app/src/main/cpp/rawdn/rawdn.cpp. Isolated namespace and header wrapper only.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
namespace iris26996_noise {
inline int rawdn_estimate_noise(const uint16_t* in, size_t stride, int w, int h, int cfa, const float black[4], float white,
                                    float* a, float* b) {
    // Green pair of each 2x2 cell: difference cancels the signal, so its
    // variance over a 16x16 px block is twice the noise variance at the block mean.
    const bool diag = (cfa & 3) == 1 || (cfa & 3) == 2;
    const int o1 = diag ? 0 : 1, o2 = diag ? int(stride) + 1 : int(stride);
    const float bk1 = black[diag ? 0 : 1], bk2 = black[diag ? 3 : 2];
    const float scale = 1.f / (white - 0.25f * (black[0] + black[1] + black[2] + black[3]));
    const int B = 8, by = h / 2 / B, bx = w / 2 / B;
    struct S {
        float mean, var, spread;
    };
    std::vector<S> s;
    s.reserve(size_t(by) * size_t(bx) / 2);
    for (int y = 0; y < by; y++)
        for (int x = (y & 1); x < bx; x += 2) {   // checkerboard subsample: half the blocks
            double sm = 0, sm2 = 0, sd = 0, sd2 = 0;
            for (int j = 0; j < B; j++) {
                const uint16_t* row = in + size_t(2 * (y * B + j)) * stride + size_t(2 * x * B);
                for (int i = 0; i < B; i++) {
                    float g1 = (float(row[2 * i + o1]) - bk1) * scale, g2 = (float(row[2 * i + o2]) - bk2) * scale;
                    float m = 0.5f * (g1 + g2), d = g1 - g2;
                    sm += m; sm2 += double(m) * m; sd += d; sd2 += double(d) * d;
                }
            }
            const double nn = B * B;
            float mean = float(sm / nn);
            if (mean <= 0.002f || mean >= 0.7f) continue;
            s.push_back({mean, float((sd2 / nn - (sd / nn) * (sd / nn)) * 0.5), float(std::sqrt(std::max(sm2 / nn - (sm / nn) * (sm / nn), 0.0)))});
        }
    if (s.size() < 24 * 40) return 0;
    std::sort(s.begin(), s.end(), [](const S& p, const S& q) { return p.mean < q.mean; });
    const int bins = 24;
    double sxx = 0, sx = 0, s1 = 0, sxy = 0, sy = 0;
    int used = 0;
    std::vector<float> tmp;
    for (int k = 0; k < bins; k++) {
        size_t lo = s.size() * size_t(k) / bins, hi = s.size() * size_t(k + 1) / bins;
        std::vector<S> bin(s.begin() + long(lo), s.begin() + long(hi));
        size_t keep = std::max<size_t>(bin.size() * 3 / 10, 8);
        if (bin.size() < keep) continue;
        std::nth_element(bin.begin(), bin.begin() + long(keep), bin.end(), [](const S& p, const S& q) { return p.spread < q.spread; });
        tmp.clear();
        double mx = 0;
        for (size_t i = 0; i < keep; i++) {
            tmp.push_back(bin[i].var);
            mx += bin[i].mean;
        }
        std::nth_element(tmp.begin(), tmp.begin() + long(keep / 2), tmp.end());
        double x = mx / double(keep), y = double(tmp[keep / 2]) / 0.98;
        if (!(y > 0)) continue;
        double wgt = 1.0 / (y * y);   // relative error
        sxx += wgt * x * x; sx += wgt * x; s1 += wgt; sxy += wgt * x * y; sy += wgt * y;
        used++;
    }
    if (used < 3) return 0;
    double det = sxx * s1 - sx * sx;
    if (std::fabs(det) < 1e-30) return 0;
    double aa = (sxy * s1 - sx * sy) / det, bb = (sxx * sy - sx * sxy) / det;
    *a = float(std::max(aa, 1e-9));
    *b = float(std::max(bb, 0.0));
    return used;
}
} // namespace iris26996_noise
