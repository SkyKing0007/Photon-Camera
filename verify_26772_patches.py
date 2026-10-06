#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, tempfile, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26772_patches.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
fwd=root/'26772_FORWARD_FULL_INDEX.patch'; rbk=root/'26772_ROLLBACK_FULL_INDEX.patch'
expected=[x for x in (root/'26772_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
modified=[x for x in (root/'26772_MODIFIED_PATHS.txt').read_text().splitlines() if x]
deleted=[x for x in (root/'26772_DELETED_PATHS.txt').read_text().splitlines() if x]
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
hb,hc=H(b),H(c)
assert len(hb)==1824 and len(hc)==1779,(len(hb),len(hc))
changed=sorted(k for k in set(hb)|set(hc) if hb.get(k)!=hc.get(k))
assert changed==sorted(expected),(len(changed),len(expected))
assert sorted(k for k in hb if k not in hc)==sorted(deleted)
assert sorted(k for k in hc if k not in hb)==[]
assert sorted(k for k in hb if k in hc and hb[k]!=hc[k])==sorted(modified)
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
    print(f'PASS 26772 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback incl 45 deletions')
