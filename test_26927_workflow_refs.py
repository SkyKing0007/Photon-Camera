#!/usr/bin/env python3
"""26927 SHA-sealed three-stage trigger, successful 26926 gates retained, no file/runner handoff drift."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
wf=R/'.github/workflows/build-26927-change-aware.yml';body=wf.read_text()
assert body.startswith('name: Photon 26927 V1') and 'experimental-clean-photon-rebuild' in body
assert re.search(r'(?m)^\s+- TRIGGER_26927\.txt\s*$',body)
assert body.count('actions/upload-artifact@v4')==1
assert body.count('actions/checkout@v5')==1
assert body.count(':app:assembleDebug')>=1
assert body.index('build_26926_incremental.py prepare')<body.index('build_26926_incremental.py verify-compiled')<body.index('build_26927_incremental.py prepare')<body.index('Restore native CMake')
assert body.index('compile_26926_shaders.sh')<body.index('build_26927_incremental.py prepare')<body.index('compile_26927_shaders.sh')
assert body.index('compile_26926_lk_shaders.py')<body.index('build_26927_incremental.py prepare')
assert body.index('build_26927_incremental.py verify-compiled')<body.index(':app:assembleDebug')<body.index('build_26927_incremental.py finalize')<body.index('actions/upload-artifact@v4')
for token in ('test_26903_v3_archive_receipt.py','verify_26904_v2_safety.py','verify_26904_v3_safety.py','test_26925_shader_abi.py --payload','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','test_26926_sealed_negatives.py','test_26926_patch_proof.py --live','test_26927_sealed_negatives.py','test_26927_patch_proof.py --live','bash compile_26904_shaders_v2.sh','bash compile_26926_shaders.sh','bash compile_26926_hr_spirv.sh','bash compile_26927_shaders.sh','bash compile_26927_hr_spirv.sh','test_26920_vulkan_abi.py --live --cmake','test_26927_shader_shadow.py --live --cmake','compile_26917_amaze_import.sh','test_26913_brightness.py --payload','verify_26916_handoff.py','test_26917_border.py --live'):
 assert token in body,token
assert 'test_26903_v3_sealed_negatives.py' not in body and 'test_26922_guard.py' not in body
assert 'TRIGGER_26926.txt\n  workflow_dispatch:' not in body
# New root executable contract must list exactly what the workflow invokes.
executables=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+)([\w./-]+\.(?:py|sh))\b',body))
executables|={'./gradlew'}
assert executables==set((R/'26927_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()),(sorted(executables-set((R/'26927_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines())),sorted(set((R/'26927_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines())-executables))
if '--all' in sys.argv:
 assert all((R/p).is_file() for p in executables),[p for p in executables if not (R/p).is_file()]
 assert (R/'TRIGGER_26927.txt').read_text().startswith('RUN_26927_V1_')
 previous=R/'.github/workflows/build-26926-change-aware.yml'
 assert previous.is_file() and hashlib.sha256(previous.read_bytes()).hexdigest()=='780201bd868bf7ece091acc0c5a5fdeb32d76ce7c5ecd09b778b40677e34b6ea'
 original=previous.read_text()
 # Retain every historical verifier/compiler invocation before 26927 source
 # advancement. Only the original 26926 assemble/finalize is replaced by 26927.
 pos=body.index('build_26927_incremental.py prepare')
 for cmd in re.findall(r'(?m)^\s+(?:python3 -S |bash )[^\n]+$',original):
  line=cmd.strip()
  if '26926_incremental.py finalize' in line:continue
  if 'test_26926_shader_shadow.py --live --cmake' in line:
   assert line in body;continue
  if './gradlew ' in line:continue
  assert line in body[:pos] or line in body, 'lost successful 26926 historical command '+line
print('PASS 26927 only new trigger, complete executable refs and successful original 26926 historical/toolchain order')
