#!/usr/bin/env python3
"""Verbatim successful 26959 preflight plus actual prior-artifact and new-source gates."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent
s=(R/'.github/workflows/build-26960-change-aware.yml').read_text()
prior=(R/'26959_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
start='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
end='      - name: Fetch only exact successful 26958 Actions artifact 14452533938'
assert prior.count(start)==prior.count(end)==1
prefix=prior[prior.index(start):prior.index(end)]
assert prefix in s and s.count(prefix)==1, '26959 successful 39-step preflight prefix changed'
for needle in (
 'python3 -S build_26959_incremental.py seal',
 'python3 -S test_26959_workflow_refs.py',
 'python3 -S test_26959_rawr051_parity.py --payload',
 'python3 -S verify_26904_v3_safety.py',
 'python3 -S verify_26904_v2_safety.py',
 'python3 -S test_26903_v3_archive_receipt.py',
 'python3 -S test_26925_shader_abi.py --payload',
 'bash compile_26904_shaders_v2.sh',
 'bash compile_26959_shaders.sh',
 'python3 -S build_26960_incremental.py fetch',
 'python3 -S build_26960_incremental.py prepare-base',
 'python3 -S build_26960_incremental.py install',
 'python3 -S build_26960_incremental.py stage-native',
 'python3 -S build_26960_incremental.py verify-compiled',
 'python3 -S build_26960_incremental.py finalize',
 'python3 -S test_26960_rawr051_parity.py --live',
 'bash compile_26960_shaders.sh',
 ':app:assembleDebug','actions/upload-artifact@v4'):
 assert needle in s,needle
assert 'runs-on: ubuntu-24.04' in s
assert 'branches:\n      - experimental-clean-photon-rebuild' in s
assert 'TRIGGER_26960.txt' in s
assert s.count('actions/upload-artifact@v4')==1
assert 'IrisCamera-0.9726960-26960-iris-rawr-debug.apk' in s
assert 'photon-26960-rawr-hdrq13-motion-color-spacing' in s
assert not re.search(r'(?m)^\s*-\s*dev\s*$',s)
# In the real GitHub checkout, ALL referenced source scripts exist and there
# are NO stale missing scripts. Local bundle is correctly only the delta.
if (R/'gradlew').is_file():
 names=set(re.findall(r'\bpython3\s+-S\s+([\w./-]+\.py)',s))
 names|=set(re.findall(r'\bbash\s+([\w./-]+\.sh)',s))
 missing=sorted(x for x in names if not (R/x).is_file())
 assert not missing,'Missing action executable: '+str(missing[:20])
print('PASS byte-identical 26959 successful prefix, no missing new scripts or stale references')
