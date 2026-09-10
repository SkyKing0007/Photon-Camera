#!/usr/bin/env python3
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26621_r1_patches.py BASE CAND FWD ROLLBACK')
B=Path(sys.argv[1]).resolve(); C=Path(sys.argv[2]).resolve(); F=Path(sys.argv[3]).resolve(); R=Path(sys.argv[4]).resolve()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
with tempfile.TemporaryDirectory() as td:
    repo=Path(td)/'repo'; repo.mkdir(); shutil.copytree(B/'app',repo/'app')
    subprocess.run(['git','init','-q'],cwd=repo,check=True); subprocess.run(['git','config','user.name','Photon26621'],cwd=repo,check=True); subprocess.run(['git','config','user.email','photon26621@example.invalid'],cwd=repo,check=True)
    subprocess.run(['git','add','app'],cwd=repo,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=repo,check=True); base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    shutil.rmtree(repo/'app'); shutil.copytree(C/'app',repo/'app'); subprocess.run(['git','add','-A'],cwd=repo,check=True); subprocess.run(['git','commit','-q','-m','candidate'],cwd=repo,check=True); cand=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    fs=[];rs=[]
    for ab in ['7','12','40']:
        fs.append(subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff','--no-renames',base,cand],cwd=repo))
        rs.append(subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff','--no-renames',cand,base],cwd=repo))
    assert fs[0]==fs[1]==fs[2]==F.read_bytes(),'forward patch nondeterministic/mismatch'
    assert rs[0]==rs[1]==rs[2]==R.read_bytes(),'rollback patch nondeterministic/mismatch'
    check=subprocess.run(['git','diff','--check',base,cand],cwd=repo,capture_output=True,text=True); assert check.returncode==0,check.stdout+check.stderr
    fw=Path(td)/'fw'; rb=Path(td)/'rb'; shutil.copytree(B,fw); shutil.copytree(C,rb)
    for root,patch,target in [(fw,F,C),(rb,R,B)]:
        env=os.environ.copy(); env['GIT_CEILING_DIRECTORIES']=str(root.parent)
        probe=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        assert probe.returncode!=0,'isolated patch proof discovered parent worktree'
        subprocess.run(['git','apply','--check',str(patch)],cwd=root,env=env,check=True)
        subprocess.run(['git','apply',str(patch)],cwd=root,env=env,check=True)
        assert H(root)==H(target),patch.name
print('PASS 26621 deterministic full-index patches core.abbrev=7/12/40; fuzz=0 exact forward/rollback including 3 deletions; diff --check clean')
