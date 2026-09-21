#!/usr/bin/env python3
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26679_patches.py ROOT BASE CANDIDATE')
root,base,cand=[Path(x).resolve() for x in sys.argv[1:4]]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def appmap(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def run(cmd,cwd,**kw): return subprocess.run(cmd,cwd=cwd,check=True,**kw)
def make(first,second):
 with tempfile.TemporaryDirectory(prefix='iris26679_patch_') as td:
  t=Path(td);run(['git','init','-q'],t);run(['git','config','user.email','iris@example.invalid'],t);run(['git','config','user.name','Iris Handoff'],t)
  shutil.copytree(first/'app',t/'app');run(['git','add','app'],t);env=os.environ.copy();env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'});run(['git','commit','-q','-m','base'],t,env=env)
  shutil.rmtree(t/'app');shutil.copytree(second/'app',t/'app');outs=[]
  for ab in ('7','12','40'):
   run(['git','config','core.abbrev',ab],t);outs.append(run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout)
  assert outs[0]==outs[1]==outs[2],'core.abbrev changed patch bytes';return outs[0]
forward=make(base,cand);rollback=make(cand,base);f=root/'R1_26679_RUNTIME_DELTA_FROM_26678.patch';r=root/'R1_26679_RUNTIME_ROLLBACK_TO_26678.patch'
assert forward==f.read_bytes(),'forward patch not canonical';assert rollback==r.read_bytes(),'rollback patch not canonical'
assert forward.count(b'diff --git ')==5 and rollback.count(b'diff --git ')==5
assert b'new file mode ' not in forward and b'deleted file mode ' not in forward
assert b'new file mode ' not in rollback and b'deleted file mode ' not in rollback
for label,start,patch,target in [('forward',base,f,cand),('rollback',cand,r,base)]:
 with tempfile.TemporaryDirectory(prefix='iris26679_apply_') as td:
  t=Path(td);shutil.copytree(start/'app',t/'app');run(['git','init','-q'],t);run(['git','apply','--check',str(patch)],t);run(['git','apply',str(patch)],t);assert appmap(t)==appmap(target),label
print('PASS 26679 deterministic full-index patches core.abbrev=7/12/40; fuzz=0 exact forward/rollback; 5 modified / 0 added / 0 deleted')
