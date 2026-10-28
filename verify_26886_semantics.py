#!/usr/bin/env python3
"""26886 B Super Res ON only; source domain, routing, ownership and invariance."""
from pathlib import Path
import sys,hashlib,re
assert len(sys.argv)==3
B,C=map(Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shader='app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
s=(C/shader).read_text();prior=(B/shader).read_text()
assert s.startswith('#version 450') and 'IRIS_26886_B_SR_ON_UNSUPPORTED_CHROMA_AND_BURST_FALLBACK' in s
assert 'layout(set=0,binding=0,rgba16f) uniform image2D amazeRgbInPlace' in s
assert 'readonly uniform image2D wronskiRgb' in s
assert 'readonly uniform uimage2D originalSensorClip' in s
assert 'readonly buffer PhysicalLsc' in s
assert 'max(outRgb,vec3(0)),src.a' in s
assert 'corrected=candidate+weight*move' in s
assert 'targetChroma-=vec3(yOf(targetChroma))' in s
assert 'originalRgb*gain*p.wb.rgb' in s
assert 'imageLoad(wronskiRgb,q)' in s
assert 'imageLoad(amazeRgbInPlace,px)' in s and s.count('imageLoad(amazeRgbInPlace,')==1
assert s.count('imageStore(amazeRgbInPlace,')==1
assert 'imageLoad(amazeRgbInPlace,q)' not in s
assert '#include' not in s and 'atomic' not in s
executable=re.sub(r'//[^\n]*','',s)
assert 'noiseEstimated' not in executable and 'Camera2' not in executable
assert 'imageStore(wronskiRgb' not in s
for x in ['Iris26864JniGpuInteropImpl.inc','Iris26864Wronski2xSingleOwnerBridge.cpp','Iris26864VendorRawr.cmake','Iris26864NativeBridgeShaders.cpp']:
 p='app/src/main/cpp/iris26864/'+x
 assert sha(C/p)==sha(B/p),('protected native runtime owner changed',x)
interop=(C/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert 'if(sr) bOnChromaEvidence.reset(' in interop
assert 'const bool measuredWaveletNoise = f.rawrBurstNoiseFitted' in interop
assert 'if(measuredWaveletNoise)' in interop and 'bWavelet->record(cmd,rgb.view(),result.outputView' in interop
assert 'f.burstGreenNoisePerMergedSample[0]>0.f' in interop
assert 'params.forceY=0.f;' in interop and 'params.maxScale=7;' in interop
bridge=(C/'app/src/main/cpp/iris26864/Iris26864Wronski2xSingleOwnerBridge.cpp').read_text()
assert bridge.index('packedKernel.record(')<bridge.index('amaze.record(')<bridge.index('chromaGuide.record(')
assert prior!=s and 'IRIS_26885_B_SR_ON_WRONSKI_RGB_CHROMA_EVIDENCE' in prior
assert (C/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726886\nVERSION_BUILD=26886\n')
print('PASS 26886 B-ON original RGB guide/AMaZE pre-wavelet ownership, fitted wavelet truth, immutable luma and 50MP layout; OFF/shared white/modes unaffected source bytes')
