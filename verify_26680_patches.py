#!/usr/bin/env python3
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,tempfile
root,base,cand=[Path(x).resolve() for x in sys.argv[1:4]]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def amap(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def run(c,cwd,**kw):return subprocess.run(c,cwd=cwd,check=True,**kw)
def make(a,b):
 with tempfile.TemporaryDirectory(prefix='iris26680_patch_') as td:
  t=Path(td);run(['git','init','-q'],t);run(['git','config','user.email','iris@example.invalid'],t);run(['git','config','user.name','Iris Handoff'],t);shutil.copytree(a/'app',t/'app');run(['git','add','app'],t);env=os.environ.copy();env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'});run(['git','commit','-q','-m','base'],t,env=env);shutil.rmtree(t/'app');shutil.copytree(b/'app',t/'app');outs=[]
  for ab in ('7','12','40'):
   run(['git','config','core.abbrev',ab],t);outs.append(run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout)
  assert outs[0]==outs[1]==outs[2];return outs[0]
f=root/'R1_26680_RUNTIME_DELTA_FROM_26679.patch';r=root/'R1_26680_RUNTIME_ROLLBACK_TO_26679.patch';fw=make(base,cand);rb=make(cand,base);assert fw==f.read_bytes();assert rb==r.read_bytes();assert fw.count(b'diff --git ')==2 and rb.count(b'diff --git ')==2
for label,start,patch,target in [('forward',base,f,cand),('rollback',cand,r,base)]:
 with tempfile.TemporaryDirectory(prefix='iris26680_apply_') as td:
  t=Path(td);shutil.copytree(start/'app',t/'app');run(['git','init','-q'],t);run(['git','apply','--check',str(patch)],t);run(['git','apply',str(patch)],t);assert amap(t)==amap(target),label
print('PASS 26680 deterministic full-index patches core.abbrev=7/12/40; fuzz=0 exact forward/rollback; 2 modified / 0 added / 0 deleted')
