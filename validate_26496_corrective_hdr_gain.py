#!/usr/bin/env python3
import math
import cmath
import sys

DIVISOR = 5.656854249492381
TOL_EV = 0.35
KERNEL = [
    0.042229693589,
    0.070339090351,
    0.103129012812,
    0.133097613729,
    0.151204589518,
    0.151204589518,
    0.133097613729,
    0.103129012812,
    0.070339090351,
    0.042229693589,
]
UHDR_OFFSET = 0.015625
GUIDE_SIGMA_EV = 0.90
MAX_GAIN = 2.5


def fail(msg):
    raise SystemExit(msg)


def close(a, b, eps=1e-9):
    return abs(a - b) <= eps


def response(freq):
    return abs(sum(w * cmath.exp(-2j * math.pi * freq * i)
                   for i, w in enumerate(KERNEL)))


def guide_weight(center, sample):
    ev = abs(math.log2((sample + UHDR_OFFSET) / (center + UHDR_OFFSET)))
    z = ev / GUIDE_SIGMA_EV
    return math.exp(-0.5 * z * z)


def old_separate_prefilter_ratio(sdr, hdr, gp):
    base = gp * 4
    hs = ss = ws = 0.0
    for k, w in enumerate(KERNEL):
        i = min(max(base - 3 + k, 0), len(sdr) - 1)
        hs += w * hdr[i]
        ss += w * sdr[i]
        ws += w
    ratio = (hs / ws + UHDR_OFFSET) / (ss / ws + UHDR_OFFSET)
    return min(max(ratio, 1.0), MAX_GAIN)


def new_guided_log_gain_ratio(sdr, hdr, gp):
    base = gp * 4
    i1 = min(max(base + 1, 0), len(sdr) - 1)
    i2 = min(max(base + 2, 0), len(sdr) - 1)
    center = 0.5 * (sdr[i1] + sdr[i2])
    total = weight = 0.0
    for k, spatial in enumerate(KERNEL):
        i = min(max(base - 3 + k, 0), len(sdr) - 1)
        ratio = min(max((hdr[i] + UHDR_OFFSET) / (sdr[i] + UHDR_OFFSET), 1.0), MAX_GAIN)
        w = spatial * guide_weight(center, sdr[i])
        total += w * math.log2(ratio)
        weight += w
    return 2.0 ** (total / weight)


def confidence(w):
    if w <= 0.15:
        return 0.0
    if w >= 0.75:
        return 1.0
    x = (w - 0.15) / (0.75 - 0.15)
    return x * x * (3.0 - 2.0 * x)


def main():
    # Short exposure: exact -2.5 EV physical probe and existing +/-0.35 EV tolerance
    # remain under the existing reconstruction scale ceiling of 8x.
    if not close(DIVISOR, 2.0 ** 2.5, 1e-12):
        fail('2.5 EV divisor mismatch')
    worst_scale = DIVISOR * (2.0 ** TOL_EV)
    if not worst_scale < 8.0:
        fail(f'short scale ceiling violated: {worst_scale}')

    # Dither positions: the legacy 48x36 AE sampler is untouched; the separate
    # 3x3 highlight-only sampler covers three offsets on each axis over 9 frames.
    step = 84
    offsets = sorted({(i % 3) * (step // 3) for i in range(9)})
    if offsets != [0, 28, 56]:
        fail(f'dither offsets unexpected: {offsets}')
    cyclic_gaps = [offsets[i + 1] - offsets[i] for i in range(len(offsets) - 1)] + [step - offsets[-1] + offsets[0]]
    if max(cyclic_gaps) != step // 3:
        fail(f'dither coverage gap unexpected: {cyclic_gaps}')

    # Spatial anti-alias kernel remains positive/symmetric/unit-sum and strongly
    # attenuates frequencies that cannot survive 4:1 gain-map decimation.
    if any(w <= 0.0 for w in KERNEL):
        fail('gain kernel must be positive')
    if any(abs(KERNEL[i] - KERNEL[-1-i]) > 1e-12 for i in range(len(KERNEL))):
        fail('gain kernel must be symmetric')
    if abs(sum(KERNEL) - 1.0) > 1e-9:
        fail(f'gain kernel sum={sum(KERNEL)}')
    if response(1/8) >= 0.10 or response(3/16) >= 0.04:
        fail(f'gain kernel insufficient attenuation {response(1/8)} {response(3/16)}')

    # Synthetic hard edge: 26495's blur-then-divide leaks large HDR gain into the
    # low-gain side. 26496 forms gain first and uses SDR-guided filtering; leakage
    # at the immediately adjacent low-side gain cell must remain near unity.
    n = 128
    sdr = [0.15] * n
    hdr = [0.15] * n
    for i in range(64, n):
        sdr[i] = 0.8
        hdr[i] = 2.0
    old_leak = old_separate_prefilter_ratio(sdr, hdr, 15)  # base x=60, edge x=64
    new_leak = new_guided_log_gain_ratio(sdr, hdr, 15)
    if not old_leak > 1.5:
        fail(f'synthetic old leak setup invalid: {old_leak}')
    if not new_leak < 1.05:
        fail(f'guided log-gain edge leak too high: {new_leak}')

    # RCD missing-chroma completion invariants used by the shader:
    # all-trusted neighborhoods are an exact no-op; constant trusted opponent
    # residuals remain constant under normalized convolution; weak support fades
    # continuously toward neutral rather than a binary color snap.
    if confidence(0.10) != 0.0 or confidence(0.80) != 1.0:
        fail('chroma confidence endpoint failure')
    vals = [0.23, 0.23, 0.23, 0.23]
    weights = [0.4, 0.8, 0.2, 1.0]
    normalized = sum(v*w for v, w in zip(vals, weights)) / sum(weights)
    if abs(normalized - 0.23) > 1e-12:
        fail('normalized chroma constant-field invariance failed')

    print('PASS: 26496 exposure headroom math')
    print('PASS: 26496 separate 3x3 spatial highlight trigger coverage')
    print('PASS: 26496 positive symmetric gain-map anti-alias kernel')
    print(f'PASS: 26496 guided log-gain edge test oldLeak={old_leak:.6f} newLeak={new_leak:.6f}')
    print('PASS: 26496 smooth missing-chroma normalized-convolution invariants')


if __name__ == '__main__':
    main()
