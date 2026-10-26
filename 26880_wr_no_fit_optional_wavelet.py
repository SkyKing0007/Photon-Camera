#!/usr/bin/env python3
"""26880 regression: a valid Wronski merge with missing measured RAW noise
must not allocate/initialize optional GPU wavelet resources before bypass.
This is an ownership/semantic gate, NOT a native or GLSL compiler.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
site='if(measuredWaveletNoise){'
assert s.count(site)==1, 'lost exact RAW-burst wavelet fitness gate'
merger=s.index('iris26864::runRealRawrFromFrozenDirectNormals(')
fit=s.index(site)
wavelet=s.index('new raw_denoise::DenoisePipeline(')
copy=s.index('bWaveletCopy.reset(new iris26864::VulkanKernelExecutor(')
fallback=s.index('"B_WAVELET_BURST_FIT_UNAVAILABLE')
assert merger<fit<wavelet<copy<fallback, 'wavelet allocated before successful measured-fit branch'
assert 'params.maxScale=7;' in s and 'params.forceY=0.f;' in s and 'params.forceUv=.75f;' in s
assert 'wronski2x::recordWronski2xToAmaze' in s
assert 'if(measuredWaveletNoise){' in s and 'else {' in s[s.index('bWaveletCopy->record('):fallback]
assert 'Camera2' not in s[fit:fallback]
print('PASS 26880: fitted-only optional RAWR wavelet, no-fit Wronski reuse, 7-scale chroma ownership')
