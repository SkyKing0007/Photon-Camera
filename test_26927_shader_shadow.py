#!/usr/bin/env python3
"""Original 26926 native/CMake/vendor exact source invariance."""
from pathlib import Path
import sys,subprocess
R=Path(__file__).resolve().parent
from build_26927_incremental import parse,sha
base=parse(R/'26927_BASE_26926_FULL_APP.sha256')
target=parse(R/'26927_EXPECTED_FULL_APP.sha256')
for name in ('bridge/Iris26923WronskiFinalize.comp','Iris26885WronskiChromaGuide.comp','Iris26880WaveletCopy.comp','Iris26864FrozenDirectRawrRunner.cpp','Iris26864RealRawrCoordinator.cpp'):
 p='app/src/main/cpp/iris26864/'+name
 assert base[p]==target[p],p
 if '--live' in sys.argv:assert sha(R/p)==base[p]
for p,h in base.items():
 if '/vendor/' in p or '/jniLibs/' in p or p.endswith('CMakeLists.txt') or p.endswith('.so'):
  assert target[p]==h,p
if '--cmake' in sys.argv:
 for cmd in (('test_26926_shader_shadow.py','--live','--cmake'),('test_26920_vulkan_abi.py','--live','--cmake')):
  subprocess.run(['python3','-S',*cmd],cwd=R,check=True)
print('PASS 26927 3 Wronski shaders, native bridge, vendor/CMake protected; dual-ABI compiled shadow when requested')
