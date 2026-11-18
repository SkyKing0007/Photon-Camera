#!/usr/bin/env python3
"""Reject hostile missing/stale/tampered stage source, patch, SHA, native, compiler and trigger."""
import pathlib,shutil,subprocess,sys,tempfile
from build_26958_incremental import R,STAGE1_FILES,seal,scope,fail

def main():
 seal()
 changed,added,_,_=scope()
 files=set(STAGE1_FILES)|{'26958_HANDOFF_HASHES.sha256','TRIGGER_26958.txt','.github/workflows/build-26958-change-aware.yml'}
 files.update('handoff_payload_26958/'+p for p in changed|added)
 checks=[('26958_EXPECTED_FULL_APP.sha256','append'),('26958_BASE_26957_FULL_APP.sha256','append'),('26958_CHANGED_RUNTIME_ALLOWLIST.txt','append'),('26958_PROTECTED_SOURCE.sha256','append'),('26958_NATIVE_RELEASE_ALLOWLIST.txt','append'),('26958_FORWARD_FULLINDEX.patch','append'),('26958_ROLLBACK_FULLINDEX.patch','append'),('prepare_26958_native.py','append'),('compile_26958_shaders.sh','append'),('test_26958_source.py','append'),('test_26958_tone_math.py','append'),('test_26958_motion.py','append'),('test_26958_workflow_refs.py','append'),('build_26958_incremental.py','append'),('26958_STAGE_1_UPLOAD_PATHS.txt','append'),('26958_STAGE_2_UPLOAD_PATHS.txt','append'),('26958_STAGE_3_UPLOAD_PATHS.txt','append'),('26957_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','append'),('.github/workflows/build-26958-change-aware.yml','append'),('TRIGGER_26958.txt','remove')]
 checks += [('handoff_payload_26958/'+p,'append') for p in sorted(changed|added)]
 for path,mode in checks:
  with tempfile.TemporaryDirectory(prefix='26958_hostile_') as d:
   root=pathlib.Path(d)
   for name in files:
    dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,dst)
   dst=root/path
   if mode=='remove':dst.unlink()
   else:dst.write_bytes(dst.read_bytes()+b'\nHOSTILE_TAMPERED_BYTE\n')
   q=subprocess.run([sys.executable,'-S','build_26958_incremental.py','seal'],cwd=root,capture_output=True,text=True)
   if q.returncode==0 or '26958 BLOCKED' not in q.stderr and '26958 BUILD ERROR:' not in q.stderr:fail('hostile stage mutation accepted '+path+' '+q.stdout[-300:]+q.stderr[-300:])
 print('PASS 26958 '+str(len(checks))+' hostile missing/altered workflow, original successful authority, shader, native, source, patch and trigger negatives')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26958 NEGATIVES BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
