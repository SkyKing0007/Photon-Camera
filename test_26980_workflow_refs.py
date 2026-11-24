#!/usr/bin/env python3
import pathlib,re
R=pathlib.Path(__file__).resolve().parent
old=(R/'26979_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text();new=(R/'.github/workflows/build-26980-change-aware.yml').read_text()
anchor='      - name: Fetch ONLY actual successful 26978 Actions artifact 14895638721';assert old.count(anchor)==1
prefix,tail=old.split(anchor,1)
prefix=prefix.replace(old.splitlines()[0],'name: Photon 26980 - C manual exposure optimization, exact RAW retry and donor tuning',1).replace('      - TRIGGER_26979.txt','      - TRIGGER_26980.txt',1)
assert new.startswith(prefix),'historical prefix changed'
current_anchor='      - name: Fetch ONLY actual successful 26979 Actions artifact 14926415488'
assert new.count(current_anchor)==1
want=re.sub('26978|26979',lambda m:{'26978':'26979','26979':'26980'}[m.group()],anchor+tail).replace('14895638721','14926415488').replace('2397 protected','2398 protected').replace('photon-26980-c-exposure-pro-sabre','photon-26980-c-manual-exposure-pro-sabre')
assert current_anchor+new.split(current_anchor,1)[1]==want,'inherited compilation tail changed'
extra=new[len(prefix):new.index(current_anchor)]
for cmd in ('build_26980_incremental.py seal','test_26980_source.py --payload','test_26980_integration_host.py --root handoff_payload_26980/app','test_26980_patches.py --payload','test_26980_sealed_negatives.py','test_26980_workflow_refs.py'):assert cmd in extra,cmd
assert new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')==1
assert new.count('actions/upload-artifact@v4')==1
for cmd in ('build_26979_incremental.py seal','test_26979_sealed_negatives.py','bash compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','bash compile_26980_shaders.sh','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','build_26980_incremental.py finalize'):assert cmd in new,cmd
for f in (R/'26980_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines():assert (R/f).is_file(),f
s=(R/'compile_26980_shaders.sh').read_text()
for t in ('EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478','--auto-map-locations --auto-map-bindings','spirv-opt --target-env=opengl4.5 -O','spirv-val --target-env opengl4.5',"assert v['static_count'] == 151 and v['dynamic_count'] == 78",'bash "$TMP"'):assert t in s,t
print('PASS successful 26979 exact historical prefix and mandatory compiler/build/publish tail, additive C tests only')
