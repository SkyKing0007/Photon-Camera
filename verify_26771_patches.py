#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,tempfile,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26771_patches.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
fwd=root/'26771_FORWARD_FULL_INDEX.patch'; rbk=root/'26771_ROLLBACK_FULL_INDEX.patch'
expected=[x for x in (root/'26771_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'26771_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
hb,hc=H(b),H(c)
assert len(hb)==1823 and len(hc)==1824
assert sorted(k for k in set(hb)|set(hc) if hb.get(k)!=hc.get(k))==sorted(expected)
assert sorted(k for k in hc if k not in hb)==sorted(added)
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory() as td:
        r=Path(td); shutil.copytree(b/'app',r/'app')
        subprocess.run(['git','init','-q'],cwd=r,check=True)
        subprocess.run(['git','config','user.email','a@b.c'],cwd=r,check=True)
        subprocess.run(['git','config','user.name','photon'],cwd=r,check=True)
        subprocess.run(['git','add','app'],cwd=r,check=True)
        subprocess.run(['git','commit','-qm','base'],cwd=r,check=True)
        subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=r,check=True)
        subprocess.run(['git','apply','--check','--unidiff-zero',str(fwd)],cwd=r,check=True)
        subprocess.run(['git','apply','--unidiff-zero',str(fwd)],cwd=r,check=True)
        assert H(r)==hc,f'forward mismatch {abbrev}'
        subprocess.run(['git','apply','--check','--unidiff-zero',str(rbk)],cwd=r,check=True)
        subprocess.run(['git','apply','--unidiff-zero',str(rbk)],cwd=r,check=True)
        assert H(r)==hb,f'rollback mismatch {abbrev}'
    print(f'PASS 26771 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback incl added resource')
