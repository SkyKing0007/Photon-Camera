#!/usr/bin/env python3
"""Historical native and FCC/stacker/GLES sources byte-identical to successful 26927 V1."""
from pathlib import Path
import sys,subprocess
R=Path(__file__).resolve().parent
from build_26928_incremental import parse,sha,scope
original=parse(R/'26928_BASE_26927_FULL_APP.sha256');target=parse(R/'26928_EXPECTED_FULL_APP.sha256')
for name,h in original.items():
 if (name.startswith('app/src/main/cpp/') or name.startswith('app/src/main/jniLibs/') or
     '/vendor/' in name or name.endswith('.so') or name.endswith('CMakeLists.txt') or
     name.endswith('GlesMgcRawSpatialStacker.kt') or name.endswith('GlesIris26856RawrFalseColor.kt') or
     name.startswith('app/src/main/assets/')):
  assert target[name]==h,name
  if '--live' in sys.argv:assert sha(R/name)==h,name
for name in ('bridge/Iris26923WronskiFinalize.comp','Iris26885WronskiChromaGuide.comp','Iris26880WaveletCopy.comp'):
 key='app/src/main/cpp/iris26864/'+name
 assert original[key]==target[key],key
if '--cmake' in sys.argv:
 for cmd in (('test_26927_shader_shadow.py','--live','--cmake'),('test_26920_vulkan_abi.py','--live','--cmake')):
  subprocess.run(['python3','-S',*cmd],cwd=R,check=True)
print('PASS 26928 all native/CMake/vendor/AMaZE/FCC/ON/Sabre processing protected exact; same native source fingerprint before/after overlay')
