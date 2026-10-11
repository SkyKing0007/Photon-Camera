#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26810_patches.py BASE CAND FORWARD ROLLBACK')
BASE,CAND=map(Path,sys.argv[1:3]); F=Path(sys.argv[3]).resolve(); R=Path(sys.argv[4]).resolve()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
def run(cmd,cwd): subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
base_u,cand_u=uni(BASE),uni(CAND)
assert len(base_u)==len(cand_u)==1782 and set(base_u)==set(cand_u)
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory(prefix=f'iris26810_patch_{abbrev}_') as td:
        w=Path(td); shutil.copytree(BASE/'app',w/'app')
        run(['git','init','-q'],w); run(['git','config','user.email','photon@example.invalid'],w); run(['git','config','user.name','Photon'],w)
        run(['git','add','app'],w); run(['git','commit','-q','-m','base'],w)
        # full-index patch bytes must not depend on core.abbrev and apply exactly.
        run(['git','config','core.abbrev',str(abbrev)],w)
        run(['git','apply','--check',str(F)],w); run(['git','apply',str(F)],w)
        assert uni(w)==cand_u,f'forward mismatch core.abbrev={abbrev}'
        run(['git','apply','--check',str(R)],w); run(['git','apply',str(R)],w)
        assert uni(w)==base_u,f'rollback mismatch core.abbrev={abbrev}'
        print(f'PASS 26810 patch replay core.abbrev={abbrev} forward=candidate rollback=authority fuzz=0')
print('PASS 26810 canonical patch proof: deterministic full-index forward/rollback at 7/12/40')
