#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parent
old=(R/'26983_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text();new=(R/'.github/workflows/build-26984-change-aware.yml').read_text()
marker='      - name: Fetch ONLY actual successful 26982 Actions artifact 14960894133\n'
a,b=old.split(marker);prefix=a.replace(a.splitlines()[0],new.splitlines()[0],1).replace('      - TRIGGER_26983.txt','      - TRIGGER_26984.txt',1)
assert new.startswith(prefix)
newmarker='      - name: Fetch ONLY actual successful 26983 Actions artifact 14982944252\n';assert new.count(newmarker)==1
actual_tail=new[new.index(newmarker):]
expected=(marker+b).replace('26983','26984').replace('26982','26983').replace('14960894133','14982944252').replace('2395 protected','2481 protected').replace('Install exactly pinned 26984 independent C ZSL and original Pro Sabre, verify complete source and gallery publisher','Install exact 26984 C settings correction, verify full source and original gallery publisher').replace('photon-26984-c-on-lkr-direct-preview','photon-26984-c-mgc-slider-settings')
expected=expected.replace('          python3 -S test_26984_patches.py --frozen\n','          python3 -S test_26984_patches.py --frozen\n          python3 -S test_26975_v5_asset_host.py --live\n          python3 -S test_26975_v10_minimal_core.py --payload\n',1)
assert actual_tail==expected,'26983 V2 actual compiler/assembly tail changed beyond successor refs'
for x in ('test_26984_source.py --payload','test_26984_patches.py --payload','test_26984_sealed_negatives.py','test_26984_workflow_refs.py','verify_26904_v3_cmake_handoff.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py','compile_26984_shaders.sh','compile_26984_con_shaders.sh','./gradlew --no-daemon --build-cache :app:assembleDebug','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','build_26984_incremental.py finalize','if-no-files-found: error'):assert x in new,x
assert new.count('actions/upload-artifact@v4')==1
builder=(R/'build_26984_incremental.py').read_text()
assert 'def historical_26982(' not in builder and '26983_ROLLBACK_FULLINDEX.patch' not in builder
assert builder.count('actions/artifacts/{ART_ID}/zip')==1 and 'ART_ID=14982944252' in builder
assert 'test_26984_latest_preflight.py' in builder
print('PASS exact 26983 V2 executed workflow historical prefix and compiler/assemble/publish tail; latest-only recovery and explicit historical fixture checks')
