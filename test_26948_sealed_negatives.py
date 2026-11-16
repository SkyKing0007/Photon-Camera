#!/usr/bin/env python3
"""Fail-closed 26948 sealed staging, SHA-256, illegal workflow, source/tamper and real compiler gates."""
import pathlib,shutil,tempfile,sys
import build_26948_incremental as b

def main():
 origin=b.R
 paths=[pathlib.Path(line.split('  ',1)[1]) for line in (origin/'26948_HANDOFF_HASHES.sha256').read_text().splitlines()]
 paths.append(pathlib.Path('26948_HANDOFF_HASHES.sha256'))
 cases=[('build_26948_incremental.py','delete'),('test_26948_source.py','delete'),('test_26948_v2_shader_compat.py','delete'),
 ('test_26948_sdr_hdr_math.py','delete'),('test_26948_flicker_host.py','delete'),
 ('test_26948_gpu_row.py','delete'),('test_26948_patch_proof.py','delete'),
 ('test_26948_workflow_refs.py','delete'),('compile_26948_shaders.sh','delete'),
 ('26948_FORWARD_FULLINDEX.patch','append'),('26948_ROLLBACK_FULLINDEX.patch','append'),
 ('26948_BASE_26947_FULL_APP.sha256','append'),('26948_EXPECTED_FULL_APP.sha256','append'),
 ('26948_PROTECTED_SOURCE.sha256','append'),('26948_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
 ('26948_EXPECTED_ACTION_EXECUTABLES.txt','append'),('26948_STAGE_1_UPLOAD_PATHS.txt','append'),
 ('26948_STAGE_2_UPLOAD_PATHS.txt','append'),('26948_STAGE_3_UPLOAD_PATHS.txt','append'),
 ('26948_COMMIT_MESSAGE.txt','append'),('TRIGGER_26948.txt','delete'),
 ('handoff_payload_26948/app/src/main/assets/shaders/motionv2/render.glsl','append'),
 ('handoff_payload_26948/app/src/main/assets/shaders/motionv2/gainmap.glsl','append'),
 ('handoff_payload_26948/app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag','append'),
 ('handoff_payload_26948/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','append'),
 ('handoff_payload_26948/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','append')]
 passed=0
 with tempfile.TemporaryDirectory(prefix='p26948_negative_') as td:
  d=pathlib.Path(td)
  for path in paths:
   dst=d/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin/path,dst)
  b.R=d;b.seal()
  for rel,mode in cases:
   f=d/rel;before=f.read_bytes()
   try:
    if mode=='delete':f.unlink()
    else:f.write_bytes(before+b'\nEVIL_MUTATION')
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('unsealed hostile staging mutation accepted '+rel)
   finally:f.write_bytes(before)
  workflow=d/'.github/workflows/build-26948-change-aware.yml';receipt=d/'26948_HANDOFF_HASHES.sha256'
  for needle,replacement in [('build_26947_incremental.py seal','build_26932_incremental.py seal'),('compile_26948_shaders.sh','compile_26944_shaders.sh'),('test_26948_v2_shader_compat.py --payload --on-actions','test_26948_source.py --payload'),('test_26948_flicker_host.py --live','test_26948_source.py --live'),('actions/upload-artifact@v4','actions/upload-artifact@v4\n        uses: actions/upload-artifact@v4'),('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace','echo "weak compiler bypass"')]:
   old=workflow.read_bytes();full=receipt.read_bytes()
   try:
    if needle.encode() not in old:b.fail('negative fixture needle absent '+needle)
    workflow.write_bytes(old.replace(needle.encode(),replacement.encode(),1))
    receipt.write_bytes(full.replace((b.sha(origin/'.github/workflows/build-26948-change-aware.yml')+'  .github/workflows/build-26948-change-aware.yml').encode(),(b.sha(workflow)+'  .github/workflows/build-26948-change-aware.yml').encode()))
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('re-sealed hostile workflow accepted '+needle)
   finally:workflow.write_bytes(old);receipt.write_bytes(full)
  for name in ('TAR_SHA','ART_SHA','BUILDER_SHA','WORKFLOW_SHA','PRIOR_APK_SHA'):
   original=getattr(b,name)
   try:
    setattr(b,name,original[:8]+'a'+original[8:])
    try:b.seal()
    except Exception:passed+=1
    else:b.fail('65-hex SHA accepted '+name)
   finally:setattr(b,name,original)
  if passed!=len(cases)+11:b.fail(f'wrong expected negative count {passed} vs {len(cases)+11}')
  b.seal()
 b.R=origin
 print('PASS',passed,'fail-closed tamper/stale/sealed-back workflow/real Android compiler and 26945 V1 invalid SHA regressions')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
