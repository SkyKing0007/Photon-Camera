#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile

EXPECTED = [
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java',
'app/version.properties',
]
ROOT=Path(__file__).resolve().parent
FWD=ROOT/'26774_FORWARD_FULL_INDEX.patch'
REV=ROOT/'26774_ROLLBACK_FULL_INDEX.patch'

def run(cwd,*args):
    p=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:
        raise SystemExit(f"command failed {args}\nstdout={p.stdout}\nstderr={p.stderr}")
    return p.stdout

def U(r):
    r=Path(r)
    return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (r/'app').rglob('*') if p.is_file()}

def changed_from_patch(p):
    out=[]
    for line in Path(p).read_text().splitlines():
        if line.startswith('diff --git a/'):
            out.append(line.split(' b/',1)[0][len('diff --git a/'):])
    return sorted(out)

if len(sys.argv)!=3: raise SystemExit('usage: verify_26774_patches.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
base_u,cand_u=U(base),U(cand)
actual=sorted(k for k in set(base_u)|set(cand_u) if base_u.get(k)!=cand_u.get(k))
if actual!=EXPECTED: raise SystemExit(f'actual changed universe mismatch: {actual}')
for p in (FWD,REV):
    text=p.read_text()
    if any(x in text for x in ('\nrename from ','\nrename to ','\ncopy from ','\ncopy to ')):
        raise SystemExit(f'rename/copy inference forbidden: {p.name}')
if changed_from_patch(FWD)!=EXPECTED or changed_from_patch(REV)!=EXPECTED:
    raise SystemExit('patch path allowlist mismatch')

for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory(prefix=f'iris26774_{abbrev}_') as td:
        td=Path(td); repo=td/'repo'; shutil.copytree(base,repo)
        run(repo,'git','init','-q'); run(repo,'git','config','user.name','Iris'); run(repo,'git','config','user.email','iris@example.invalid')
        run(repo,'git','config','core.abbrev',str(abbrev)); run(repo,'git','add','-A'); run(repo,'git','commit','-q','-m','base')
        run(repo,'git','apply','--check','--unidiff-zero',str(FWD)); run(repo,'git','apply','--unidiff-zero',str(FWD))
        if U(repo)!=cand_u: raise SystemExit(f'forward replay mismatch core.abbrev={abbrev}')
        run(repo,'git','apply','--check','--unidiff-zero',str(REV)); run(repo,'git','apply','--unidiff-zero',str(REV))
        if U(repo)!=base_u: raise SystemExit(f'rollback replay mismatch core.abbrev={abbrev}')
        print(f'PASS 26774 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback; 2 modifications')
print('PASS 26774 canonical patch proof: exact 2-path allowlist, no rename/copy inference, byte-exact forward and rollback')
