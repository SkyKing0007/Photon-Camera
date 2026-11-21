#!/usr/bin/env python3
"""26973 successful historical workflow prefix byte unchanged; 26974 adds real compiler gates."""
from pathlib import Path
import re,hashlib
R=Path(__file__).resolve().parent
before=(R/'26973_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
after=(R/'.github/workflows/build-26974-change-aware.yml').read_text()
p='      - name: Fetch ONLY exact successful 26972 Actions artifact 14715277974'
q='      - name: Seal 26974 exact successful 26973 source, preview-shutter C ownership and 2128 protected'
assert before.count(p)==1 and after.count(q)==1
first=before[:before.index(p)]
fixed=after[:after.index('      # All successful 26973 historical preflight commands above remain byte-identical.')]
first=first.replace('name: Photon 26973 - successful 26972 source, selectable C guarded device trial', 'name: Photon 26974 - exact successful 26973 source, independent C shutter lifecycle repair',1).replace('      - TRIGGER_26973.txt','      - TRIGGER_26974.txt',1)
assert first==fixed,'successful 26973 historical prefix changed; no relaxation'
assert after.count('      - name:')==before.count('      - name:')+1
assert after.count('      - name: Fetch ONLY exact successful 26973 Actions artifact 14717056814')==1
assert after.count('      - name: Publish exactly one verified 26974 APK and actual compiled source TAR')==1
for x in ('python3 -S build_26974_incremental.py seal','python3 -S test_26974_sealed_negatives.py','python3 -S test_26974_source.py --live --host-java','python3 -S test_26974_patches.py --live','python3 -S build_26974_incremental.py prepare-base','python3 -S build_26974_incremental.py stage-native','bash compile_26974_shaders.sh','python3 -S build_26974_incremental.py verify-compiled','python3 -S build_26974_incremental.py finalize','./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace','verify_26906_native_cache.py postflight','bash compile_26904_shaders_v2.sh','python3 -S verify_26904_v3_cmake_handoff.py --handoff','actions/upload-artifact@v4'):
 assert x in after,x
assert 'TRIGGER_26974.txt' in after[:200] and 'TRIGGER_26973.txt' not in after[:200]
assert 'photon_26974_outputs/' in after and 'IrisCamera-0.9726974-26974-iris-rawr-debug.apk' in after
assert before[:before.index(p)].count('      - name:')==after[:after.index(q)].count('      - name:')
print('PASS 26974 EXACT successful 26973 historical workflow prefix unchanged, additive C-only gates, actual shader SPIR-V Kotlin Java dual-ABI NDK assemble and published artifact preserved')
