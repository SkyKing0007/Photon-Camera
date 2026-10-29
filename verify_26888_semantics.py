#!/usr/bin/env python3
"""Actual successful 26887 -> frozen 26888 ownership, domain, ABI, and GPU handoff assertions."""
from pathlib import Path
import hashlib,sys,re
assert len(sys.argv)==3,'BASE CAND expected';B,C=map(Path,sys.argv[1:])
r='app/src/main/cpp/iris26864/'
def txt(root,path):return (root/path).read_text()
def equal(path):return hashlib.sha256((B/path).read_bytes()).digest()==hashlib.sha256((C/path).read_bytes()).digest()
allow=Path(__file__).with_name('26888_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)==9 and all(x.startswith(r) or x=='app/version.properties' for x in allow)
assert set(x for x in allow if x in [p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()])=={
 r+'Iris26864VendorRawr.cmake',r+'bridge/Iris26887BOffHdrqMerge.comp',
 r+'bridge/Iris26887BOffHdrqMismatchNorm.comp',r+'bridge/Iris26887BOffHdrqRecorder.cpp','app/version.properties'}
# B ON and A experimental routing preserved at identical bytes.
for path in (r+'Iris26864JniGpuInteropImpl.inc',r+'Iris26864Wronski2xSingleOwnerBridge.cpp',
 r+'Iris26885WronskiChromaGuide.comp',r+'Iris26864FrozenDirectRawrRunner.cpp',
 r+'Iris26864NativeBridgeShaders.cpp',r+'Iris26864NativeBridgeShaders.hpp'):
 assert equal(path),('protected routing changed',path)
# All vendored 102 native RAWR files retained byte-for-byte.
vd=r+'vendor/rawr/native/'
v=[p.relative_to(B).as_posix() for p in (B/vd).rglob('*') if p.is_file()]
assert len(v)==102 and all(equal(p) for p in v)
cm=txt(C,r+'Iris26864VendorRawr.cmake')
for shader in ('Iris26888BOffHdrqMismatch.comp','Iris26887BOffHdrqMerge.comp','Iris26887BOffHdrqMismatchNorm.comp'):
 assert cm.count('bridge/'+shader+'"')==1,('CMake shader owner',shader)
assert cm.count('configure_file(')==8
assert 'add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in cm
assert 'add_subdirectory("${IRIS26864_VENDOR_ROOT}/multiframe/pipeline"' not in cm
rec=txt(C,r+'bridge/Iris26887BOffHdrqRecorder.cpp')
merge=txt(C,r+'bridge/Iris26887BOffHdrqMerge.comp')
mis=txt(C,r+'bridge/Iris26888BOffHdrqMismatch.comp')
exe=txt(C,r+'bridge/Iris26888BOffVulkanExecutor.cpp')
co=txt(C,r+'bridge/Iris26888BOffHdrqCoordinator.cpp')
for a in ('rawNoiseMeasured_ ? 1 : 0','ib(4, arena_.image("hdrq_weight_sum"))','ib(7, arena_.image("hdrq_weight_sum"))',
          'ShaderId::HdrqMismatch','ShaderId::HdrqMerge'):
 assert a in rec,('missing GPU bridge',a)
assert rec.index('ShaderId::HdrqMismatch') < rec.index('ShaderId::HdrqMerge')
assert 'int supportMeasured;' in merge and 'float independentSupport' in merge
assert 'binding = 4, r32f' in mis and 'binding = 7, r32f' in merge
assert 'float pointSupport(' in mis and 'p.measuredNoise != 0' in mis
assert 'Iris26888BOffHdrqMismatch' in cm and 'Iris26888BOffVulkanExecutor' in cm
assert 'Iris26888BOffHdrqPrivateHeader' in cm
assert len(co)>40000 and len(exe)>35000 and 'RAW' in co and 'vk' in exe
assert txt(C,'app/version.properties').endswith('VERSION_NAME=0.9726888\nVERSION_BUILD=26888\n')
print('PASS 26888 B-OFF exact 9-file frozen scope, preserved A/B-ON/Spektra routing, original 102-file vendor RAWR, 8 private overrides and explicit mismatch->merge support binding (source level)')
