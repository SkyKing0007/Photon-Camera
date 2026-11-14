#!/usr/bin/env python3
from pathlib import Path
import sys
from build_26929_incremental import scope,sha
R=Path(__file__).resolve().parent
changes,added,original,target=scope()
sh='app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp'
impl='app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc'
assert {p for p in changes if p.startswith('app/src/main/cpp/')}=={sh,impl}
for name,h in original.items():
 if (name.startswith('app/src/main/cpp/') or name.startswith('app/src/main/jniLibs/') or
     '/vendor/' in name or name.endswith('.so') or name.endswith('CMakeLists.txt') or
     name.startswith('app/src/main/assets/')) and name not in changes:
  assert target[name]==h,name
  if '--live' in sys.argv:assert sha(R/name)==h,name
if '--cmake' in sys.argv:
 # Never substitute a static assertion for real project dual-ABI NDK proof:
 # both CMake tasks and full :app:assembleDebug are mandatory in the runner.
 import glob
 a=list((R/'app/.cxx').rglob('build.ninja'))
 assert a,'real native CMake outputs required'
 # Prior actual generated shader CMake tests run on the historical 26928 stage;
 # current native copy SPIR-V is checked by compiler hashes and Gradle.
print('PASS 26929 native exact allowlist, all other vendor/CMake/GLSL/ABI assets unchanged')
