#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,tempfile,shutil,subprocess,os
if len(sys.argv)!=4: raise SystemExit('usage: verify_26667_patches.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def appmap(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def make(first,second):
 with tempfile.TemporaryDirectory(prefix='iris26667_patch_') as td:
  t=Path(td); subprocess.run(['git','init','-q'],cwd=t,check=True); subprocess.run(['git','config','user.email','iris@example.invalid'],cwd=t,check=True); subprocess.run(['git','config','user.name','Iris Handoff'],cwd=t,check=True)
  shutil.copytree(first/'app',t/'app'); subprocess.run(['git','add','app'],cwd=t,check=True)
  env=os.environ.copy();env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'});subprocess.run(['git','commit','-q','-m','base'],cwd=t,check=True,env=env)
  shutil.rmtree(t/'app');shutil.copytree(second/'app',t/'app');out=[]
  for ab in ('7','12','40'):
   subprocess.run(['git','config','core.abbrev',ab],cwd=t,check=True);out.append(subprocess.run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],cwd=t,check=True,stdout=subprocess.PIPE).stdout)
  assert out[0]==out[1]==out[2];return out[0]
f=make(base,cand);r=make(cand,base)
assert f==(root/'R1_26667_RUNTIME_DELTA_FROM_26666.patch').read_bytes();assert r==(root/'R1_26667_RUNTIME_ROLLBACK_TO_26666.patch').read_bytes()
for label,start,patch,target in [('forward',base,root/'R1_26667_RUNTIME_DELTA_FROM_26666.patch',cand),('rollback',cand,root/'R1_26667_RUNTIME_ROLLBACK_TO_26666.patch',base)]:
 with tempfile.TemporaryDirectory(prefix='iris26667_apply_') as td:
  t=Path(td);shutil.copytree(start/'app',t/'app');subprocess.run(['git','init','-q'],cwd=t,check=True);subprocess.run(['git','apply','--check',str(patch)],cwd=t,check=True);subprocess.run(['git','apply',str(patch)],cwd=t,check=True);assert appmap(t)==appmap(target),label
print('PASS 26667 deterministic full-index patches core.abbrev=7/12/40; forward/rollback exact application (git apply exact context / no 3-way)')
