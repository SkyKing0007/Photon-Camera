#!/usr/bin/env python3
"""Require exactly inherited historical preflight and all real compilation steps."""
import pathlib,re,hashlib
R=pathlib.Path(__file__).resolve().parent
old=(R/'26977_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text();new=(R/'.github/workflows/build-26978-change-aware.yml').read_text();anchor='      - name: Fetch ONLY actual successful 26976 Actions artifact 14890426950'
assert old.count(anchor)==1
prefix,tail=old.split(anchor,1)
prefix=prefix.replace(old.splitlines()[0],'name: Photon 26978 - C sRGB JPEG-R final output and shared UI lifecycle').replace('      - TRIGGER_26977.txt','      - TRIGGER_26978.txt')
assert new.startswith(prefix),'historical prefix changed'
current_anchor='      - name: Fetch ONLY actual successful 26977 Actions artifact 14894066287'
assert new.count(current_anchor)==1
want=re.sub('26976|26977',lambda m:{'26976':'26977','26977':'26978'}[m.group()],anchor+tail).replace('14890426950','14894066287').replace('2390 protected','2399 protected').replace('photon-26978-c-donor-pro-sabre','photon-26978-c-jpegr-pro-sabre')
assert current_anchor+new.split(current_anchor,1)[1]==want,'inherited compilation tail changed'
extra=new[len(prefix):new.index(current_anchor)]
for cmd in ('build_26978_incremental.py seal','test_26978_source.py --payload','test_26978_integration_host.py --root handoff_payload_26978/app','test_26978_patches.py --payload','test_26978_sealed_negatives.py','test_26978_workflow_refs.py'):assert cmd in extra,cmd
assert new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')==1
assert new.count('actions/upload-artifact@v4')==1
for cmd in ('build_26977_incremental.py seal','test_26977_sealed_negatives.py','bash compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','bash compile_26978_shaders.sh','verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight','build_26978_incremental.py finalize'):assert cmd in new,cmd
for f in (R/'26978_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines():assert (R/f).is_file(),f
s=(R/'compile_26978_shaders.sh').read_text()
for t in ('EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478','--auto-map-locations --auto-map-bindings','spirv-opt --target-env=opengl4.5 -O','spirv-val --target-env opengl4.5','assert v[\'static_count\'] == 151 and v[\'dynamic_count\'] == 78','bash "$TMP"'):assert t in s,t
print('PASS successful 26977 exact historical prefix and mandatory compiler/build/publish tail, additive C tests only')
