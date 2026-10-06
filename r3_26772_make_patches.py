#!/usr/bin/env python3
from pathlib import Path
import os, shutil, subprocess, sys, hashlib
if len(sys.argv)!=4: raise SystemExit('usage: r3_26772_make_patches.py BASE CANDIDATE OUTDIR')
base,cand,out=map(Path,sys.argv[1:]); out.mkdir(parents=True,exist_ok=True)
repo=out/'patchrepo'
if repo.exists(): shutil.rmtree(repo)
repo.mkdir()
def run(*a, cwd=repo, env=None, capture=False):
    e=os.environ.copy(); e.update(env or {})
    return subprocess.run(a,cwd=cwd,env=e,check=True,text=True,stdout=subprocess.PIPE if capture else None).stdout if capture else None
def copy_app(src):
    d=repo/'app'
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(src/'app',d)
run('git','init','-q'); run('git','config','user.name','Photon R3 Proof'); run('git','config','user.email','proof@example.invalid'); run('git','config','core.autocrlf','false'); run('git','config','core.filemode','false')
copy_app(base); run('git','add','-A'); fixed={'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}; run('git','commit','-q','-m','base26771',env=fixed)
base_commit=run('git','rev-parse','HEAD',capture=True).strip()
copy_app(cand); run('git','add','-A'); fixed2={'GIT_AUTHOR_DATE':'2000-01-01T00:00:01Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:01Z'}; run('git','commit','-q','-m','candidate26772r3',env=fixed2)
cand_commit=run('git','rev-parse','HEAD',capture=True).strip()
patches=[]
for abbrev in (7,12,40):
    run('git','config','core.abbrev',str(abbrev))
    f=run('git','diff','--binary','--full-index','--no-ext-diff',base_commit,cand_commit,'--','app',capture=True)
    r=run('git','diff','--binary','--full-index','--no-ext-diff',cand_commit,base_commit,'--','app',capture=True)
    fp=out/f'r3_26772_FORWARD_FULL_INDEX_abbrev{abbrev}.patch'; rp=out/f'r3_26772_ROLLBACK_FULL_INDEX_abbrev{abbrev}.patch'
    fp.write_text(f); rp.write_text(r); patches.append((fp,rp))
assert len({hashlib.sha256(x[0].read_bytes()).hexdigest() for x in patches})==1, 'forward patch varies with core.abbrev'
assert len({hashlib.sha256(x[1].read_bytes()).hexdigest() for x in patches})==1, 'rollback patch varies with core.abbrev'
# Exact replay from fresh base and exact rollback from candidate. git apply uses exact context; no fuzzy patch fallback.
for fp,rp in patches:
    test=out/('replay_'+fp.stem)
    if test.exists(): shutil.rmtree(test)
    test.mkdir(); shutil.copytree(base/'app',test/'app');
    subprocess.run(['git','apply','--check',str(fp)],cwd=test,check=True)
    subprocess.run(['git','apply',str(fp)],cwd=test,check=True)
    def U(root):
        return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
    assert U(test)==U(cand), f'forward replay mismatch {fp.name}'
    subprocess.run(['git','apply','--check',str(rp)],cwd=test,check=True)
    subprocess.run(['git','apply',str(rp)],cwd=test,check=True)
    assert U(test)==U(base), f'rollback replay mismatch {rp.name}'
    shutil.rmtree(test)
shutil.rmtree(repo)
print('PASS deterministic binary full-index forward/rollback patches at core.abbrev 7/12/40; exact-context replay and rollback')
