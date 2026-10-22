#!/usr/bin/env python3
"""Pinned genuine upstream source and all production/trace native shader inputs.
Compilation uses only the REAL pinned glslangValidator 16.5.0, spirv-val and
spirv-opt through the actually packaged CMake shaderc-compatible adapter.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys
P=argparse.ArgumentParser()
P.add_argument('app_root',type=Path)
P.add_argument('--compile')
P.add_argument('--spirv-val')
P.add_argument('--spirv-opt')
P.add_argument('--out',type=Path)
a=P.parse_args();root=a.app_root.resolve();app=root/'src/main/cpp/iris26864';vendor=app/'vendor/rawr';native=vendor/'native'
lock=json.loads((vendor/'IRIS26864_RAWR_VENDOR_SOURCE_LOCK.json').read_text())
two=json.loads((vendor/'IRIS26864_TWOSLOT_RUNTIME_SOURCE_PROOF.json').read_text())
assert lock['pin']=='ce767e80bfce2e1641abf7dad6b1bf504d844fd9'
assert len(lock['files'])==97 and lock['expected_source_files']==95
assert len(two['strict_changed_file_allowlist'])==2
# IRIS_26864_NDK_VK11_MEMORY_REQUIREMENTS_39712359645
# The EXACT pinned ResourceArena original stays recorded in the upstream lock;
# Android 1.1-only API adaptation is separately narrow, with no shader/merge change.
mem=two.get('android_vk11_memory_requirements_adapter')
assert mem is not None, 'missing failed Actions 39712359645 Vulkan 1.1 source adapter'
mem_rel='native/multiframe/pipeline/src/ResourceArena.cpp'
assert mem['relative_path']==mem_rel
assert mem['upstream_sha256']==lock['files'][mem_rel]['sha256']=='f4b26c9502402be7c127d33d70c17a7a1fe9120eeb870b6c89c667f1a8e87eea'
assert mem['candidate_sha256']=='ad3749757076a9e43a6697a36341b081021b6d2252833477ac4defbe34b8ee83'
assert mem['two_original_conditional_fallbacks_replaced']==2
assert set(two['strict_changed_file_allowlist'])=={
 'native/multiframe/pipeline/include/rawr/raw_gpu_pipeline/AndroidBurstCoordinator.h',
 'native/multiframe/pipeline/src/AndroidBurstCoordinator.cpp'}
for rel,expected in lock['files'].items():
 path=vendor/rel;assert path.is_file(),('absent pinned RAWR',rel)
 if rel==mem_rel:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==mem['candidate_sha256'],('Android Vulkan 1.1 arena adapter changed',rel)
 elif rel in two['strict_changed_file_allowlist']:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==two['after_sha256'][rel],('pinned two slot adaptation',rel)
 else:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==expected['sha256'],('upstream RAWR changed unexpectedly',rel)
assert len(list(native.rglob('*.comp')))==55
bridges=[app/'bridge/Iris26864HdrqCfaToAmaze.comp',app/'Iris26864WronskiPackedCfa2x.comp',app/'Iris26864PackedSensorClipToGl.comp']
assert all(p.is_file() for p in bridges)
cm=(native/'multiframe/pipeline/CMakeLists.txt').read_text()
block=cm.split('set(RAWR_MF_SHADER_SOURCES\n',1)[1].split(')\nset(RAWR_MF_SPV_OUTPUTS)',1)[0]
specs=re.findall(r'\$\{(CMAKE_CURRENT_LIST_DIR|RAWR_MF_DIR)\}/([^\s)]+\.comp)',block)
assert len(specs)==55,(len(specs),'exact upstream CMake compilation universe changed')
files=[]
for var,tail in specs:
 path=(native/'multiframe/pipeline'/tail) if var=='CMAKE_CURRENT_LIST_DIR' else (native/'multiframe'/tail)
 assert path.is_file(),('RAWR CMake shader missing',path)
 files.append(path)
assert set(files)==set(native.rglob('*.comp')),(len(set(files)),len(list(native.rglob('*.comp'))))
print('PASS 26864 pinned upstream: 95 unchanged/source-adapted file paths plus LICENSE/NOTICE, 55 original compute shaders, exact 2 two-slot adapters plus one Vulkan 1.1 API compiler adapter')
if a.compile:
 assert a.out and a.spirv_val and a.spirv_opt
 wrapper=app/'compile_locked_rawr_glslc.py'
 assert wrapper.is_file()
 a.out.mkdir(parents=True,exist_ok=True)
 opts=['--validator='+str(Path(a.compile).resolve()),'--spirv-val='+str(Path(a.spirv_val).resolve()),'--spirv-opt='+str(Path(a.spirv_opt).resolve())]
 for shader in files:
  base=shader.stem
  for flavor in ('prod','trace'):
   dest=a.out/(f'{base}_{flavor}.spv')
   extra=['-DRAWR_PARITY_TRACE=1'] if flavor=='trace' else (['-DRAWR_MIN_GATE=1'] if base=='robust_photometric' else [])
   subprocess.run([sys.executable,'-S',str(wrapper),*opts,'--target-env=vulkan1.1','-O',*extra,str(shader),'-o',str(dest)],check=True)
 for i,shader in enumerate(bridges):
  dest=a.out/(f'iris_bridge_{i}.spv')
  subprocess.run([sys.executable,'-S',str(wrapper),*opts,'--target-env=vulkan1.1','-O','-I'+str(native/'shader_common/shaders'),str(shader),'-o',str(dest)],check=True)
 assert len(list(a.out.glob('*.spv')))==113
 print('PASS 26864 real 58 SPIR-V compute shaders: 55 upstream * two variants + 3 Iris bridges, optimized, pre/post spirv-val validated')
