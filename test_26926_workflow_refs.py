#!/usr/bin/env python3
"""26926 stage upload guard: verifies every actual invoked executable and stage hash.
--all runs only after user uploaded all three stages into the Android checkout.
"""
from pathlib import Path
import sys,re
R=Path(__file__).resolve().parent
WF=R/'.github/workflows/build-26926-change-aware.yml';body=WF.read_text()
expected=(R/'26926_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
assert expected and len(set(expected))==len(expected)
used=set(re.findall(r'(?:python3\s+-S\s+|bash\s+)([a-zA-Z0-9_][a-zA-Z0-9_.-]+\.(?:py|sh))\b',body))
assert used==set(expected),('stale or unlisted Actions executable',sorted(used-set(expected)),sorted(set(expected)-used))
assert body.count('actions/upload-artifact@v4')==1
assert 'TRIGGER_26926.txt' in body
assert 'build_26926_incremental.py prepare' in body
assert body.index('build_26926_incremental.py prepare') < body.index('Restore native CMake')
# Original successful 26923 did not require a generated 26902 runner.
# Reproduce the 26903 archive failure as a standalone targeted fixture and
# retain real Night mode tests on the compiled candidate. No extra orphan runner.
assert 'test_26903_v3_sealed_negatives.py' not in body
assert 'build_26902_iris_rawr.sh' not in body
for required in ('python3 -S build_26923_incremental.py fetch',
                 'python3 -S build_26923_incremental.py prepare',
                 'python3 -S test_26923_shader_contract.py',
                 'python3 -S test_26923_patch_proof.py --live',
                 'python3 -S test_26923_workflow_refs.py',
                 'python3 -S verify_26904_v3_safety.py',
                 'python3 -S verify_26904_v2_safety.py',
                 'python3 -S test_26903_v3_archive_receipt.py',
                 'python3 -S test_26903_modes.py .',
                 'bash compile_26904_shaders_v2.sh',
                 'bash compile_26926_shaders.sh',
                 'bash compile_26926_hr_spirv.sh',
                 'verify_26904_v3_cmake_handoff.py --handoff',
                 'bash compile_26907_hue_glsl.sh',
                 'bash compile_26908_render_glsl.sh',
                 'bash compile_26917_amaze_import.sh',
                 'python3 -S compile_26923_lk_shaders.py',
                 'test_26926_shader_shadow.py --live --cmake',
                 ':app:assembleDebug',
                 'build_26926_incremental.py finalize'):
 assert required in body, ('successful 26923 compiler/regression gate missing',required)
# During Actions verify original historical 26923 workflow bytes are the
# same as the one preserved in its successful published Actions artifact.
if '--all' in sys.argv:
 import hashlib
 historical=R/'.github/workflows/build-26923-change-aware.yml'
 assert historical.is_file(), 'original successful 26923 workflow missing'
 assert hashlib.sha256(historical.read_bytes()).hexdigest()=='d86417c39d9879201191469233e693f270844f5f7f88c377eafebd9c79481d2c', '26923 original executed workflow drifted'
 # All commands from the successful 26923 historical preflight (before
 # runtime source reconstruction) remain in this V3 workflow.
 original=historical.read_text().split('      - name: Restore content-addressed Gradle dependency and task caches',1)[0]
 needed=set(re.findall(r'(?:python3\s+-S\s+|bash\s+)([a-zA-Z0-9_][a-zA-Z0-9_.-]+\.(?:py|sh))\b',original))
 assert needed.issubset(used),('missing successful 26923 historical preflights',sorted(needed-used))
# All historical files are part of the existing successful Actions checkout;
# local staging contains only the new uploader contents.
new={'build_26926_incremental.py','test_26926_workflow_refs.py','test_26926_sealed_negatives.py','test_26926_source.py','test_26926_math_host.py','test_26926_shader_contract.py','test_26926_shader_shadow.py','test_26926_patch_proof.py','compile_26926_shaders.sh','compile_26926_hr_spirv.sh'}
assert new.issubset(used)
for f in new:assert (R/f).is_file(),('26926 uploaded stage missing executable',f)
if '--all' in sys.argv or (R/'gradlew').is_file():
 for f in expected:assert (R/f).is_file(),('historical executable missing from actual checkout',f)
 for f in ['26926_HANDOFF_HASHES.sha256','26926_BASE_26923_FULL_APP.sha256','26926_EXPECTED_FULL_APP.sha256','26926_PROTECTED_SOURCE.sha256','26926_CHANGED_RUNTIME_ALLOWLIST.txt','26926_ADDED_RUNTIME_PATHS.txt','26926_FORWARD_FULLINDEX.patch','26926_ROLLBACK_FULLINDEX.patch']:
  assert (R/f).is_file(),('sealed stage prerequisite missing',f)
print('PASS 26926 one workflow, exact referenced real compiler/build/test scripts, no stale Actions commands',len(expected))
