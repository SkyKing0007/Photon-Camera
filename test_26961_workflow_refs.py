#!/usr/bin/env python3
"""Exact successful 26959 historical Actions preflight prefix, guarded current stage and no missing path references."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent
wf=R/'.github/workflows/build-26961-change-aware.yml'
s=wf.read_text();prior=(R/'26959_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
start='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
end='      - name: Fetch only exact successful 26958 Actions artifact 14452533938'
assert prior.count(start)==prior.count(end)==1
prefix=prior[prior.index(start):prior.index(end)]
assert prefix in s and s.count(prefix)==1,'26959 successful 39-stage historical prefix changed'
needles=(
 'python3 -S build_26959_incremental.py seal','python3 -S test_26959_workflow_refs.py',
 'python3 -S test_26959_rawr051_parity.py --payload','python3 -S verify_26904_v3_safety.py',
 'python3 -S verify_26904_v2_safety.py','python3 -S test_26903_v3_archive_receipt.py',
 'python3 -S test_26925_shader_abi.py --payload','bash compile_26904_shaders_v2.sh',
 'bash compile_26959_shaders.sh',
 'python3 -S build_26961_incremental.py fetch',
 'python3 -S build_26961_incremental.py prepare-base',
 'python3 -S build_26961_incremental.py install',
 'python3 -S build_26961_incremental.py stage-native',
 'python3 -S build_26961_incremental.py verify-compiled',
 'python3 -S build_26961_incremental.py finalize',
 'python3 -S test_26961_rawr051_parity.py --live',
 'bash compile_26961_shaders.sh',
 ':app:assembleDebug','actions/upload-artifact@v4')
for needle in needles:assert needle in s,needle
assert 'runs-on: ubuntu-24.04' in s
assert 'branches:\n      - experimental-clean-photon-rebuild' in s
assert 'TRIGGER_26961.txt' in s
assert s.count('actions/upload-artifact@v4')==1
assert 'IrisCamera-0.9726961-26961-iris-rawr-debug.apk' in s
assert 'photon-26961-26959-mottling-free-indoor-foliage' in s
assert not re.search(r'(?m)^\s*-\s*dev\s*$',s)
assert 'RAWR HDRQ motion gate strength 13 and SDR color separation' not in s
if (R/'gradlew').is_file():
 names=set(re.findall(r'\bpython3\s+-S\s+([\w./-]+\.py)',s))
 names|=set(re.findall(r'\bbash\s+([\w./-]+\.sh)',s))
 absent=sorted(p for p in names if not (R/p).is_file())
 assert not absent,'unresolved workflow references: '+str(absent[:15])
print('PASS byte-identical 26959 successful historical preflight, 26961 complete real compiler/Actions stages, no missing script references')
