#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26617_patches.py BASE CAND FWD ROLLBACK')
B=Path(sys.argv[1]).resolve(); C=Path(sys.argv[2]).resolve(); F=Path(sys.argv[3]).resolve(); R=Path(sys.argv[4]).resolve()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
with tempfile.TemporaryDirectory() as td:
    repo=Path(td)/'repo'; repo.mkdir(); shutil.copytree(B/'app',repo/'app')
    subprocess.run(['git','init','-q'],cwd=repo,check=True); subprocess.run(['git','config','user.name','Photon26617'],cwd=repo,check=True); subprocess.run(['git','config','user.email','photon26617@example.invalid'],cwd=repo,check=True)
    subprocess.run(['git','add','app'],cwd=repo,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=repo,check=True); base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    shutil.rmtree(repo/'app'); shutil.copytree(C/'app',repo/'app'); subprocess.run(['git','add','-A'],cwd=repo,check=True); subprocess.run(['git','commit','-q','-m','candidate'],cwd=repo,check=True); cand=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    fs=[];rs=[]
    for ab in ['7','12','40']:
        fs.append(subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',base,cand],cwd=repo))
        rs.append(subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',cand,base],cwd=repo))
    assert fs[0]==fs[1]==fs[2]==F.read_bytes(),'forward patch nondeterministic/mismatch'
    assert rs[0]==rs[1]==rs[2]==R.read_bytes(),'rollback patch nondeterministic/mismatch'
    check=subprocess.run(['git','diff','--check',base,cand],cwd=repo,capture_output=True,text=True); assert check.returncode==0,check.stdout+check.stderr
    fw=Path(td)/'fw'; rb=Path(td)/'rb'; shutil.copytree(B,fw); shutil.copytree(C,rb)
    for root,patch,target in [(fw,F,C),(rb,R,B)]:
        subprocess.run(['git','apply','--check',str(patch)],cwd=root,check=True); subprocess.run(['git','apply',str(patch)],cwd=root,check=True); assert H(root)==H(target),patch.name
print('PASS 26617 deterministic full-index patches core.abbrev=7/12/40; exact forward/rollback; diff --check clean')
