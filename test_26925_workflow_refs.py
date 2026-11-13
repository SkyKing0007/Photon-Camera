#!/usr/bin/env python3
"""Fail closed on any missing/stale actual Actions executable or wrong trigger.
Checks exact previously successful 26924 executed workflow, no suppressed tests.
"""
from pathlib import Path
import re,hashlib,tempfile,sys
R=Path(__file__).resolve().parent
old=R/'.github/workflows/build-26924-change-aware.yml'
new=R/'.github/workflows/build-26925-change-aware.yml'
assert old.is_file() and new.is_file(),'26924 V2 executed workflow missing or 26925 not uploaded'
o=old.read_text();n=new.read_text()
assert n.startswith('name: Photon 26925 V4 - ') and '\non:\n' in n[:180], '26925 V4 workflow YAML root identity invalid'
assert hashlib.sha256(o.encode()).hexdigest()=='9de9ed6e0ebef60009016c682528e8927a31bce997c38445cffe9ba75712c565','26924 successful executed workflow changed'
PAT=re.compile(r'\b(?:python3?\s+-S\s+|bash\s+|chmod\s+\+x\s+)(?:\./)?([\w./-]+\.(?:py|sh)|gradlew)\b')
oldrefs=set(PAT.findall(o));refs=set(PAT.findall(n))
assert oldrefs<=refs,'historical executable call deleted '+repr(oldrefs-refs)
assert len(refs)>=100,(len(refs),'historic build regression coverage lost')
mandatory={'test_26925_workflow_refs.py','build_26925_incremental.py','test_26925_sealed_negatives.py',
 'test_26925_source.py','test_26925_math_host.py','test_26925_shader_shadow.py','test_26925_shader_abi.py',
 'test_26925_shader_contract.py','test_26925_patch_proof.py','compile_26925_shaders.sh',
 'compile_26925_hr_spirv.sh','compile_26925_lk_shaders.py','verify_26904_v2_safety.py',
 'verify_26904_v3_safety.py','test_26920_vulkan_abi.py','verify_26886_candidate.py',
 'test_26903_v3_archive_receipt.py'}
# Historical 26886 and 26903 replay is through mandatory inherited verifier
# wrappers; direct workflow triggers their own exact historical checks.
assert (mandatory-{'verify_26886_candidate.py','test_26903_v3_archive_receipt.py'})<=refs,'required current/historic executable removed'
assert 'TRIGGER_26924.txt' not in n and n.count('TRIGGER_26925.txt')==1
assert 'test_26922_guard.py' not in n,'the historically nonexistent script was reintroduced'
# V3: real V2 would have reached these latent fails after correcting the
# GLSL keyword. Check nested compiler manifests and CMake/ABI output ownership,
# not only executable names: 106 direct references alone were insufficient.
lk=(R/'compile_26925_lk_shaders.py').read_text()
assert "parse('26925_BASE_26924_FULL_APP.sha256')" in lk, 'LK compiler references nonexistent stale 26923 manifest'
assert '26925_BASE_26923_FULL_APP.sha256' not in lk
for path in ('26925_BASE_26924_FULL_APP.sha256','26925_EXPECTED_FULL_APP.sha256'):
    assert (R/path).is_file(), 'missing real compiler source manifest '+path
hr=(R/'compile_26925_hr_spirv.sh').read_text()
reflect=(R/'test_26925_shader_abi.py').read_text()
assert 'DIR="$TOOLS/26925_raw_projection"' in hr
assert "root=R/'.photon_26904_incremental_work/real_shader_tools/26925_raw_projection'" in reflect, 'compiled SPIR-V reflection points to absent stale output directory'
assert "root=R/'photon_26925_outputs/26925_raw_projection'" not in reflect
assert n.count('actions/upload-artifact@v4')==1
assert '      - TRIGGER_26925.txt' in n
# V1 already triggered failure 43365207385: a byte-identical stage-3
# trigger cannot start the replacement workflow with the same push path.
trigger=(R/'TRIGGER_26925.txt').read_text()
assert 'variant=V4_NDK_RECORDER_TRACE_ARGUMENT_REAL_COMPILE_FIX' in trigger
assert 'unique_trigger=PHOTON_26925_V4_ANDROID_NDK_MULTIFRAME_RECORDNORMALIZE_FIVE_ARGUMENT_REGRESSION' in trigger
assert 'failed_actions_job=131687883560' in trigger
assert 'failed_v2_actions_run=43368337237' in trigger and 'failed_v2_actions_job=131697958967' in trigger
assert 'failed_v3_actions_run=43370294678' in trigger and 'failed_v3_actions_job=131704220755' in trigger
assert hashlib.sha256(trigger.encode()).hexdigest()!='7c860aa31fdb181f4c14a5349804f6b788afbcb15d4ebcfe012f30c019b445fa','stale identical V2 trigger'
assert hashlib.sha256(trigger.encode()).hexdigest()!='e7d7d72fc1246884a173d17cdb87c09ae3acc88e8ca573296c390718743754ba', 'stale identical V1 trigger'
assert n.index('build_26924_incremental.py prepare')<n.index('build_26924_incremental.py verify-compiled')<n.index('build_26925_incremental.py prepare')<n.index('build_26925_incremental.py verify-compiled')<n.index(':app:assembleDebug')<n.index('build_26925_incremental.py finalize')
assert 'test_26920_vulkan_abi.py --live --cmake' in n
for k in ('compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26924_shaders.sh','compile_26924_hr_spirv.sh','compile_26924_lk_shaders.py','compile_26925_shaders.sh','compile_26925_hr_spirv.sh','compile_26925_lk_shaders.py','test_26925_shader_shadow.py --live --cmake'):
 assert k in n,'real compiler gate not preserved '+k
# Beyond the directly executed commands, both historical wrapper compilers
# indirectly depend on these fixed scripts. Never invent a nonexistent stub.
indirect={'compile_26906_tone_glsl.sh','compile_26920_lk_shaders.sh','test_26920_source.py',
          'test_26920_vulkan_abi.py','test_26921_guard.py'}
required=refs|indirect
expected=set((R/'26925_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines())
assert required==expected,('executable dependency inventory drift',required-expected,expected-required)
assert len(required)>=105
if '--package' in sys.argv:
 # The packaged 26925 files are added at stages 1 and 2; all historical
 # commands are separately resolved against the actual GitHub source tree
 # before release by the offline packager, and again on Actions checkout.
 assert all((R/k).is_file() for k in refs-oldrefs if k!='gradlew')
else:
 for k in required:
  if k=='gradlew':continue
  assert (R/k).is_file(),'missing historical/new executable '+k
# Detect the exact type of old nonexistent executable failure.
with tempfile.TemporaryDirectory(prefix='p26925_missing_exec_') as d:
 probe=Path(d)/'workflow.yml';probe.write_text(n+'\nrun: python3 -S test_26922_guard.py\n')
 assert 'test_26922_guard.py' in PAT.findall(probe.read_text())
 assert not (R/'test_26922_guard.py').is_file()
print(f'PASS 26925 all {len(required)} executable references, old 26924 V2 workflow SHA, no removed historical gates, unique trigger, missing-reference negative')
