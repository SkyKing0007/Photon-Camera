#!/usr/bin/env python3
"""26971 exact historical 26970 guarded Actions build prefix and one publication."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
p=R/'26970_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml';wf=R/'.github/workflows/build-26971-change-aware.yml'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='bf7c875eec9c9576051edf778c6a4183e9100b8eecd44b107de6f879c2dc1a7c'
a=p.read_text();b=wf.read_text()
first='      - name: Checkout intended experimental branch'
last='      - name: Fetch ONLY exact successful 26968 Actions artifact 14601236629'
assert first in a and first in b and last in a
historical=a[a.index(first):a.index(last)]
assert historical in b,'26970 successful guarded historical prefix was edited; halt'
assert b.count('actions/upload-artifact@v4')==1
assert b.count('      - name: Publish exactly one verified 26971 APK and actual compiled source TAR')==1
assert b.count('      - name: One mandatory real 26971 Android dual-ABI NDK Kotlin Java and full assembleDebug')==1
assert b.count('      - name: Compile exact successful 26970 shaders before changed 26971 source')==1
assert 'bash compile_26904_shaders_v2.sh' in b and 'verify_26904_v3_cmake_handoff.py --handoff' in b
assert 'bash compile_26970_shaders.sh' in b and 'bash compile_26971_shaders.sh' in b
assert 'python3 -S build_26971_incremental.py verify-compiled' in b
assert 'python3 -S build_26971_incremental.py finalize' in b
assert 'test_26903_modes.py .' in b
assert 'TRIGGER_26971.txt' in b and 'TRIGGER_26970.txt' not in b[:b.index(first)]
assert 'branches:\n      - experimental-clean-photon-rebuild' in b
assert 'hashFiles(\'app/src/main/cpp/**/*\'' in b and 'app/.cxx' in b
assert b.index('      - name: Fetch ONLY exact successful 26970 Actions artifact 14666627344')<b.index('      - name: One mandatory real 26971 Android dual-ABI NDK Kotlin Java and full assembleDebug')
assert b.count('GITHUB_TOKEN: ${{ github.token }}')==1
print('PASS 26971 literal successful 26970 historical guarded prefix; original 26904 GLSL/CMake, one real dual-ABI assemble and one published verified artifact')
