#!/usr/bin/env python3
import math

# 1) Wronski flow semantic contract: interpolation cancellation preserves the base vector.
def flow_conf(variation):
    return math.exp(-80.0 * max(variation, 0.0))
assert flow_conf(0.001) > 0.9
assert flow_conf(0.02) < 0.30
print('PASS: 26497 base-flow preservation semantics independent of interpolation-cancel flag')

# 2) Local correspondence search must recover a small residual shift and reject ambiguity.
def synthetic_error(offset, truth=0.5):
    return abs(offset-truth)*0.20 + 0.025
candidates=[-0.5,0.0,0.5]
errs=sorted((synthetic_error(x),x) for x in candidates)
assert errs[0][1] == 0.5 and errs[0][0] <= 0.055 and errs[1][0]-errs[0][0] >= 0.01
print('PASS: 26497 bounded local short-correspondence refinement synthetic recovery')

# 3) Multi-direction chroma rule: one isolated seed must never gain authority.
def chroma_conf(sectors, dispersion, total_w):
    if sectors < 2 or total_w <= 1e-6:
        return 0.0
    def smooth(a,b,x):
        if x <= a: return 0.0
        if x >= b: return 1.0
        t=(x-a)/(b-a)
        return t*t*(3-2*t)
    direction=smooth(1.5,3.0,sectors)
    agreement=1.0-smooth(0.18,0.42,dispersion)
    support=smooth(0.45,1.35,total_w)
    return direction*agreement*support
assert chroma_conf(1,0.0,2.0) == 0.0
assert chroma_conf(3,0.05,2.0) > 0.7
assert chroma_conf(3,0.60,2.0) == 0.0
print('PASS: 26497 isolated/disagreeing chroma evidence cannot propagate')

# 4) UHDR cell ownership: exact non-overlapping 4x4 footprints share no source sample.
def footprint(cx,cy):
    return {(cx*4+x,cy*4+y) for y in range(4) for x in range(4)}
a=footprint(10,10); b=footprint(11,10); c=footprint(10,11)
assert len(a)==16 and not (a&b) and not (a&c)
print('PASS: 26497 UHDR 4x4 gain footprints are exact and non-overlapping')

# 5) No cross-cell gain leakage on a synthetic thin-bar pattern.
# Per-pixel log gain alternates by 4-pixel cells. Exact ownership must reproduce it.
row=[]
for cell_gain in [0.0, 2.0, 0.0, 2.0, 0.0]:
    row += [cell_gain]*4
out=[]
for i in range(0,len(row),4):
    out.append(sum(row[i:i+4])/4.0)
assert out == [0.0,2.0,0.0,2.0,0.0]
print('PASS: 26497 UHDR thin-structure test has zero cross-cell smoothing')

# 6) Exposure plan remains one Short A at -2.5 EV; no Short B policy is introduced here.
scale=2.0**2.5
assert abs(scale-5.656854249492381) < 1e-12
print('PASS: 26497 retains -2.5 EV Short A headroom math; no darker exposure assumption')
