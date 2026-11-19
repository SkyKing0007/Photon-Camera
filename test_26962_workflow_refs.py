#!/usr/bin/env python3
"""Exact successful 26961 historical workflow prefix, same real compilers/caches, new 26962 current stages."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent
w=(R/'.github/workflows/build-26962-change-aware.yml').read_text()
p=(R/'26961_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
start='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
end='      - name: Fetch only exact successful 26959 Actions artifact 14460861326'
assert p.count(start)==p.count(end)==1
prefix=p[p.index(start):p.index(end)]
assert prefix in w and w.count(prefix)==1,'26961 successful historical steps deviated'
for needle in ('run: python3 -S build_26962_incremental.py fetch','run: python3 -S build_26962_incremental.py prepare-base',
 'python3 -S build_26962_incremental.py install','python3 -S build_26962_incremental.py stage-native',
 'python3 -S build_26962_incremental.py verify-compiled','python3 -S build_26962_incremental.py finalize',
 'python3 -S build_26961_incremental.py seal','bash compile_26961_shaders.sh','bash compile_26962_shaders.sh',
 'python3 -S verify_26904_v3_cmake_handoff.py --handoff','python3 -S verify_26904_v2_safety.py',
 'python3 -S test_26903_v3_archive_receipt.py','python3 -S test_26925_shader_abi.py --payload',
 'python3 -S test_26962_rawr051_parity.py --live',':app:assembleDebug','actions/upload-artifact@v4',
 'TRIGGER_26962.txt','IrisCamera-0.9726962-26962-iris-rawr-debug.apk','photon-26962-26961-allzoom-b-off-bodycontrast-023',
 'runs-on: ubuntu-24.04','actions/cache/restore@v4','actions/cache/save@v4'):
 assert needle in w,needle
assert w.count('actions/upload-artifact@v4')==1
assert 'on:\n  push:\n    branches:\n      - experimental-clean-photon-rebuild' in w
assert 'dev' not in re.findall(r'(?m)^\s+branches:\s*\n\s+-\s+(.+)$',w)
assert 'gradle-cache-26962' in w and 'native-cache-26962' in w
if (R/'gradlew').is_file():
 names=set(re.findall(r'\bpython3\s+-S\s+([\w./-]+\.py)',w))
 names|=set(re.findall(r'\bbash\s+([\w./-]+\.sh)',w))
 assert all((R/n).is_file() for n in names),[n for n in names if not (R/n).is_file()]
print('PASS exact 26961 historical workflow, unique 26962 trigger, pinned shader/NDK/Kotlin/Java/assemble and cache stages')
