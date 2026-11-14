#!/usr/bin/env python3
"""Only the 26928 trigger, all 26927 historical compiler/negative gates retained."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
wf=R/'.github/workflows/build-26928-change-aware.yml';body=wf.read_text()
assert body.startswith('name: Photon 26928 V1') and 'experimental-clean-photon-rebuild' in body
assert re.search(r'(?m)^\s+- TRIGGER_26928\.txt\s*$',body)
assert not re.search(r'(?m)^\s+- TRIGGER_26927\.txt\s*$',body)
assert body.count('actions/upload-artifact@v4')==1 and body.count('actions/checkout@v5')==1
assert body.count(':app:assembleDebug')>=1
assert body.index('build_26926_incremental.py prepare')<body.index('build_26926_incremental.py verify-compiled')<body.index('build_26927_incremental.py prepare')
assert body.index('build_26927_incremental.py verify-compiled')<body.index('build_26928_incremental.py fetch')<body.index('build_26928_incremental.py prepare')<body.index('build_26928_incremental.py verify-compiled')<body.index(':app:assembleDebug')<body.index('build_26928_incremental.py finalize')<body.index('actions/upload-artifact@v4')
assert body.index('compile_26926_shaders.sh')<body.index('build_26927_incremental.py prepare')<body.index('compile_26927_shaders.sh')<body.index('build_26928_incremental.py prepare')<body.index('compile_26928_shaders.sh')
for token in (
 'verify_26904_v2_safety.py','verify_26904_v3_safety.py','test_26903_v3_archive_receipt.py',
 'test_26925_shader_abi.py --payload','verify_26906_native_cache.py preflight',
 'verify_26906_native_cache.py postflight','test_26926_sealed_negatives.py',
 'test_26926_patch_proof.py --live','test_26927_sealed_negatives.py',
 'test_26927_patch_proof.py --live','test_26928_sealed_negatives.py',
 'test_26928_patch_proof.py --live','bash compile_26904_shaders_v2.sh',
 'bash compile_26926_shaders.sh','bash compile_26927_shaders.sh',
 'bash compile_26927_hr_spirv.sh','bash compile_26928_shaders.sh',
 'bash compile_26928_hr_spirv.sh','test_26920_vulkan_abi.py --live --cmake',
 'test_26927_shader_shadow.py --live --cmake','compile_26917_amaze_import.sh',
 'test_26913_brightness.py --payload','verify_26916_handoff.py','test_26917_border.py --live'):
 assert token in body,token
assert 'test_26903_v3_sealed_negatives.py' not in body and 'test_26922_guard.py' not in body
executables=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+)([\w./-]+\.(?:py|sh))\b',body))|{'./gradlew'}
expected=set((R/'26928_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines())
assert executables==expected,(sorted(executables-expected),sorted(expected-executables))
if '--all' in sys.argv:
 assert all((R/x).is_file() for x in expected),[x for x in expected if not (R/x).is_file()]
 assert (R/'TRIGGER_26928.txt').read_text().startswith('RUN_26928_V1_')
 prior=R/'.github/workflows/build-26927-change-aware.yml'
 assert prior.is_file() and hashlib.sha256(prior.read_bytes()).hexdigest()=='9d84fb402fb476c3d575b57ff72c5e893ffbc5eb1870cf9eafa4de682099f84a'
 original=prior.read_text()
 for command in re.findall(r'(?m)^\s+(?:python3 -S |bash )[\w.\- /]+$',original):
  line=command.strip()
  if 'build_26927_incremental.py finalize' in line:continue
  assert line in body,'lost successful 26927 verifier/compiler command '+line
 assert body.count('bash compile_26927_shaders.sh')==1
 assert body.count('bash compile_26928_shaders.sh')==1
print('PASS single 26928 trigger, every original successful 26927 executable/compiler/negative gate, sealed action set')
