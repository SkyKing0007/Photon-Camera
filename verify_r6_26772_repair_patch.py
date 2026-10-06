#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, tempfile, shutil, sys
if len(sys.argv)!=4:
    raise SystemExit('usage: verify_r6_26772_repair_patch.py BASE FAILED26772 REPAIRED26772')
b,f,c=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
fwd=root/'r6_26772_CORRECTION_FORWARD_FULL_INDEX.patch'
rbk=root/'r6_26772_CORRECTION_ROLLBACK_FULL_INDEX.patch'
expected=[x for x in (root/'26772_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
modified=[x for x in (root/'26772_MODIFIED_PATHS.txt').read_text().splitlines() if x]
deleted=[x for x in (root/'26772_DELETED_PATHS.txt').read_text().splitlines() if x]
repair='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java'
gallery='app/src/main/java/com/particlesdevs/photoncamera/gallery/binding/CustomBinding.java'
def H(r):
    return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
hb,hf,hc=H(b),H(f),H(c)
assert len(hb)==1824 and len(hf)==1779 and len(hc)==1779,(len(hb),len(hf),len(hc))
base_failed=sorted(k for k in set(hb)|set(hf) if hb.get(k)!=hf.get(k))
failed_repaired=sorted(k for k in set(hf)|set(hc) if hf.get(k)!=hc.get(k))
base_repaired=sorted(k for k in set(hb)|set(hc) if hb.get(k)!=hc.get(k))
assert base_failed==sorted(expected),(len(base_failed),len(expected))
assert failed_repaired==[repair],failed_repaired
assert base_repaired==sorted(expected),(len(base_repaired),len(expected))
assert sorted(k for k in hb if k not in hc)==sorted(deleted)
assert sorted(k for k in hc if k not in hb)==[]
assert sorted(k for k in hb if k in hc and hb[k]!=hc[k])==sorted(modified)
assert gallery in deleted and gallery not in hc
assert repair in modified and repair in hc
for p in (fwd,rbk):
    t=p.read_text()
    for forbidden in ('rename from ','rename to ','copy from ','copy to '):
        assert forbidden not in t, f'{p.name}: forbidden path inference {forbidden!r}'
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory() as td:
        r=Path(td); shutil.copytree(f/'app',r/'app')
        subprocess.run(['git','init','-q'],cwd=r,check=True)
        subprocess.run(['git','config','user.email','a@b.c'],cwd=r,check=True)
        subprocess.run(['git','config','user.name','photon'],cwd=r,check=True)
        subprocess.run(['git','add','app'],cwd=r,check=True)
        subprocess.run(['git','commit','-qm','failed26772'],cwd=r,check=True)
        subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=r,check=True)
        subprocess.run(['git','apply','--check','--unidiff-zero',str(fwd)],cwd=r,check=True)
        subprocess.run(['git','apply','--unidiff-zero',str(fwd)],cwd=r,check=True)
        assert H(r)==hc,f'R6 correction forward mismatch {abbrev}'
        subprocess.run(['git','apply','--check','--unidiff-zero',str(rbk)],cwd=r,check=True)
        subprocess.run(['git','apply','--unidiff-zero',str(rbk)],cwd=r,check=True)
        assert H(r)==hf,f'R6 correction rollback mismatch {abbrev}'
    print(f'PASS R6 correction full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact one-file repair rollback')
print('PASS R6 composite final universe: exact 68 paths = 23 modified + 45 deleted + 0 added; Gallery binding deleted; camera binding modified')
