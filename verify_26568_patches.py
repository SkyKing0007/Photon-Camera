#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, shutil, subprocess, tempfile

def fail(m): raise SystemExit('FAIL: '+m)
def run(cmd,cwd=None,capture=False):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None)
    if p.returncode: fail(f'command failed {cmd}:\n{p.stdout or ""}')
    return p.stdout or ''
def hashes(root):
    root=Path(root); return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
def canonical(base,cand):
    with tempfile.TemporaryDirectory(prefix='iris26568_patchgen_') as td:
        r=Path(td); shutil.copytree(Path(base)/'app',r/'app'); run(['git','init','-q'],r); run(['git','config','user.name','Iris'],r); run(['git','config','user.email','iris@invalid'],r); run(['git','add','app'],r); run(['git','commit','-q','-m','base26567'],r); bc=run(['git','rev-parse','HEAD'],r,True).strip()
        shutil.rmtree(r/'app'); shutil.copytree(Path(cand)/'app',r/'app'); run(['git','add','-A'],r); run(['git','commit','-q','-m','candidate26568'],r); cc=run(['git','rev-parse','HEAD'],r,True).strip()
        f=[]; rb=[]
        for ab in ('7','12','40'):
            f.append(run(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',bc,cc],r,True).encode())
            rb.append(run(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',cc,bc],r,True).encode())
        if not (f[0]==f[1]==f[2]): fail('forward patch changes with core.abbrev')
        if not (rb[0]==rb[1]==rb[2]): fail('rollback patch changes with core.abbrev')
        return f[0],rb[0]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base_root');ap.add_argument('candidate_root');ap.add_argument('forward');ap.add_argument('rollback');ns=ap.parse_args()
    base=Path(ns.base_root).resolve();cand=Path(ns.candidate_root).resolve();fwd=Path(ns.forward).resolve();rb=Path(ns.rollback).resolve()
    ff,rr=canonical(base,cand)
    if ff!=fwd.read_bytes(): fail('packaged forward differs canonical 7/12/40 regeneration')
    if rr!=rb.read_bytes(): fail('packaged rollback differs canonical 7/12/40 regeneration')
    with tempfile.TemporaryDirectory(prefix='iris26568_apply_') as td:
        r=Path(td);shutil.copytree(base/'app',r/'app');run(['git','init','-q'],r);run(['git','config','user.name','Iris'],r);run(['git','config','user.email','iris@invalid'],r);run(['git','add','app'],r);run(['git','commit','-q','-m','base'],r)
        out=run(['git','apply','--check','--verbose',str(fwd)],r,True)
        if 'offset' in out.lower() or 'fuzz' in out.lower(): fail('forward used offset/fuzz')
        run(['git','apply',str(fwd)],r)
        if hashes(r/'app')!=hashes(cand/'app'): fail('forward replay not exact candidate')
        out=run(['git','apply','--check','--verbose',str(rb)],r,True)
        if 'offset' in out.lower() or 'fuzz' in out.lower(): fail('rollback used offset/fuzz')
        run(['git','apply',str(rb)],r)
        if hashes(r/'app')!=hashes(base/'app'): fail('rollback replay not exact base')
    print('PASS canonical full-index binary patches core.abbrev=7/12/40 + forward/rollback fuzz=0 exactness')
if __name__=='__main__': main()
