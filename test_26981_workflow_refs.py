#!/usr/bin/env python3
import pathlib,re
R=pathlib.Path(__file__).resolve().parent
old=(R/'26980_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text();new=(R/'.github/workflows/build-26981-change-aware.yml').read_text()
anchor='      - name: Fetch ONLY actual successful 26979 Actions artifact 14926415488';assert old.count(anchor)==1
prefix,tail=old.split(anchor,1)
prefix=prefix.replace(old.splitlines()[0],'name: Photon 26981 - C absolute highlight target, touch exposure and adaptive shutter ISO',1).replace('      - TRIGGER_26980.txt','      - TRIGGER_26981.txt',1)
assert new.startswith(prefix),'historical prefix changed'
current_anchor='      - name: Fetch ONLY actual successful 26980 Actions artifact 14941614437';assert new.count(current_anchor)==1
want=re.sub('26979|26980',lambda m:{'26979':'26980','26980':'26981'}[m.group()],anchor+tail).replace('14926415488','14941614437').replace('2398 protected','2406 protected').replace('photon-26981-c-manual-exposure-pro-sabre','photon-26981-c-absolute-exposure-pro-sabre')
assert current_anchor+new.split(current_anchor,1)[1]==want,'inherited compilation tail changed'
extra=new[len(prefix):new.index(current_anchor)]
for cmd in ('build_26981_incremental.py seal','test_26981_source.py --payload','test_26981_integration_host.py --root handoff_payload_26981/app','test_26981_patches.py --payload','test_26981_sealed_negatives.py','test_26981_workflow_refs.py'):assert cmd in extra,cmd
assert new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')==1
assert new.count('actions/upload-artifact@v4')==1
for cmd in ('build_26980_incremental.py seal','test_26980_sealed_negatives.py','bash compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','bash compile_26981_shaders.sh','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','build_26981_incremental.py finalize'):assert cmd in new,cmd
for f in (R/'26981_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines():assert (R/f).is_file(),f
s=(R/'compile_26981_shaders.sh').read_text()
for t in ('EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478','--auto-map-locations --auto-map-bindings','spirv-opt --target-env=opengl4.5 -O','spirv-val --target-env opengl4.5',"assert v['static_count'] == 151 and v['dynamic_count'] == 78",'bash "$TMP"'):assert t in s,t
print('PASS successful 26980 exact historical prefix and mandatory compiler/build/publish tail, additive C tests only')
