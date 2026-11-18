#!/usr/bin/env python3
"""Reject hostile missing/stale/tampered stage source, patch, SHA, native, compiler and trigger."""
import pathlib,shutil,subprocess,sys,tempfile
from build_26955_incremental import R,STAGE1_FILES,seal,scope,fail

def main():
 seal()
 changed,added,_,_=scope()
 files=set(STAGE1_FILES)|{'26955_HANDOFF_HASHES.sha256','TRIGGER_26955.txt','.github/workflows/build-26955-change-aware.yml'}
 files.update('handoff_payload_26955/'+p for p in changed|added)
 checks=[('26955_EXPECTED_FULL_APP.sha256','append'),('26955_BASE_26954_FULL_APP.sha256','append'),('26955_CHANGED_RUNTIME_ALLOWLIST.txt','append'),('26955_PROTECTED_SOURCE.sha256','append'),('26955_NATIVE_RELEASE_ALLOWLIST.txt','append'),('26955_FORWARD_FULLINDEX.patch','append'),('26955_ROLLBACK_FULLINDEX.patch','append'),('prepare_26955_native.py','append'),('compile_26955_shaders.sh','append'),('test_26955_source.py','append'),('test_26955_tone_math.py','append'),('test_26955_workflow_refs.py','append'),('build_26955_incremental.py','append'),('26955_STAGE_1_UPLOAD_PATHS.txt','append'),('26955_STAGE_2_UPLOAD_PATHS.txt','append'),('26955_STAGE_3_UPLOAD_PATHS.txt','append'),('26954_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','append'),('.github/workflows/build-26955-change-aware.yml','append'),('TRIGGER_26955.txt','remove')]
 checks += [('handoff_payload_26955/'+p,'append') for p in sorted(changed|added)]
 for path,mode in checks:
  with tempfile.TemporaryDirectory(prefix='26955_hostile_') as d:
   root=pathlib.Path(d)
   for name in files:
    dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,dst)
   dst=root/path
   if mode=='remove':dst.unlink()
   else:dst.write_bytes(dst.read_bytes()+b'\nHOSTILE_TAMPERED_BYTE\n')
   q=subprocess.run([sys.executable,'-S','build_26955_incremental.py','seal'],cwd=root,capture_output=True,text=True)
   if q.returncode==0 or '26955 BLOCKED' not in q.stderr and '26955 BUILD ERROR:' not in q.stderr:fail('hostile stage mutation accepted '+path+' '+q.stdout[-300:]+q.stderr[-300:])
 print('PASS 26955 '+str(len(checks))+' hostile missing/altered workflow, original successful authority, shader, native, source, patch and trigger negatives')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26955 NEGATIVES BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
