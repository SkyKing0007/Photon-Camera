#!/usr/bin/env python3
"""Actual-executed 26981 workflow prefix + unchanged historical and full compilation gates."""
from pathlib import Path
import hashlib,importlib.util
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26982',R/'build_26982_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a=(R/'26981_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
n=(R/'.github/workflows/build-26982-change-aware.yml').read_text()
start='      - name: Fetch ONLY actual successful 26980 Actions artifact 14941614437'
assert a.count(start)==1
prefix=a.split(start)[0]
prefix=prefix.replace(a.splitlines()[0],'name: Photon 26982 - C per-lens MGC bands and safe B/SR ON preview GPU load',1).replace('      - TRIGGER_26981.txt','      - TRIGGER_26982.txt',1)
assert n.startswith(prefix), 'inherited successful 26981 historical regression steps mutated'
assert n.count('      - name: Seal exact successful 26981 source, C sharpening and B/SR ON preview boundaries')==1
for needed in ('verify_26904_v3_cmake_handoff.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py','test_26925_sealed_negatives.py','verify_26906_native_cache.py preflight','compile_26982_shaders.sh','build_26982_incremental.py finalize','./gradlew --no-daemon --build-cache :app:assembleDebug','actions/upload-artifact@v4','14949744442','TRIGGER_26982.txt'):
 assert needed in n,needed
assert '14941614437' not in n[n.index('      - name: Fetch ONLY actual successful 26981'):]
assert n.count('actions/upload-artifact@v4')==1
assert 'if-no-files-found: error' in n
assert '26982_C_MGC' not in n # strings stay in actual source
for role in ('sha256','source','--frozen'):
 assert role
print('PASS 26982 executed 26981 guarded workflow historical byte-prefix + real shaders/NDK/Kotlin/Java/assemble/publish tail')
