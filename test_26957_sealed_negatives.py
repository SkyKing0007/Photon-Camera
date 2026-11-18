#!/usr/bin/env python3
"""Reject hostile missing/stale/tampered stage source, patch, SHA, native, compiler and trigger."""
import pathlib,shutil,subprocess,sys,tempfile
from build_26957_incremental import R,STAGE1_FILES,seal,scope,fail

def main():
 seal()
 changed,added,_,_=scope()
 files=set(STAGE1_FILES)|{'26957_HANDOFF_HASHES.sha256','TRIGGER_26957.txt','.github/workflows/build-26957-change-aware.yml'}
 files.update('handoff_payload_26957/'+p for p in changed|added)
 checks=[('26957_EXPECTED_FULL_APP.sha256','append'),('26957_BASE_26956_FULL_APP.sha256','append'),('26957_CHANGED_RUNTIME_ALLOWLIST.txt','append'),('26957_PROTECTED_SOURCE.sha256','append'),('26957_NATIVE_RELEASE_ALLOWLIST.txt','append'),('26957_FORWARD_FULLINDEX.patch','append'),('26957_ROLLBACK_FULLINDEX.patch','append'),('prepare_26957_native.py','append'),('compile_26957_shaders.sh','append'),('test_26957_source.py','append'),('test_26957_tone_math.py','append'),('test_26957_motion.py','append'),('test_26957_workflow_refs.py','append'),('build_26957_incremental.py','append'),('26957_STAGE_1_UPLOAD_PATHS.txt','append'),('26957_STAGE_2_UPLOAD_PATHS.txt','append'),('26957_STAGE_3_UPLOAD_PATHS.txt','append'),('26956_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','append'),('.github/workflows/build-26957-change-aware.yml','append'),('TRIGGER_26957.txt','remove')]
 checks += [('handoff_payload_26957/'+p,'append') for p in sorted(changed|added)]
 for path,mode in checks:
  with tempfile.TemporaryDirectory(prefix='26957_hostile_') as d:
   root=pathlib.Path(d)
   for name in files:
    dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,dst)
   dst=root/path
   if mode=='remove':dst.unlink()
   else:dst.write_bytes(dst.read_bytes()+b'\nHOSTILE_TAMPERED_BYTE\n')
   q=subprocess.run([sys.executable,'-S','build_26957_incremental.py','seal'],cwd=root,capture_output=True,text=True)
   if q.returncode==0 or '26957 BLOCKED' not in q.stderr and '26957 BUILD ERROR:' not in q.stderr:fail('hostile stage mutation accepted '+path+' '+q.stdout[-300:]+q.stderr[-300:])
 print('PASS 26957 '+str(len(checks))+' hostile missing/altered workflow, original successful authority, shader, native, source, patch and trigger negatives')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26957 NEGATIVES BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
