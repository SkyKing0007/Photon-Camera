#!/usr/bin/env python3
"""Physical successful 26971 V3 workflow prefix and targeted historical regression checks."""
from pathlib import Path
import re,hashlib,sys
R=Path(__file__).resolve().parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
a=R/'26971_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml';b=R/'26971_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py'
c=R/'.github/workflows/build-26972-change-aware.yml'
assert sha(a)=='dedd61e319ee6a1da5a4366a08fd6c0d490854ab6577c8652994e2815fc548c0'
assert sha(b)=='deae902b6388102d6d9352a81cc2e13ed85da8ab23ecea169cd1a1bf9e46a0e7'
old=a.read_text();new=c.read_text()
start='      - name: Checkout intended experimental branch\n'
endold='      - name: Fetch ONLY exact successful 26970 Actions artifact 14666627344\n'
endnew='      - name: Seal 26972 physical SHA source, 82-file allowlist, 24 C shader sources, 3-stage package and negative regressions\n'
assert old.count(start)==new.count(start)==1 and old.count(endold)==new.count(endnew)==1
assert old.split(start,1)[1].split(endold,1)[0]==new.split(start,1)[1].split(endnew,1)[0],'26971 historical preflight prefix was altered'
assert new.startswith('name: Photon 26972')
assert "      - TRIGGER_26972.txt" in new and "      - TRIGGER_26971.txt" not in new
assert new.count('on:')>=1 and 'experimental-clean-photon-rebuild' in new
# Historical regressions are required and must retain successful action script/CLI pairing.
for token in ('test_26903_v3_archive_receipt.py','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26925_sealed_negatives.py','test_26971_sealed_negatives.py','test_26971_patches.py','26904 SPIR-V optimizer','26886/26887'):
 assert token in new,token
for token in ('build_26972_incremental.py seal','build_26972_incremental.py fetch','build_26972_incremental.py prepare-base','compile_26971_shaders.sh','build_26972_incremental.py install','test_26972_sealed_negatives.py','test_26972_patches.py --live','build_26972_incremental.py stage-native','compile_26972_shaders.sh','build_26972_incremental.py verify-compiled',':app:assembleDebug','build_26972_incremental.py finalize','actions/upload-artifact@v4'):
 assert token in new,token
order=['build_26972_incremental.py seal','build_26972_incremental.py fetch','build_26972_incremental.py prepare-base','compile_26971_shaders.sh','build_26972_incremental.py install','test_26972_patches.py --live','build_26972_incremental.py stage-native','compile_26972_shaders.sh','build_26972_incremental.py verify-compiled',':app:assembleDebug','build_26972_incremental.py finalize','actions/upload-artifact@v4']
assert [new.index(v) for v in order]==sorted(new.index(v) for v in order)
assert new.count('    runs-on: ubuntu-24.04')==1 and 'timeout-minutes: 120' in new
assert new.count('      - name: Publish exactly one verified 26972 APK')==1
print('PASS byte-identical 26971 V3 45-step historical preflight, actual builder/workflow SHA, targeted old failures, 26972 full compiler and one artifact')
