#!/usr/bin/env python3
"""Physically confirm entire last successful 26958 historical regression prefix unchanged."""
from pathlib import Path
import re,sys
R=Path(__file__).resolve().parent
p=R/'.github/workflows/build-26959-change-aware.yml'
s=p.read_text();prior=(R/'26958_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
anchor='      - name: Fetch only actually successful 26957 Actions artifact 14398233829 with proven authenticated curl'
assert anchor in prior and prior.count(anchor)==1
first='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
start=prior[prior.index(first):prior.index(anchor)]
assert start in s and s.count(start)==1, 'the successful 26958 historical regression prefix was modified'
for needle in ('python3 -S build_26958_incremental.py seal','python3 -S test_26958_sealed_negatives.py',
 'python3 -S verify_26904_v3_safety.py','python3 -S verify_26904_v2_safety.py',
 'python3 -S test_26903_v3_archive_receipt.py','python3 -S test_26925_shader_abi.py --payload',
 'bash compile_26904_shaders_v2.sh','bash compile_26958_shaders.sh',
 'python3 -S test_26959_rawr051_parity.py --payload',
 'python3 -S test_26959_rawr051_parity.py --live',
 'python3 -S build_26959_incremental.py fetch',
 'python3 -S build_26959_incremental.py prepare-base',
 'python3 -S build_26959_incremental.py install',
 'python3 -S build_26959_incremental.py verify-compiled',
 'python3 -S build_26959_incremental.py finalize',
 'python3 -S build_26959_incremental.py stage-native',
 'bash compile_26959_shaders.sh',
 ':app:assembleDebug','actions/upload-artifact@v4'):
 assert needle in s,needle
assert 'runs-on: ubuntu-24.04' in s
assert 'branches:\n      - experimental-clean-photon-rebuild' in s
assert 'dev' not in re.findall(r'(?m)^\s*-\s*dev\s*$',s)
assert 'IrisCamera-0.9726959-26959-iris-rawr-debug.apk' in s
assert s.count('actions/upload-artifact@v4')==1
assert s.count('fetch only actually successful 26957')==0
print('PASS 26958 historical regression step prefix verbatim, 26959 source and strict Actions upload gates')
