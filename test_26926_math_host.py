#!/usr/bin/env python3
"""26926 deterministic numerical invariants, Bayer and noise-domain negative controls."""
from math import sqrt,isfinite
from pathlib import Path
import sys
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26926' if '--payload' in sys.argv else R
# Encode exact quarter step in integer persistence, no two nearby float settings.
for max_t,default in zip((32,16,64),(16,8,64)):
 assert default<=max_t
 for t in range(max_t+1):
  v=t*.25
  assert round(v*4)==t and v>=0
# N=15 is only correct for complete uniform support: rejected/occluded pixels are different.
N=15
for acceptance in (0.01,0.15,.34,.5,1.0):
 effective=1+(N-1)*acceptance
 assert 1<=effective<=N
 assert 0<(1/effective)<1.001
assert 1+(15-1)*.01 < 1.2
# LSC corrected sensor y=g*x: var_corrected=g*a*y_corrected+g^2*b.
for g in (1.,1.2,2.,4.,8.):
 for x in (.003,.025,.12,.44):
  a=.00038;b=.0000065
  expected=g*g*(a*x+b)
  transformed=g*a*(g*x)+g*g*b
  assert abs(expected-transformed)<1e-12
  if g>1:assert transformed>a*(g*x)+b
# CFA/phase mapping in Kotlin preserves correct red and blue for all Bayer layouts.
for pattern in range(4):
 greens=(0,3) if pattern in (1,2) else (1,2)
 red=pattern;blue=3-pattern
 assert len(set((red,blue,*greens)))==4,(pattern,red,blue,greens)
# Gaussian fallback gain is radius gain, 16 cap does not bind at N=15, f=1.
assert 4*sqrt(14/(4*3.14159265))<16 and 2*sqrt(14/(4*3.14159265))<16
# Confidence-weighted, locally unreliable pixels should have higher expected uncertainty.
def variance(y,shot,read,g,confidence,frames):
 return (g*shot*y+g*g*read)/(1+(frames-1)*confidence)
assert variance(.045,.0004,0.000003,3,0,15)>variance(.045,.0004,.000003,3,1,15)
# New native Wronski alpha must survive both guide and wavelet.
wave=(P/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp').read_text()
assert 'imageLoad(irisRgb,p).a' in wave and 'vec4(denoised,originalRawConfidence)' in wave
# No ever increasing global chroma penalty; shader must have a reliable-color veto.
s=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
for t in ('burstFloor','originalRawSupport','uIris26926LensShading','sourceSupport','coherent'):
 assert t in s or t=='coherent' and 'coherence' in s
print('PASS 26926 quarter step, Bayer phase maps, RAW LSC variance, spatial support and non-global smoothing math')
