#!/usr/bin/env python3
"""Byte-preserve exact 26963 successful historical workflow prefix & mandatory 26964 stages."""
from pathlib import Path
import re,hashlib
R=Path(__file__).resolve().parent
prior=(R/'26963_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
s=(R/'.github/workflows/build-26964-change-aware.yml').read_text()
marker='      # 26963 read-only source and synthetic motion regressions; no diagnostic APK.'
assert prior.count(marker)==1
start='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
assert prior.count(start)==s.count(start)==1
prefix=prior[prior.index(start):prior.index(marker)]
assert prefix in s and s.count(prefix)==1,'the actual successful 26963 historical preflight steps changed'
assert hashlib.sha256(prior.encode()).hexdigest()=='9a11d1cc99ccafd2b378ae431d2ff41695f541abd1faac32511bc998c4a0ef43'
assert s.count('actions/upload-artifact@v4')==1
assert 'runs-on: ubuntu-24.04' in s
assert 'branches:\n      - experimental-clean-photon-rebuild' in s
assert '      - TRIGGER_26964.txt' in s and '      - TRIGGER_26963.txt' not in s
for needle in (
 'python3 -S build_26964_incremental.py seal',
 'python3 -S test_26964_workflow_refs.py',
 'python3 -S test_26964_source.py --payload',
 'python3 -S test_26964_motion_math.py --payload',
 'python3 -S test_26964_exposure_java.py --payload',
 'python3 -S test_26964_shader_abi.py --payload',
 'python3 -S test_26964_sealed_negatives.py',
 'python3 -S test_26964_patches.py --payload',
 'python3 -S build_26964_incremental.py fetch',
 'python3 -S build_26964_incremental.py prepare-base',
 'python3 -S test_26963_source.py --live',
 'python3 -S test_26963_shader_abi.py --live',
 'python3 -S verify_26904_v3_cmake_handoff.py --handoff',
 'bash compile_26904_shaders_v2.sh',
 'bash compile_26963_shaders.sh',
 'python3 -S build_26964_incremental.py install',
 'python3 -S test_26964_motion_math.py --live',
 'python3 -S test_26964_exposure_java.py --live',
 'bash compile_26964_shaders.sh',
 'python3 -S build_26964_incremental.py verify-compiled',
 './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
 'python3 -S verify_26906_native_cache.py postflight',
 'python3 -S build_26964_incremental.py finalize',
 'photon-26964-26963-motion-exposure-protected',
 'IrisCamera-0.9726964-26964-iris-rawr-debug.apk',
 'actions/cache/restore@v4',
 'actions/cache/save@v4'):
 assert needle in s,needle
assert not re.search(r'(?m)^\s*-\s*dev\s*$',s)
if (R/'gradlew').is_file():
 names=set(re.findall(r'\bpython3\s+-S\s+([\w./-]+\.py)',s))
 names|=set(re.findall(r'\bbash\s+([\w./-]+\.sh)',s))
 absent=sorted(p for p in names if not (R/p).is_file())
 assert not absent,'unresolved current/historical workflow references: '+str(absent[:18])
print('PASS byte-identical actual successful 26963 preflight prefix + 26904 CMake/SPIR-V regressions, full real shader/dual NDK/Kotlin/Java/assemble')
