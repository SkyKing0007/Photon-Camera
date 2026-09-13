#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,tempfile,shutil,sys,os
if len(sys.argv)!=5: raise SystemExit('usage: verify_26634_r1_patches.py BASE CAND FWD ROLLBACK')
base,cand,fwd,rb=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
changed=set(x for x in (pkg/'R1_26634_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(root): return {str(p.relative_to(root)):H(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=snap(base),snap(cand); assert len(bh)==1713==len(ch)
assert {p for p in bh if bh[p]!=ch[p]}==changed

def run(cwd,*args):
    return subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory(prefix=f'iris26634_patch_{abbrev}_') as td:
        t=Path(td); shutil.copytree(base,t/'repo'); r=t/'repo'
        run(r,'git','init','-q'); run(r,'git','config','user.name','Photon 26634 Patch Proof'); run(r,'git','config','user.email','photon26634@example.invalid'); run(r,'git','config','core.abbrev',str(abbrev)); run(r,'git','add','-A'); run(r,'git','commit','-q','-m','base')
        run(r,'git','apply','--check',str(fwd)); run(r,'git','apply',str(fwd))
        names=set(x for x in run(r,'git','diff','--name-only','HEAD').splitlines() if x); assert names==changed,(abbrev,names^changed)
        assert snap(r)==ch, f'forward mismatch abbrev={abbrev}'
        run(r,'git','apply','--check',str(rb)); run(r,'git','apply',str(rb))
        assert snap(r)==bh, f'rollback mismatch abbrev={abbrev}'
        assert not run(r,'git','diff','--name-only','HEAD').strip(), f'rollback dirty abbrev={abbrev}'
print('PASS 26634 full-index forward/rollback patch proof: core.abbrev 7/12/40, exact 8-file allowlist, exact rollback')
