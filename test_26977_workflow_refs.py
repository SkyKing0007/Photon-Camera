#!/usr/bin/env python3
"""Require exactly inherited historical preflight and all real compilation steps."""
import pathlib,re,hashlib
R=pathlib.Path(__file__).resolve().parent
old=(R/'26976_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text();new=(R/'.github/workflows/build-26977-change-aware.yml').read_text();anchor='      - name: Fetch ONLY actual successful 26975 Actions artifact 14888155360'
assert old.count(anchor)==1
prefix,tail=old.split(anchor,1)
prefix=prefix.replace(old.splitlines()[0],'name: Photon 26977 - C donor PGTM, merged noise and guarded Pro Sabre completion').replace('      - TRIGGER_26976.txt','      - TRIGGER_26977.txt')
assert new.startswith(prefix),'historical prefix changed'
current_anchor='      - name: Fetch ONLY actual successful 26976 Actions artifact 14890426950'
assert new.count(current_anchor)==1
want=re.sub('26975|26976',lambda m:{'26975':'26976','26976':'26977'}[m.group()],anchor+tail).replace('14888155360','14890426950').replace('0.9726976-26977','0.9726977-26977').replace('2390 protected','2390 protected').replace('photon-26977-c-independent-zsl-pro-sabre','photon-26977-c-donor-pro-sabre')
assert current_anchor+new.split(current_anchor,1)[1]==want,'inherited compilation tail changed'
extra=new[len(prefix):new.index(current_anchor)]
for cmd in ('build_26977_incremental.py seal','test_26977_source.py --payload','test_26977_integration_host.py --root handoff_payload_26977/app','test_26977_patches.py --payload','test_26977_sealed_negatives.py','test_26977_workflow_refs.py'):assert cmd in extra,cmd
assert new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')==1
assert new.count('actions/upload-artifact@v4')==1
for cmd in ('build_26976_incremental.py seal','test_26976_sealed_negatives.py','bash compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','bash compile_26977_shaders.sh','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','build_26977_incremental.py finalize'):assert cmd in new,cmd
for f in (R/'26977_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines():assert (R/f).is_file(),f
s=(R/'compile_26977_shaders.sh').read_text()
for t in ('EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478','--auto-map-locations --auto-map-bindings','spirv-opt --target-env=opengl4.5 -O','spirv-val --target-env opengl4.5','assert v[\'static_count\'] == 151 and v[\'dynamic_count\'] == 78','bash "$TMP"'):assert t in s,t
print('PASS successful 26976 exact historical prefix and mandatory compiler/build/publish tail, additive C tests only')
