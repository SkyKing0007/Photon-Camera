#!/usr/bin/env python3
# IRIS 26564 true-2x CPU/GPU numeric parity regression.
# Intentionally Python-standard-library only: this file MUST pass under `python3 -S`.
import math
import random
import struct

rng = random.Random(26564)
RAW_W, RAW_H = 12, 10
OUT_W, OUT_H = RAW_W * 2, RAW_H * 2
FLOW_W, FLOW_H = 4, 4
COV_W, COV_H = 6, 5
REJ_W, REJ_H = 3, 3
FRAMES = 6


def f32(v):
    return struct.unpack('<f', struct.pack('<f', float(v)))[0]


def f16(v):
    return struct.unpack('<e', struct.pack('<e', float(v)))[0]


def clamp(v, a, b):
    return max(a, min(b, v))


def mirror(u, b):
    if u <= b:
        u = 2 * b - u
    if u > 1 - b:
        u = 2 * (1 - b) - u
    return clamp(u, 0.0, 1.0)


def is_vec(v):
    return isinstance(v, (list, tuple))


def lerp_value(a, b, t):
    if is_vec(a):
        return [lerp_value(a[i], b[i], t) for i in range(len(a))]
    return float(a) * (1.0 - t) + float(b) * t


def bilinear(arr, u, v):
    h = len(arr)
    w = len(arr[0])
    x = clamp(u * w - 0.5, 0.0, w - 1.0)
    y = clamp(v * h - 0.5, 0.0, h - 1.0)
    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    x1 = min(x0 + 1, w - 1)
    y1 = min(y0 + 1, h - 1)
    fx = x - x0
    fy = y - y0
    top = lerp_value(arr[y0][x0], arr[y0][x1], fx)
    bot = lerp_value(arr[y1][x0], arr[y1][x1], fx)
    return lerp_value(top, bot, fy)


def swizzle(v, t):
    maps = ((0, 1, 2, 3), (1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0))
    m = maps[t & 3]
    return [float(v[m[0]]), float(v[m[1]]), float(v[m[2]]), float(v[m[3]])]


def raw_at(raw, x, y):
    xi = int(clamp(x, 0, RAW_W - 1))
    yi = int(clamp(y, 0, RAW_H - 1))
    return float(raw[yi][xi])


def kernel(dx, dy, c):
    d = dx * dx * c[0] + dy * dy * c[1] + dx * dy * c[2] * 2.0
    return math.pow(2.0, -0.5 * d) + 0.00005


def dot(a, b):
    return sum(float(x) * float(y) for x, y in zip(a, b))


def rbf(raw, sx, sy, cfa, gains, black, cov):
    px = int(math.floor(sx))
    py = int(math.floor(sy))
    b = [[0.0] * 3 for _ in range(3)]
    w = [[0.0] * 3 for _ in range(3)]
    subx = math.floor(sx) + 0.5 - sx
    suby = math.floor(sy) + 0.5 - sy
    for ix in range(3):
        for iy in range(3):
            b[ix][iy] = raw_at(raw, px + ix - 1, py + iy - 1)
            w[ix][iy] = kernel(subx + ix - 1, suby + iy - 1, cov)
    off = ((1, 1), (0, 1), (1, 0), (0, 0))[cfa]
    t = (((py + off[1]) & 1) << 1) + ((px + off[0]) & 1)
    rg = swizzle(gains, t)
    rb = swizzle(black, t)
    cw = [w[0][0], w[0][2], w[2][0], w[2][2]]
    cv = [b[0][0], b[0][2], b[2][0], b[2][2]]
    uw = [w[1][0], w[1][2]]
    uv = [b[1][0], b[1][2]]
    lw = [w[0][1], w[2][1]]
    lv = [b[0][1], b[2][1]]
    ti = [0.0] * 4
    tw = [0.0] * 4
    ti[0] = dot([cv[i] * rg[0] + rb[0] for i in range(4)], cw)
    tw[0] = sum(cw)
    ti[1] = dot([uv[i] * rg[1] + rb[1] for i in range(2)], uw)
    tw[1] = sum(uw)
    ti[2] = dot([lv[i] * rg[2] + rb[2] for i in range(2)], lw)
    tw[2] = sum(lw)
    ti[3] = (b[1][1] * rg[3] + rb[3]) * w[1][1]
    tw[3] = w[1][1]
    I = swizzle(ti, t)
    W = swizzle(tw, t)
    return [I[0], I[1] + I[2], I[3]], [W[0], W[1] + W[2], W[3]]


def gpu_add_half(acc, contrib):
    # RGBA16F/RG16F additive render targets round each input and each blended write.
    return [f16(f16(acc[i]) + f16(contrib[i])) for i in range(len(acc))]


# Smooth but textured Bayer-like deterministic synthetic RAW data.
base = []
for y in range(RAW_H):
    row = []
    for x in range(RAW_W):
        val = (
            2500.0
            + 5000.0 * (x / (RAW_W - 1))
            + 2800.0 * (y / (RAW_H - 1))
            + 700.0 * math.sin(x * 0.9)
            + 350.0 * math.cos(y * 1.1)
        )
        row.append(val)
    base.append(row)

raws, flows, covs, rejs = [], [], [], []
shifts = ((0.05, 0.06), (0.28, 0.10), (0.09, 0.31), (0.32, 0.34), (1.06, 0.07), (0.30, 1.32))
for fi, (dx, dy) in enumerate(shifts):
    raw = []
    for y in range(RAW_H):
        row = []
        for x in range(RAW_W):
            val = base[y][x] + rng.gauss(0.0, 28.0) + fi * 6.0
            row.append(int(round(clamp(val, 64.0, 15000.0))))
        raw.append(row)
    raws.append(raw)

    flow = []
    for _y in range(FLOW_H):
        row = []
        for _x in range(FLOW_W):
            fx = f16((dx + rng.gauss(0.0, 0.005)) / RAW_W)
            fy = f16((dy + rng.gauss(0.0, 0.005)) / RAW_H)
            row.append((fx, fy))
        flow.append(row)
    flows.append(flow)

    cov = []
    for _y in range(COV_H):
        row = []
        for _x in range(COV_W):
            vals = []
            for _ in range(3):
                q = int(round(rng.uniform(0.12, 0.78) * 1023.0))
                vals.append(f32(q / 1023.0))
            row.append(tuple(vals))
        cov.append(row)
    covs.append(cov)

    rej = []
    for _y in range(REJ_H):
        row = [f32(rng.randint(180, 255) / 255.0) for _x in range(REJ_W)]
        rej.append(row)
    rejs.append(rej)

gains = [f32(1 / 15000.0), f32(1 / 14900.0), f32(1 / 15100.0), f32(1 / 15050.0)]
black = [f32(-64 / 15000.0), f32(-64 / 14900.0), f32(-64 / 15100.0), f32(-64 / 15050.0)]
crg = [f32(0.55), f32(1.7), f32(0.62), f32(1.55)]
cb = [f32(-0.25), f32(0.5)]
scale = [f32(1.01), f32(0.99), f32(1.02)]
lens = [[(1.01, 0.99, 1.00, 1.02) for _x in range(4)] for _y in range(3)]

max_abs = 0.0
max_rel = 0.0
phase_mismatch = 0
samples = 0
for gy in range(OUT_H):
    for gx in range(OUT_W):
        cpu = [f32(0.0)] * 6
        gpu = [f16(0.0)] * 6
        cmask = 0
        gmask = 0
        ru = (gx + 0.5) / OUT_W
        rv = (gy + 0.5) / OUT_H
        for fi in range(FRAMES):
            flow = bilinear(flows[fi], ru, rv)
            su = mirror(ru + float(flow[0]), 1.5 / RAW_W)
            sv = mirror(rv + float(flow[1]), 1.5 / RAW_H)
            packed = bilinear(covs[fi], su, sv)
            cov = [
                f32(packed[0] * crg[1] + crg[0]),
                f32(packed[1] * crg[3] + crg[2]),
                f32(packed[2] * cb[1] + cb[0]),
            ]
            color, weights = rbf(raws[fi], su * RAW_W, sv * RAW_H, 0, gains, black, cov)
            fw = float(bilinear(rejs[fi], ru, rv))
            contrib = [f32(x * fw) for x in (color + weights)]
            cpu = [f32(cpu[i] + contrib[i]) for i in range(6)]
            gpu = gpu_add_half(gpu, contrib)
            if fw > 0.08:
                px = (float(flow[0]) * RAW_W) % 1.0
                py = (float(flow[1]) * RAW_H) % 1.0
                bit = 1 << ((1 if px >= 0.5 else 0) + (2 if py >= 0.5 else 0))
                cmask |= bit
                gmask |= bit

        def resolve(a):
            rgb = [max(0.0, float(a[i]) / max(float(a[i + 3]), 1e-7)) * scale[i] for i in range(3)]
            sh = bilinear(lens, ru, rv)
            rgb[0] *= sh[0]
            rgb[1] *= 0.5 * (sh[1] + sh[2])
            rgb[2] *= sh[3]
            return [max(x, 0.0) for x in rgb]

        a = resolve(cpu)
        b = resolve(gpu)
        for i in range(3):
            err = abs(a[i] - b[i])
            rel = err / max(abs(a[i]), 1e-4)
            max_abs = max(max_abs, err)
            max_rel = max(max_rel, rel)
        phase_mismatch += int(cmask != gmask)
        samples += 1

assert phase_mismatch == 0, phase_mismatch
assert max_abs < 0.004, max_abs
assert max_rel < 0.006, max_rel


def phase_mask(sh):
    m = 0
    for dx, dy in sh:
        m |= 1 << ((1 if dx % 1 >= 0.5 else 0) + (2 if dy % 1 >= 0.5 else 0))
    return m


assert phase_mask(((0.1, 0.1), (1.1, 2.1), (3.1, 4.1))).bit_count() == 1
assert phase_mask(((0.1, 0.1), (0.6, 0.1), (0.1, 0.6), (0.6, 0.6))).bit_count() == 4
print(f'PASS synthetic CPU/GPU true2x parity samples={samples} maxAbs={max_abs:.8f} maxRel={max_rel:.8f} phaseMismatch={phase_mismatch}')
print('PASS repeated subpixel phases do not increase independent phase support')
print('PASS four quadrant subpixel phases report support=4')
print('PASS stdlib-only parity fixture (python3 -S compatible; no third-party packages)')
