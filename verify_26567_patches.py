#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, os, shutil, subprocess, tempfile

def fail(msg): raise SystemExit('FAIL: '+msg)
def run(cmd,cwd=None,capture=False):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None)
    if p.returncode: fail(f'command failed {cmd}:\n{p.stdout or ""}')
    return p.stdout or ''
def tree_hashes(root):
    root=Path(root)
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base_root'); ap.add_argument('candidate_root'); ap.add_argument('forward'); ap.add_argument('rollback')
    ns=ap.parse_args(); base=Path(ns.base_root).resolve(); cand=Path(ns.candidate_root).resolve(); fwd=Path(ns.forward).resolve(); rb=Path(ns.rollback).resolve()
    if not (base/'app').is_dir() or not (cand/'app').is_dir(): fail('app roots missing')
    with tempfile.TemporaryDirectory(prefix='iris26567_patch_') as td:
        repo=Path(td)/'repo'; repo.mkdir(); shutil.copytree(base/'app',repo/'app')
        run(['git','init','-q'],repo); run(['git','config','user.name','Iris'],repo); run(['git','config','user.email','iris@invalid'],repo)
        run(['git','add','app'],repo); run(['git','commit','-q','-m','base26566'],repo); bc=run(['git','rev-parse','HEAD'],repo,True).strip()
        shutil.rmtree(repo/'app'); shutil.copytree(cand/'app',repo/'app'); run(['git','add','-A'],repo); run(['git','commit','-q','-m','candidate26567'],repo); cc=run(['git','rev-parse','HEAD'],repo,True).strip()
        fbytes=[]; rbytes=[]
        for ab in ('7','12','40'):
            ff=run(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',bc,cc],repo,True).encode()
            rr=run(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',cc,bc],repo,True).encode()
            fbytes.append(ff); rbytes.append(rr)
        if not (fbytes[0]==fbytes[1]==fbytes[2]): fail('forward patch changes with core.abbrev')
        if not (rbytes[0]==rbytes[1]==rbytes[2]): fail('rollback patch changes with core.abbrev')
        if fbytes[0]!=fwd.read_bytes(): fail('packaged forward patch differs from canonical regeneration')
        if rbytes[0]!=rb.read_bytes(): fail('packaged rollback patch differs from canonical regeneration')
        apply=Path(td)/'apply'; apply.mkdir(); shutil.copytree(base/'app',apply/'app')
        run(['git','init','-q'],apply); run(['git','config','user.name','Iris'],apply); run(['git','config','user.email','iris@invalid'],apply); run(['git','add','app'],apply); run(['git','commit','-q','-m','base'],apply)
        out=run(['git','apply','--check','--verbose',str(fwd)],apply,True)
        if 'offset' in out.lower() or 'fuzz' in out.lower(): fail('forward apply used offset/fuzz')
        run(['git','apply',str(fwd)],apply)
        if tree_hashes(apply/'app')!=tree_hashes(cand/'app'): fail('forward replay not exact candidate')
        out=run(['git','apply','--check','--verbose',str(rb)],apply,True)
        if 'offset' in out.lower() or 'fuzz' in out.lower(): fail('rollback apply used offset/fuzz')
        run(['git','apply',str(rb)],apply)
        if tree_hashes(apply/'app')!=tree_hashes(base/'app'): fail('rollback replay not exact base')
    print('PASS canonical full-index binary patches core.abbrev=7/12/40 + forward/rollback fuzz=0 exactness')
if __name__=='__main__': main()
