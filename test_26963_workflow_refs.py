#!/usr/bin/env python3
"""Exact successful 26962 historical workflow preserved; full real native/Android successor."""
from pathlib import Path
import re,hashlib
R=Path(__file__).resolve().parent
prior=(R/'26962_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
s=(R/'.github/workflows/build-26963-change-aware.yml').read_text()
start='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
end='      - name: Fetch only exact successful 26961 Actions artifact 14489008111'
assert prior.count(start)==prior.count(end)==1
prefix=prior[prior.index(start):prior.index(end)]
assert s.count(prefix)==1,'actual successful 26962 47-stage historical prefix altered'
assert hashlib.sha256(prior.encode()).hexdigest()=='62fcad2888340af7d7e7a92a01041fb5f7892babe676369ce15a50628e4c13a3'
assert 'branches:\n      - experimental-clean-photon-rebuild' in s
assert 'TRIGGER_26963.txt' in s and '      - TRIGGER_26962.txt' not in s
assert 'runs-on: ubuntu-24.04' in s
assert s.count('actions/upload-artifact@v4')==1
for token in (
 'python3 -S build_26963_incremental.py seal',
 'python3 -S test_26963_source.py --payload',
 'python3 -S test_26963_shader_abi.py --payload',
 'python3 -S test_26963_motion_math.py --payload',
 'python3 -S test_26963_rawr051_parity.py --payload',
 'python3 -S test_26963_sealed_negatives.py',
 'python3 -S test_26963_patches.py --payload',
 'python3 -S build_26963_incremental.py fetch',
 'python3 -S build_26963_incremental.py prepare-base',
 'python3 -S test_26962_source.py --live',
 'python3 -S test_26962_tone_math.py --live',
 'python3 -S test_26962_rawr051_parity.py --live',
 'python3 -S verify_26904_v3_cmake_handoff.py --handoff',
 'bash compile_26904_shaders_v2.sh',
 'bash compile_26962_shaders.sh',
 'python3 -S build_26963_incremental.py install',
 'python3 -S build_26963_incremental.py regress',
 'bash compile_26963_shaders.sh',
 'python3 -S build_26963_incremental.py verify-compiled',
 './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
 'python3 -S build_26963_incremental.py finalize',
 'python3 -S verify_26906_native_cache.py postflight',
 'photon-26963-26962-raw-temporal-inlier-no-mottling',
 'IrisCamera-0.9726963-26963-iris-rawr-debug.apk',
 'actions/cache/restore@v4',
 'actions/cache/save@v4',
 ):
 assert token in s,token
assert '26960_B_OFF_MOTION_REJECTION' not in s
# Physical path resolution requires the actual checked out repository for historical scripts.
if (R/'gradlew').is_file():
 names=set(re.findall(r'\bpython3\s+-S\s+([\w./-]+\.py)',s))
 names |= set(re.findall(r'\bbash\s+([\w./-]+\.sh)',s))
 absent=sorted(n for n in names if not (R/n).is_file())
 assert not absent,'unresolved real workflow references: '+str(absent[:20])
print('PASS exact successful 26962 historical prefix, 26903/26904 pinned CMake and SPIR-V regression, current native compiler+NDK+Kotlin+Java+APK full stages')
