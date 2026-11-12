#!/usr/bin/env python3
"""26923: prove the REAL B Wronski finalize shader is CMake's two-ABI source."""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parent
SOURCE=R if '--live' in sys.argv or '--cmake' in sys.argv else R/'handoff_payload_26923'
shader=SOURCE/'app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp'
cmake=SOURCE/'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake'
body=cmake.read_text()
assert body.count('Iris26923WronskiFinalize.comp')==1
assert '"${IRIS26887_VENDOR_SHADOW}/multiframe/merge_wronski/shaders/a11_finalize.comp" COPYONLY' in body
assert shader.is_file()
assert '#version 450' in shader.read_text()
if '--cmake' in sys.argv:
 root=R/'app/.cxx'
 assert root.is_dir(),'No real Android .cxx compilation outputs'
 for abi in ('arm64-v8a','armeabi-v7a'):
  matched=[p for p in root.glob('**/iris26887_b_only_vendor/native/multiframe/merge_wronski/shaders/a11_finalize.comp')
           if abi in p.parts]
  assert len(matched)==1,(abi,'wrong number of compiled shadow shader sources',matched)
  assert matched[0].read_bytes()==shader.read_bytes(),(abi,'compiled shader does not equal guarded runtime source')
 print('PASS 26923 BOTH NDK ABIs CMake copied exact nine-update shader, no vendor source mutated')
else:
 print('PASS 26923 source-wired B-only Wronski finalize shader, both CMake ABIs pending')
