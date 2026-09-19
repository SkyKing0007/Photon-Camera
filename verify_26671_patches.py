#!/usr/bin/env python3
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26671_patches.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def appmap(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def run(cmd,cwd,**kw): return subprocess.run(cmd,cwd=cwd,check=True,**kw)
def make(first,second):
 with tempfile.TemporaryDirectory(prefix='iris26671_patch_') as td:
  t=Path(td); run(['git','init','-q'],t); run(['git','config','user.email','iris@example.invalid'],t); run(['git','config','user.name','Iris Handoff'],t)
  shutil.copytree(first/'app',t/'app'); run(['git','add','app'],t); env=os.environ.copy(); env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}); run(['git','commit','-q','-m','base'],t,env=env)
  shutil.rmtree(t/'app'); shutil.copytree(second/'app',t/'app'); p=run(['git','ls-files','--others','--exclude-standard','-z','--','app'],t,stdout=subprocess.PIPE); un=[x.decode() for x in p.stdout.split(b'\0') if x]
  if un: run(['git','add','-N','--',*un],t)
  outs=[]
  for ab in ('7','12','40'): run(['git','config','core.abbrev',ab],t); outs.append(run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout)
  assert outs[0]==outs[1]==outs[2],'core.abbrev changed patch bytes'; return outs[0]
forward=make(base,cand); rollback=make(cand,base); f=root/'R1_26671_RUNTIME_DELTA_FROM_26670.patch'; r=root/'R1_26671_RUNTIME_ROLLBACK_TO_26670.patch'
assert forward==f.read_bytes(),'forward patch not canonical'; assert rollback==r.read_bytes(),'rollback patch not canonical'
for p,label in [(forward,'forward'),(rollback,'rollback')]: assert p.count(b'new file mode 100644')==0 and p.count(b'deleted file mode 100644')==0 and p.count(b'diff --git ')==5,(label,p.count(b'diff --git '))
for label,start,patch,target in [('forward',base,f,cand),('rollback',cand,r,base)]:
 with tempfile.TemporaryDirectory(prefix='iris26671_apply_') as td:
  t=Path(td); shutil.copytree(start/'app',t/'app'); run(['git','init','-q'],t); run(['git','apply','--check',str(patch)],t); run(['git','apply',str(patch)],t); assert appmap(t)==appmap(target),label
# Permanent added-file rollback completeness regression inherited unchanged.
with tempfile.TemporaryDirectory(prefix='iris26671_added_rollback_') as td:
 a=Path(td)/'a'; b=Path(td)/'b'; (a/'app').mkdir(parents=True); (b/'app').mkdir(parents=True); (a/'app/base.txt').write_text('base\n'); shutil.copytree(a/'app',b/'app',dirs_exist_ok=True); (b/'app/new.txt').write_text('new\n'); sf=make(a,b); sr=make(b,a); assert sf.count(b'new file mode 100644')==1 and sr.count(b'deleted file mode 100644')==1
print('PASS 26671 deterministic full-index patches core.abbrev=7/12/40; fuzz=0 exact forward/rollback; 5 modifications / 0 additions / 0 deletions; inherited added-file rollback regression PASS')
