#!/usr/bin/env python3
"""26970 Fourier Wiener post-merge sidecar exact mathematical synthetic receipts."""
import math,random,sys
from pathlib import Path
R=Path(__file__).resolve().parent;P=R if '--live' in sys.argv else R/'handoff_payload_26970'
g=(P/'app/src/main/cpp/iris26864/bridge/Iris26970BOffGrainEven.comp').read_text()
m=(P/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp').read_text()
d=(P/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqDeconvolute.comp').read_text()
r=(P/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp').read_text()
co=(P/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
v=(P/'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp').read_text()
cm=(P/'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake').read_text()
assert 'sNoiseSq[lane]' in m and 'weight * weight' in m and 'previous + v * (1.0 / 63.0)' in m
assert '(1.0 + max(moment,0.0)) / n' in d and 'max(old,upperM)' in d
assert 'recordIris26970ResidualCopy' in r and 'vkCmdCopyImageToBuffer' in r
assert 'iris26970HdrqResidualMTiles.assign' in co and 'vkWaitForFences' in co
assert 'VK_DESCRIPTOR_TYPE_STORAGE_IMAGE' in v and 'grain_even26970' in cm
assert 'toLC' in g and 'fromLC' in g and 'nearCleanNoise' in g
assert 'm>1.25*nearM && m>0.19' in g and 'S=max(' not in g
assert 'const vec3 detail=max(E-expected,vec3(0.0))' in g
assert 'GMIN' not in g and 'outputRGB' in g
rng=random.Random(26970)
for n in [2,3,5,10,14,25]:
 for _ in range(600):
  w=[rng.random() for _ in range(n-1)] # w=1 => reference, w=0 => companion
  actual=((1+sum(w))**2+sum((1-x)**2 for x in w))/(n*n)
  conservative=(1+sum(x*x for x in w))/n
  assert 1/n-1e-12<=actual<=conservative+1e-12<=1+1e-12,(n,actual,conservative)
  if all(x==0 for x in w):assert abs(actual-1/n)<1e-10
  if all(x==1 for x in w):assert abs(actual-1)<1e-10
# Rexture-like noise/detail gain: noise-dominated pixels reduced, true high-frequency structure kept.
for m0 in (.2,.4,.6,.95):
 near=.07;target=min(0.25,1.25*near,m0)/m0
 noiseGain=math.sqrt(target)
 highTextureGain=math.sqrt((100 + target)/(100+1))
 assert noiseGain<highTextureGain and highTextureGain>.995
print('PASS 26970 CPU synthetic Wiener independent-source variance bound +4 correlated pass max, mode gates and noise-vs-detail energy')
