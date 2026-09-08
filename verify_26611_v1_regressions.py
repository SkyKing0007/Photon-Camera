#!/usr/bin/env python3
import math,sys

def fail(m): raise SystemExit('FAIL: '+m)
def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def smoothstep(a,b,x):
    t=clamp((x-a)/(b-a)); return t*t*(3-2*t)

def strict_boundary_residual(residual): return 1.0-smoothstep(0.35,0.95,max(residual,0.0))
def propagation_flow(delta): return 1.0-smoothstep(0.50,1.25,max(delta,0.0))

def short_final(ordinary,physical,component_trust,headroom,literal_loss):
    censored=min(physical,min(headroom,component_trust))
    pc=clamp(literal_loss)
    return (1-pc)*ordinary+pc*censored

# Exact 26610 device failure: p50=2.457 RAW px must not be able to seed a boundary anymore.
if strict_boundary_residual(2.4570312) != 0.0: fail('26610 p50 residual still seeds SHORT')
if strict_boundary_residual(0.35) < 0.999999: fail('good sub-pixel residual not fully trusted')
if strict_boundary_residual(0.95) > 1e-9: fail('near-one-pixel residual not rejected')
# Connected interior propagation may retain a smooth motion field but cannot cross ~CFA-phase flow jumps.
if propagation_flow(0.25) < 0.999: fail('smooth clipped interior propagation broken')
if propagation_flow(1.25) > 1e-9: fail('CFA-meaningful flow discontinuity not blocked')
# Literal clipping itself cannot create trust: component trust zero => no rescue even with perfect source/physical weights.
if short_final(0.0,1.0,0.0,1.0,1.0) != 0.0: fail('clipped core self-seeded without boundary trust')
# Effective/sub-clipping evidence does not enter physical_censor: exact ordinary weight is retained.
for ordinary in (0.0,0.17,0.63,1.0):
    if abs(short_final(ordinary,1.0,1.0,1.0,0.0)-ordinary)>1e-12: fail('nonliteral loss changed ordinary NORMAL weight')
# Valid physically clipped core survives only with proven propagated trust and common physical protection.
if abs(short_final(0.0,0.82,0.91,0.95,1.0)-0.82)>1e-12: fail('valid clipped core recovery broken')
if short_final(0.0,0.0,1.0,1.0,1.0)!=0.0: fail('common physical protection can be bypassed')

# HDR-independent VGN direction: below white is identical; above white preserves direction by one scalar.
def max3(v): return max(v)
def hdr_direction(physical):
    m=max(max3(physical),1.0); return tuple(max(0.0,min(1.0,x/m)) for x in physical)
for v in [(0.2,0.4,0.8),(0.95,0.7,0.1)]:
    if any(abs(a-b)>1e-12 for a,b in zip(hdr_direction(v),v)): fail('below-white VGN input changed')
v=(1.30,0.92,1.22); d=hdr_direction(v)
ratio_in=(v[1]/v[0],v[2]/v[0]); ratio_out=(d[1]/d[0],d[2]/d[0])
if max(abs(a-b) for a,b in zip(ratio_in,ratio_out))>1e-12: fail('HDR color direction distorted')

# New restore: cleaned direction is sole chroma authority; physical carrier supplies one scalar maxRGB only.
def restore(physical,cleaned):
    pm=max3(physical)
    if pm<=1.0: return cleaned
    cm=max3(cleaned)
    direction=(1.0,1.0,1.0) if cm<=1e-6 else tuple(x/cm for x in cleaned)
    return tuple(x*pm for x in direction)
# Neutral cleanup must stay neutral even if old physical carrier is strongly magenta.
r=restore((1.30,0.92,1.22),(1.0,1.0,1.0))
if max(r)-min(r)>1e-12 or abs(max3(r)-1.30)>1e-12: fail('dirty magenta resurrected or HDR magnitude lost')
# Real blue highlight must remain blue with exact scalar HDR magnitude.
clean_blue=(0.30,0.50,1.0); r=restore((0.40,0.80,2.40),clean_blue)
expected=tuple(x*2.40 for x in clean_blue)
if max(abs(a-b) for a,b in zip(r,expected))>1e-12: fail('real colored HDR direction not preserved')
# Below white post-VGN behavior remains exactly cleaned RGB.
clean=(0.71,0.66,0.58)
if restore((0.75,0.70,0.61),clean)!=clean: fail('below-white VGN behavior changed')

# 26610 dirty restore fixture must demonstrably fail the new invariant.
def old_restore(physical,cleaned):
    proxy=tuple(clamp(x) for x in physical)
    return tuple(max(0.0,p+(c-q)) for p,c,q in zip(physical,cleaned,proxy))
old=old_restore((1.30,0.92,1.22),(1.0,1.0,1.0))
if max(old)-min(old)<0.20: fail('regression fixture no longer reproduces 26610 dirty chroma resurrection')

# Decisive neutral proof must be capable of removing more than legacy 0.05/40% cap; ambiguous proof stays capped.
def maximum_move(center_mag,desired,decisive): return (1-decisive)*min(0.050,0.40*center_mag)+decisive*desired
if maximum_move(0.30,0.25,1.0)<0.249999: fail('decisive neutral proof remains legacy-capped')
if abs(maximum_move(0.30,0.25,0.0)-0.05)>1e-12: fail('ambiguous/real-color legacy cap changed')

print('PASS exact 26610 p50=2.457 RAW-pixel device failure cannot seed SHORT boundary trust')
print('PASS physically clipped interior cannot self-seed; only boundary-proven propagated trust can rescue and common physical protection remains hard cap')
print('PASS effective/sub-clipping loss retains exact ordinary NORMAL weight')
print('PASS HDR-independent VGN direction preserves below-white bytes and above-white RGB direction ratios')
print('PASS clean-direction scalar HDR restore preserves physical maxRGB magnitude without reintroducing dirty per-channel chroma; real colored HDR remains colored')
print('PASS decisive neutral CFA proof can exceed old 0.05/40% cleanup ceiling while ambiguous/real-color cases retain legacy cap')
print('PASS 26610 old restore fixture fails by construction, proving regression relevance')
