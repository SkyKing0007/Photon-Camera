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
# The 26903 V3 historical sealed-negative validator REQUIRES an exact
# successful 26902 generated runner fixture. Original 26926 failed before
# any Android compiler because it did not upload this INDIRECT prerequisite.
# Do not mock the runner, skip the historic regression, or generate it on
# Actions without its original successful SHA-frozen ancestry.
from hashlib import sha256
prior=R/'build_26902_iris_rawr.sh'
assert prior.is_file(), 'RESTORED ORIGINAL 26902 SUCCESSFUL RUNNER MISSING (26926 V1 Actions failure)'
assert sha256(prior.read_bytes()).hexdigest()=='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc', '26902 original successful runner SHA mismatch'
assert 'python3 -S test_26903_v3_sealed_negatives.py' in body, 'historical negative regression removed'
# Existing pinned Android compiler / assemble steps MUST NOT be narrowed.
for required in ('bash compile_26904_shaders_v2.sh',
                 'bash compile_26926_shaders.sh',
                 'bash compile_26926_hr_spirv.sh',
                 'verify_26904_v3_cmake_handoff.py --handoff',
                 ':app:assembleDebug',
                 'test_26926_shader_shadow.py --live --cmake',
                 'build_26926_incremental.py finalize'):
 assert required in body, ('original mandatory build gate removed',required)
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
