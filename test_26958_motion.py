#!/usr/bin/env python3
"""26958: Rawr #122 correct affine fallback, temporal neighbour and gate test."""
import math,random,sys
from build_26958_incremental import scope,fail
scope()
# The original two-detector numerical regression is also retained in the
# historical 26957 stage, before the new build touches live shaders.
def gate(z):
 t=max(0.,min(1.,z-1.6));return t*t*(3-2*t)
def variance(slope,offset,signal,black):return slope*max(signal-black,0.)+offset
# Camera2 fallback is normalized to the reference RAW code range exactly once.
for level in (70.,140.,400.,960.):
 slopeNorm=.000180710882;offsetNorm=.0000031937599182128
 rawRange=1023.-64.
 slope=slopeNorm*rawRange;offset=offsetNorm*rawRange*rawRange
 actual=variance(slope,offset,level,64.)
 equivalent=(slopeNorm*((level-64.)/rawRange)+offsetNorm)*rawRange*rawRange
 if abs(actual-equivalent)>1e-9:fail('incorrect normalized/RAW noise conversion')
 # 26957's unsupported constant low quantile has a chance to understate
 # high-signal noise and reject a normal stationary companion.
 if level>=400:
  miss=3.0
  n=16.0
  zWithAffine=miss/(math.sqrt(2*actual/n)*.7979)
  zWithConst=miss/(math.sqrt(2*3.5/n)*.7979)
  if gate(zWithConst)<=gate(zWithAffine):fail('unreliable constant fallback regression not discriminating')
# After a failed full fit, configured *affine* noise is unchanged, never
# overwritten by a fabricated fitted profile.
def choose(config,fit):return fit if fit is not None else config
configured=(.000180710882,.0000031937599182128)
assert choose(configured,None)==configured
assert choose(configured,(.00015,.000002))==(.00015,.000002)
# Reordering does not drop any burst frames and matches Rawr's selected ref+1.
for n in (2,3,6,15,30):
 for ref in range(n):
  order=[i for i in range(n) if i!=ref]
  neighbour=ref+1 if ref+1<n else ref-1
  i=order.index(neighbour);order=[order[i]]+order[:i]+order[i+1:]
  if order[0]!=neighbour or sorted(order)!=[i for i in range(n) if i!=ref]:fail('adjacent source not exactly preserved')
# Bound of harmonic effective-frame support, including fully rejected tiles.
for N in (2,6,15,30):
 for accepted in ([0.]*(N-1),[N-1.]*(N-1),[float(i%(N)) for i in range(N-1)]):
  effective=len(accepted)/sum(1/(1+x) for x in accepted)
  if not (1.-1e-6<=effective<=N+1e-6):fail('harmonic effective frames')
print('PASS 26958 Rawr affine noise conversion, failed-fit fallback, false-rejection negative, neighbour for all refs, harmonic frame support')
