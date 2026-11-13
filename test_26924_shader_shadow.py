#!/usr/bin/env python3
"""26924 exact generated private CMake copy + dual ABI compiled-source parity."""
from pathlib import Path
import sys,hashlib
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26924' if '--payload' in sys.argv else R
ROOT=P/'app/src/main/cpp/iris26864'; B=ROOT/'bridge'
C=(ROOT/'Iris26864VendorRawr.cmake').read_text()
M=(B/'Iris26924MultiframeCMakeLists.txt').read_text()
HEAD=(B/'Iris26924VulkanExecutor.h').read_text()
sourceNames=['Iris26924MultiframeCMakeLists.txt','Iris26924MultiframeRecorder.cpp','Iris26924MultiframeRecorder.h','Iris26924VulkanExecutor.h','Iris26924WronskiFinalize.comp']
for name in sourceNames:assert C.count(name)==1,(name,'private-shadow only')
assert C.count('foreach(N26924 IN ITEMS raw_residual raw_adjoint raw_update reference_model)')==1
for n in ['raw_residual','raw_adjoint','raw_update','reference_model']:
 assert (B/f'Iris26924_{n}.comp').is_file()
 assert M.count(f'iris26924_{n}.comp')==1
 assert n in (B/'Iris26888BOffVulkanExecutor.cpp').read_text()
assert 'Iris26923WronskiFinalize.comp' not in C
assert C.count('"${IRIS26887_VENDOR_SHADOW}/multiframe/merge_wronski/shaders/a11_finalize.comp" COPYONLY')==1
assert 'add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in C
assert '  Iris26924RawResidual,' in HEAD and '  Iris26924ReferenceModel,' in HEAD
assert M.count('src/MultiframeRecorder.cpp')==1 and M.count('src/VulkanExecutor.cpp')==1
print('PASS 26924 generated-only CMake B shadow, shader source/enum/spec/embedding ownership; native/vendor unchanged')
if '--cmake' in sys.argv:
 cxx=R/'app/.cxx';assert cxx.is_dir(),'real Android .cxx output unavailable'
 files={
 'multiframe/merge_wronski/shaders/a11_finalize.comp':B/'Iris26924WronskiFinalize.comp',
 'multiframe/pipeline/CMakeLists.txt':B/'Iris26924MultiframeCMakeLists.txt',
 'multiframe/pipeline/src/MultiframeRecorder.cpp':B/'Iris26924MultiframeRecorder.cpp',
 'multiframe/pipeline/src/VulkanExecutor.cpp':B/'Iris26888BOffVulkanExecutor.cpp',
 'multiframe/pipeline/src/AndroidBurstCoordinator.cpp':B/'Iris26888BOffHdrqCoordinator.cpp',
 'multiframe/pipeline/include/rawr/raw_gpu_pipeline/MultiframeRecorder.h':B/'Iris26924MultiframeRecorder.h',
 'multiframe/pipeline/include/rawr/raw_gpu_pipeline/VulkanExecutor.h':B/'Iris26924VulkanExecutor.h'
 }
 for n in ['raw_residual','raw_adjoint','raw_update','reference_model']:
  files[f'multiframe/merge_wronski/shaders/iris26924_{n}.comp']=B/f'Iris26924_{n}.comp'
 for abi in ('arm64-v8a','armeabi-v7a'):
  for name,ref in files.items():
   candidates=[f for f in cxx.rglob(name) if abi in f.parts and 'iris26887_b_only_vendor' in f.parts]
   assert len(candidates)==1,(abi,name,'generated shadow ABI count',candidates)
   assert candidates[0].read_bytes()==ref.read_bytes(),(abi,name,'compiled source not byte-identical')
 print('PASS 26924 BOTH NDK ABIs copied exact CMake-private code/shaders, no vendor source modification')
