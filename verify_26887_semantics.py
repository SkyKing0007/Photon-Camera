#!/usr/bin/env python3
"""26887 B-only real-source semantic/domain/lifecycle contract.

Successor of 26886 semantics: historic 26886 validator MUST run on its own
successfully compiled 26885/26886 source, not this modified runtime. This
validator complements, never replaces, candidate hash and compiler gates.
"""
from pathlib import Path
import argparse,hashlib,re
p=argparse.ArgumentParser()
p.add_argument('base',type=Path);p.add_argument('candidate',type=Path)
a=p.parse_args();B=a.base;C=a.candidate
r='app/src/main/cpp/iris26864/'
def read(root,rel):return (root/rel).read_text()
def equal(rel):return hashlib.sha256((B/rel).read_bytes()).digest()==hashlib.sha256((C/rel).read_bytes()).digest()
interop=read(C,r+'Iris26864JniGpuInteropImpl.inc')
old=read(B,r+'Iris26864JniGpuInteropImpl.inc')
cma=read(C,r+'Iris26864VendorRawr.cmake')
shader=read(C,r+'Iris26885WronskiChromaGuide.comp')
assert not equal(r+'Iris26864JniGpuInteropImpl.inc')
assert not equal(r+'Iris26864VendorRawr.cmake')
assert not equal(r+'Iris26885WronskiChromaGuide.comp')
# The accepted B-ON pre-AMaZE Wronski RGB path and measured wavelet noise
# contract are not redirected through the new B-OFF witness.
for s in ('if(sr) bOnChromaEvidence.reset(',
          'const bool measuredWaveletNoise = f.rawrBurstNoiseFitted',
          'if(measuredWaveletNoise)',
          'params.forceY=0.f;', 'params.maxScale=7;'):
 assert s in old and s in interop,('inherited B-ON owner drift',s)
bridge=r+'Iris26864Wronski2xSingleOwnerBridge.cpp'
assert equal(bridge)
s=read(C,bridge)
assert s.index('packedKernel.record(')<s.index('amaze.record(')<s.index('chromaGuide.record(')
assert 'IRIS_26886_B_SR_ON_UNSUPPORTED_CHROMA_AND_BURST_FALLBACK' in shader
assert 'imageStore(wronskiRgb' not in shader
assert shader.count('imageStore(amazeRgbInPlace,')==1
# A separate B-OFF color witness only, never a replacement for RAWR HDRQ,
# AMaZE luminance, burst-count semantics, sensor clipping, or A routing.
for s in ('const bool bOffWitnessPotential=(!sr&&',
          'canSupplyTwiceEachBayerColor(',
          'if(bOffWitnessPotential){',
          'if(i!=size_t(referenceIndex)) original.prepareNormal(uint32_t(i));',
          'if(bOffWitnessAllocated && !bOffWitnessReady)',
          'if(bOffWitnessReady){',
          'Iris26887WaitedWitnessArenaRetire',
          'vkQueueWaitIdle(queue)==VK_SUCCESS',
          'B_OFF_RAW_WITNESS_SOURCE_MISSING',
          'B_OFF_RAW_WITNESS_INSUFFICIENT_LOCAL_SUPPORT'):
 assert s in interop,('B-OFF witness lifecycle/routing drift',s)
assert interop.index('iris26864::runRealRawrFromFrozenDirectNormals(')<interop.index('if(bOffWitnessPotential){')
assert interop.index('if(bOffWitnessPotential){')<interop.index('amaze::LinearRgbImage output{}')
assert interop.index('amaze.record(cmd,packedInput,output,')<interop.index('if(bOffWitnessReady){')
# Exact overlays, no mutation to upstream tree, no duplicate owner.
assert 'file(COPY "${IRIS26864_VENDOR_ROOT}/" DESTINATION "${IRIS26887_VENDOR_SHADOW}")' in cma
pairs=(('Iris26887BOffHdrqMerge.comp','hdrq_merge.comp'),
 ('Iris26887BOffHdrqMismatchNorm.comp','hdrq_mismatch_norm.comp'),
 ('Iris26887BOffHdrqDeconvolute.comp','hdrq_deconvolute.comp'),
 ('Iris26887BOffHdrqRecorder.cpp','HdrPlusRecorder.cpp'))
assert cma.count('configure_file(')==4,('unexpected build shadow overrides',cma.count('configure_file('))
for source,target in pairs:
 assert cma.count('configure_file('+'"${CMAKE_CURRENT_SOURCE_DIR}/iris26864/bridge/'+source+'"')==1
 assert cma.count('"${IRIS26887_VENDOR_SHADOW}/')>=4
 assert target in cma
assert 'add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in cma
assert 'add_subdirectory("${IRIS26864_VENDOR_ROOT}/multiframe/pipeline"' not in cma
# Preserve immutable original pinned vendor CMake/source universe, and
# native source owners outside the explicitly allowed set.
vendor=B/(r+'vendor/rawr/native');cvendor=C/(r+'vendor/rawr/native')
basefiles={f.relative_to(vendor).as_posix():f for f in vendor.rglob('*') if f.is_file()}
candfiles={f.relative_to(cvendor).as_posix():f for f in cvendor.rglob('*') if f.is_file()}
assert len(basefiles)==len(candfiles)==102
assert all(hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256(candfiles[k].read_bytes()).digest() for k,f in basefiles.items()),'original vendor write'
assert read(C,'app/version.properties').endswith('VERSION_NAME=0.9726887\nVERSION_BUILD=26887\n')
assert 'Iris26887' not in read(B,r+'Iris26864JniGpuInteropImpl.inc')
print('PASS 26887 actual compiled-source B-only routing, preserved B-ON Wronski/wavelet, frozen A/Spektra/DNG owners, vendor 102 invariant, exact 4 shadow overrides, witness memory/synchronization contract (source only)')
