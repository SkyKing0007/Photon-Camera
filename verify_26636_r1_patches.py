#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,tempfile,shutil,sys
if len(sys.argv)!=5: raise SystemExit('usage: verify_26636_r1_patches.py BASE CAND FWD ROLLBACK')
base,cand,fwd,rb=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
changed=set(x for x in (pkg/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x); added=set(x for x in (pkg/'R1_26636_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(root): return {str(p.relative_to(root)):H(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=snap(base),snap(cand); assert len(bh)==1713 and len(ch)==1716; assert {p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p)}==changed; assert set(ch)-set(bh)==added
def run(cwd,*args): return subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26636_patch_{abbrev}_') as td:
  r=Path(td)/'repo'; shutil.copytree(base,r); run(r,'git','init','-q'); run(r,'git','config','user.name','Photon 26636 Patch Proof'); run(r,'git','config','user.email','photon26636@example.invalid'); run(r,'git','config','core.abbrev',str(abbrev)); run(r,'git','add','-A'); run(r,'git','commit','-q','-m','base')
  run(r,'git','apply','--check',str(fwd)); run(r,'git','apply',str(fwd)); assert snap(r)==ch,f'forward mismatch {abbrev}'
  status=run(r,'git','status','--porcelain','--untracked-files=all'); names=set(line[3:] for line in status.splitlines() if line.strip()); assert names==changed,(abbrev,names^changed)
  run(r,'git','apply','--check',str(rb)); run(r,'git','apply',str(rb)); assert snap(r)==bh,f'rollback mismatch {abbrev}'; assert not run(r,'git','status','--porcelain','--untracked-files=all').strip(),f'rollback dirty {abbrev}'
print('PASS 26636 full-index forward/rollback patch proof: core.abbrev 7/12/40, exact 18-path allowlist, exact rollback')
