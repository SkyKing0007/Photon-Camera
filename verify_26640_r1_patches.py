#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26640_r1_patches.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
fwd=(root/'R1_26640_RUNTIME_DELTA_FROM_26639_R1.patch').read_bytes(); rev=(root/'R1_26640_RUNTIME_ROLLBACK_TO_26639_R1.patch').read_bytes()
def run(args,cwd,**kw): return subprocess.run(args,cwd=cwd,check=True,**kw)
def digest(b): return hashlib.sha256(b).hexdigest()
with tempfile.TemporaryDirectory(prefix='iris26640_patch_') as td:
 repo=Path(td)/'repo'; shutil.copytree(base,repo)
 run(['git','init','-q'],repo); run(['git','config','user.email','iris@local.invalid'],repo); run(['git','config','user.name','Iris Verify'],repo)
 run(['git','add','-A'],repo); run(['git','commit','-qm','base26639'],repo); base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
 # Overlay exactly candidate app and commit immutable candidate.
 shutil.rmtree(repo/'app'); shutil.copytree(cand/'app',repo/'app')
 run(['git','add','-A'],repo); run(['git','commit','-qm','candidate26640'],repo); cand_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
 outs=[]; ro=[]
 for ab in ('7','12','40'):
  run(['git','config','core.abbrev',ab],repo)
  outs.append(subprocess.check_output(['git','diff','--binary','--full-index','--no-ext-diff',base_commit,cand_commit],cwd=repo))
  ro.append(subprocess.check_output(['git','diff','--binary','--full-index','--no-ext-diff',cand_commit,base_commit],cwd=repo))
 assert outs[0]==outs[1]==outs[2]==fwd,(list(map(digest,outs)),digest(fwd))
 assert ro[0]==ro[1]==ro[2]==rev,(list(map(digest,ro)),digest(rev))
 # Forward exact recreation then rollback exact base recreation.
 run(['git','checkout','-q',base_commit],repo); run(['git','apply','--check',str(root/'R1_26640_RUNTIME_DELTA_FROM_26639_R1.patch')],repo); run(['git','apply',str(root/'R1_26640_RUNTIME_DELTA_FROM_26639_R1.patch')],repo)
 def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'app').rglob('*')) if p.is_file()}
 assert H(repo)==H(cand)
 run(['git','reset','--hard','-q'],repo); run(['git','checkout','-q',cand_commit],repo); run(['git','apply','--check',str(root/'R1_26640_RUNTIME_ROLLBACK_TO_26639_R1.patch')],repo); run(['git','apply',str(root/'R1_26640_RUNTIME_ROLLBACK_TO_26639_R1.patch')],repo)
 assert H(repo)==H(base)
print('PASS 26640 canonical full-index binary patches: core.abbrev 7/12/40 identical; forward/rollback fuzz=0 exact')
