#!/usr/bin/env python3
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=(R/'26972_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text();cur=(R/'.github/workflows/build-26973-change-aware.yml').read_text()
assert sha(R/'26972_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')=='60b71ec1c86f3e809aebcdefa0008502277fa1d7e5d63648affe6012191dcc08'
assert sha(R/'26972_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')=='39eb9bedafc467e1faeb98c7a9c94c4ac20151fdce6fb53a2930a5b97cf26137'
start='      - name: Checkout intended experimental branch'
end='      - name: Fetch ONLY exact successful 26971 Actions artifact 14681533715'
end2='      # All successful 26972 preflight commands above are byte-identical.'
assert prior.split(start,1)[1].split(end,1)[0]==cur.split(start,1)[1].split(end2,1)[0]
for token in ('test_26903_v3_archive_receipt.py','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26971_patches.py','test_26972_patches.py','26886/26887'):
 assert token in cur,token
for token in ('build_26973_incremental.py seal','build_26973_incremental.py fetch','build_26973_incremental.py prepare-base','build_26973_incremental.py install','test_26973_source.py --live --host-java','test_26973_patches.py --live','build_26973_incremental.py stage-native','compile_26973_shaders.sh','build_26973_incremental.py verify-compiled',':app:assembleDebug','build_26973_incremental.py finalize','actions/upload-artifact@v4'):
 assert token in cur,token
arr=['build_26973_incremental.py seal','build_26973_incremental.py fetch','build_26973_incremental.py prepare-base','build_26973_incremental.py install','build_26973_incremental.py stage-native','compile_26973_shaders.sh','build_26973_incremental.py verify-compiled',':app:assembleDebug','build_26973_incremental.py finalize','actions/upload-artifact@v4']
assert list(map(cur.index,arr))==sorted(map(cur.index,arr))
assert cur.startswith('name: Photon 26973') and 'TRIGGER_26973.txt' in cur and 'TRIGGER_26972.txt' not in cur.split(start,1)[0]
assert cur.count('      - name: Publish exactly one verified 26973 APK')==1
assert 'runs-on: ubuntu-24.04' in cur and 'timeout-minutes: 120' in cur
print('PASS 26973 exact successful 26972 historical preflight, pinned real shader/native Kotlin/Java assemble and publish requirements')
