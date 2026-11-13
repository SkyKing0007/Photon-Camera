#!/usr/bin/env python3
"""26926 exact original private B-only CMake shader copying; protect original vendor source."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26926' if '--payload' in sys.argv else R
C=P/'app/src/main/cpp/iris26864'
for file in ('bridge/Iris26923WronskiFinalize.comp','Iris26885WronskiChromaGuide.comp','Iris26880WaveletCopy.comp'):
 s=(C/file).read_text();assert s.startswith('#version 450') and s.count('void main()')==1,file
if '--live' in sys.argv:
 cmake=(C/'Iris26864VendorRawr.cmake').read_text()
 for shader in ('Iris26923WronskiFinalize.comp','Iris26880WaveletCopy.comp','Iris26885WronskiChromaGuide.comp'):
  assert shader in cmake,('private compiled shader excluded',shader)
 assert '"${IRIS26887_VENDOR_SHADOW}/multiframe/merge_wronski/shaders/a11_finalize.comp" COPYONLY' in cmake
 if '--cmake' in sys.argv:
  cxx=R/'app/.cxx';assert cxx.is_dir(),'Android NDK compilation output missing'
  src=(C/'bridge/Iris26923WronskiFinalize.comp').read_bytes()
  for abi in ('arm64-v8a','armeabi-v7a'):
   matches=[p for p in cxx.rglob('a11_finalize.comp') if abi in p.parts and 'iris26887_b_only_vendor' in p.parts]
   assert len(matches)==1,(abi,'private CMake shadow',matches[:3])
   assert matches[0].read_bytes()==src,(abi,'compiled private shader bytes differ')
print('PASS 26926 three current native GLSL, private CMake shadow, vendor original protected (compiled ABI where requested)')
