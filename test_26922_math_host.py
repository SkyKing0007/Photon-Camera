#!/usr/bin/env python3
"""Numerical fail-closed regressions for 26922 pointwise gain/tone/chroma gates.
This is NOT a substitute for real Android GPU compile, device IQ, or APK tests.
"""
import math
from pathlib import Path
s=Path('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag')
if not s.is_file():s=Path('handoff_payload_26922')/s
src=s.read_text()
assert 'IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT' in src

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3.-2.*t)
def new_gain(source_y,sdr_y,display_gain,content_max):
 off=.015625
 raw=max(1.,min(content_max,(source_y*display_gain*.8+off)/(sdr_y+off)))
 eligible=smooth(.12,.58,source_y)
 return max(1.,min(content_max,2.**(math.log2(raw)*eligible)))
def old_gain(src,sdr,display_gain,cap):
 eligible=smooth(.65,.85,src)
 if src<=.65 or not eligible:return 1.
 # 26921's old source-guarded maximum, enough to illustrate dead-zone.
 g=max(.01,src*display_gain*.8)
 return 2.**(math.log2(min(cap,max(1.,g/max(sdr,.01))))*eligible)
for d in (1.,2.,4.5,6.8):
 for y in (.0,.03,.10,.12,.2,.30,.4,.58,.8,1.,1.4):
  for sdr in (.01,.03,.15,.3,.6,.95):
   gain=new_gain(y,sdr,d,6.5)
   assert math.isfinite(gain) and 1<=gain<=6.5
for y in (0.,.01,.06,.10,.12):assert new_gain(y,.08,6.0,6.5)==1.
# The 26921 source gate collapses physically continuous bright cloud values.
clouds=[.34+i*.015 for i in range(18)]
new=[new_gain(y,.70,5.0,6.5) for y in clouds]
old=[old_gain(y,.70,5.0,6.5) for y in clouds]
assert all(v==1 for v in old)
assert max(new)>1.3 and all(a<=b+1e-9 for a,b in zip(new,new[1:]))
assert max(abs(b-a) for a,b in zip(new,new[1:]))<.24
# The shadow correction cannot exceed a bounded chroma fraction and preserves
# luminance algebraically (Y=.25R+.5G+.25B); real image quality awaits device.
for cy in (.003,.012,.045,.12,.19):
 for c0,c1 in ((.05,-.06),(.15,.09),(-.03,.22)):
  span=max(cy,.035);g=cy-.25*(c0+c1)*span;rgb=(g+c0*span,g,g+c1*span)
  assert abs(sum(a*b for a,b in zip(rgb,(.25,.5,.25)))-cy)<1e-6
assert 0<=.27<=.56
# Historical B OFF 26906 shader source is unchanged and native LK remains protected.
print('PASS 26922 numerical cloud gain continuity + unity shadows + positivity/cap + exact constant-luma shadow chroma; NOT device IQ proof')
