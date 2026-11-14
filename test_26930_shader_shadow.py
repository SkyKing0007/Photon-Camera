#!/usr/bin/env python3
"""26930 only private native B ON shader+JNI changed; no vendor/CMake edits."""
from pathlib import Path
import sys,subprocess
from build_26930_incremental import scope,sha
R=Path(__file__).resolve().parent
base,new=scope()[2:]
for path,h in base.items():
 if path not in ('app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
                 'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp',
                 'app/version.properties'):
  assert new[path]==h,path
  if '--live' in sys.argv and (path.startswith('app/src/main/cpp/iris26864/vendor/') or
        path.endswith('Iris26864VendorRawr.cmake') or path.endswith('CMakeLists.txt')):
   assert sha(R/path)==h,path
for path in ('app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp',
             'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'):
 assert base[path]==new[path]
if '--cmake' in sys.argv:
 assert '--live' in sys.argv
 subprocess.run(['python3','-S','test_26926_shader_shadow.py','--live','--cmake'],cwd=R,check=True)
 subprocess.run(['python3','-S','test_26920_vulkan_abi.py','--live','--cmake'],cwd=R,check=True)
print('PASS 26930 current native source: vendor/CMake/GL preserved; real compiled dual-ABI shadow if requested')
