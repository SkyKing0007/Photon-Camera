#!/usr/bin/env python3
"""23 fail-closed missing/altered/sealed source, workflow, actual real compiler and auth regressions."""
import pathlib,shutil,subprocess,sys,tempfile
from build_26953_incremental import R,STAGE1_FILES,seal,scope
seal()
changed,added,_,_=scope()
files=set(STAGE1_FILES)|{'26953_HANDOFF_HASHES.sha256','TRIGGER_26953.txt','.github/workflows/build-26953-change-aware.yml'}
files.update('handoff_payload_26953/'+p for p in changed|added)
checks=[
 ('26953_EXPECTED_FULL_APP.sha256','append'),
 ('26953_BASE_26952_FULL_APP.sha256','append'),
 ('26953_CHANGED_RUNTIME_ALLOWLIST.txt','append'),
 ('26953_PROTECTED_SOURCE.sha256','append'),
 ('26953_NATIVE_RELEASE_ALLOWLIST.txt','append'),
 ('26953_FORWARD_FULLINDEX.patch','append'),
 ('26953_ROLLBACK_FULLINDEX.patch','append'),
 ('prepare_26953_native.py','append'),
 ('compile_26953_shaders.sh','append'),
 ('test_26953_source.py','append'),
 ('test_26953_tone_math.py','append'),
 ('test_26953_workflow_refs.py','append'),
 ('build_26953_incremental.py','append'),
 ('26953_STAGE_1_UPLOAD_PATHS.txt','append'),
 ('26953_STAGE_2_UPLOAD_PATHS.txt','append'),
 ('26953_STAGE_3_UPLOAD_PATHS.txt','append'),
 ('26952_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','append'),
 ('.github/workflows/build-26953-change-aware.yml','append'),
 ('TRIGGER_26953.txt','remove'),
]
checks += [('handoff_payload_26953/'+p,'append') for p in sorted(changed|added)]
for path,how in checks:
 with tempfile.TemporaryDirectory(prefix='26953_negative_') as td:
  root=pathlib.Path(td)
  for file in files:
   dst=root/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/file,dst)
  dst=root/path
  if how=='remove':dst.unlink()
  else:dst.write_bytes(dst.read_bytes()+b'\nHOSTILE_CORRUPTION_DO_NOT_ACCEPT\n')
  result=subprocess.run([sys.executable,'-S','build_26953_incremental.py','seal'],cwd=root,text=True,capture_output=True)
  if result.returncode==0 or '26953 BLOCKED' not in result.stderr:
   raise RuntimeError('FAIL negative file accepted '+path+' '+(result.stdout+result.stderr)[-700:])
print('PASS 26953 '+str(len(checks))+' real hostile missing/corrupt source/manifest/workflow/previous authority/patch/compiler/trigger rejects')
