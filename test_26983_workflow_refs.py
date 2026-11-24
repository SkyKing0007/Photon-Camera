from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
old=(R/'26982_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
new=(R/'.github/workflows/build-26983-change-aware.yml').read_text()
split='      - name: Fetch ONLY actual successful 26981 Actions artifact 14949744442'
prefix=old.split(split)[0].replace(old.splitlines()[0],new.splitlines()[0],1).replace('      - TRIGGER_26982.txt','      - TRIGGER_26983.txt',1)
assert new.startswith(prefix)
for s in ('verify_26904_v3_cmake_handoff.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py','test_26925_sealed_negatives.py','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','compile_26983_shaders.sh','compile_26983_con_shaders.sh','build_26983_incremental.py finalize','./gradlew --no-daemon --build-cache :app:assembleDebug','14960894133','TRIGGER_26983.txt','if-no-files-found: error'):
 assert s in new,s
assert new.count('actions/upload-artifact@v4')==1
assert '14949744442' not in new[new.index('      - name: Fetch ONLY actual successful 26982'):]
print('PASS inherited executed workflow byte-prefix, mandatory historical/real compiler/assembly/publish gates, new 13 C ON GLSL stages')
