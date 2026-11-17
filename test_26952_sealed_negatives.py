#!/usr/bin/env python3
"""Mutate every major 26952 handoff category; build seal must reject all mutation."""
import pathlib,subprocess,sys,tempfile,shutil
from build_26952_incremental import R,STAGE1_FILES,seal,scope
seal()
changed,added,_,_=scope()
files=set(STAGE1_FILES)|{'26952_HANDOFF_HASHES.sha256','TRIGGER_26952.txt','.github/workflows/build-26952-change-aware.yml'}
files.update('handoff_payload_26952/'+p for p in changed|added)
checks=[('26952_EXPECTED_FULL_APP.sha256','append'),('26952_BASE_26951_FULL_APP.sha256','append'),('26952_CHANGED_RUNTIME_ALLOWLIST.txt','append'),('26952_PROTECTED_SOURCE.sha256','append'),('26952_NATIVE_RELEASE_ALLOWLIST.txt','append'),('26952_FORWARD_FULLINDEX.patch','append'),('26952_ROLLBACK_FULLINDEX.patch','append'),('prepare_26952_native.py','append'),('compile_26952_shaders.sh','append'),('replay_26952_current_legacy_glsl.py','append'),('test_26952_chroma.py','append'),('test_26952_halo.py','append'),('test_26952_workflow_refs.py','append'),('test_26952_source.py','append'),('26952_STAGE_1_UPLOAD_PATHS.txt','append'),('.github/workflows/build-26952-change-aware.yml','append'),('TRIGGER_26952.txt','remove')]
checks += [('handoff_payload_26952/'+p,'append') for p in sorted(changed|added)]
for name,kind in checks:
 with tempfile.TemporaryDirectory(prefix='26952_seal_hostile_') as td:
  root=pathlib.Path(td)
  for f in files:
   target=root/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,target)
  target=root/name
  if kind=='remove':target.unlink()
  else:target.write_bytes(target.read_bytes()+b'\nHOSTILE_MUTATION\n')
  proc=subprocess.run([sys.executable,'-S','build_26952_incremental.py','seal'],cwd=root,text=True,capture_output=True)
  if proc.returncode==0 or '26952 BLOCKED' not in proc.stderr:raise RuntimeError('HOSTILE negative accepted '+name+' '+(proc.stdout+proc.stderr)[-500:])
print('PASS 26952 '+str(len(checks))+' hostile changed, added, removed, stale, missing and resealed file mutation rejects')
