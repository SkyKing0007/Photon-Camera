#!/usr/bin/env python3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, hashlib, shutil, subprocess, tempfile

NEW='app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def tree(root):
    root=Path(root); ps=sorted(p for p in (root/'app').rglob('*') if p.is_file())
    def one(p): return p.relative_to(root).as_posix(),sha(p)
    with ThreadPoolExecutor(max_workers=32) as pool: return dict(pool.map(one,ps))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate'); ap.add_argument('package'); a=ap.parse_args()
    base=Path(a.base); cand=Path(a.candidate); pkg=Path(a.package)
    fpin=(pkg/'V1_26566_RUNTIME_DELTA_FROM_26565_V1_2.patch').read_bytes(); rpin=(pkg/'V1_26566_RUNTIME_ROLLBACK_TO_26565_V1_2.patch').read_bytes()
    bt,ct=tree(base),tree(cand)
    with tempfile.TemporaryDirectory(prefix='iris26566_patch_') as td:
        repo=Path(td)/'repo'; repo.mkdir(); shutil.copytree(base/'app',repo/'app')
        subprocess.run(['git','init','-q'],cwd=repo,check=True); subprocess.run(['git','config','user.name','Iris'],cwd=repo,check=True); subprocess.run(['git','config','user.email','iris@invalid'],cwd=repo,check=True)
        subprocess.run(['git','add','app'],cwd=repo,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=repo,check=True)
        bc=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
        shutil.rmtree(repo/'app'); shutil.copytree(cand/'app',repo/'app')
        # Intent-to-add is mandatory because 26566 introduces one runtime source file.
        subprocess.run(['git','add','-N',NEW],cwd=repo,check=True)
        fs=[]; rs=[]
        for ab in (7,12,40):
            fs.append(subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',bc,'--','app'],cwd=repo))
            rs.append(subprocess.check_output(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff','-R',bc,'--','app'],cwd=repo))
        assert fs[0]==fs[1]==fs[2]==fpin,'forward patch differs across core.abbrev or sealed patch'
        assert rs[0]==rs[1]==rs[2]==rpin,'rollback patch differs across core.abbrev or sealed patch'
        replay=Path(td)/'replay'; replay.mkdir(); shutil.copytree(base/'app',replay/'app')
        p=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(pkg/'V1_26566_RUNTIME_DELTA_FROM_26565_V1_2.patch')],cwd=replay,text=True,capture_output=True)
        assert p.returncode==0,p.stdout+p.stderr; assert tree(replay)==ct,'forward fuzz=0 did not reproduce exact candidate'
        p=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(pkg/'V1_26566_RUNTIME_ROLLBACK_TO_26565_V1_2.patch')],cwd=replay,text=True,capture_output=True)
        assert p.returncode==0,p.stdout+p.stderr; assert tree(replay)==bt,'rollback fuzz=0 did not reproduce exact base'
    print('PASS deterministic full-index patches core.abbrev=7/12/40 + new-file intent + forward/rollback fuzz=0 exact trees')
if __name__=='__main__': main()
