#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4:raise SystemExit('usage: verify_26684_patches.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:]);fwd=(root/'R1_26684_RUNTIME_DELTA_FROM_26683_R1.patch').read_bytes();rb=(root/'R1_26684_RUNTIME_ROLLBACK_TO_26683_R1.patch').read_bytes()
def run(c,w):return subprocess.run(c,cwd=w,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
def snap(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
with tempfile.TemporaryDirectory() as td:
 t=Path(td);shutil.copytree(base/'app',t/'app');run(['git','init','-q'],t);run(['git','config','user.email','a@b.c'],t);run(['git','config','user.name','x'],t);run(['git','add','app'],t);run(['git','commit','-qm','base'],t);bc=run(['git','rev-parse','HEAD'],t).decode().strip()
 for rel in (root/'R1_26684_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines():shutil.copy2(cand/rel,t/rel)
 run(['git','add','app'],t);run(['git','commit','-qm','cand'],t);cc=run(['git','rev-parse','HEAD'],t).decode().strip()
 for ab in ('7','12','40'):
  if run(['git','-c','core.abbrev='+ab,'diff','--binary','--full-index','--no-ext-diff',bc,cc,'--','app'],t)!=fwd:raise SystemExit('FAIL forward patch abbrev '+ab)
  if run(['git','-c','core.abbrev='+ab,'diff','--binary','--full-index','--no-ext-diff',cc,bc,'--','app'],t)!=rb:raise SystemExit('FAIL rollback patch abbrev '+ab)
 run(['git','checkout','-q',bc],t);(t/'f.patch').write_bytes(fwd);run(['git','apply','--check','--unidiff-zero','f.patch'],t);run(['git','apply','--unidiff-zero','f.patch'],t)
 if snap(t)!=snap(cand):raise SystemExit('FAIL exact forward')
 (t/'r.patch').write_bytes(rb);run(['git','apply','--check','--unidiff-zero','r.patch'],t);run(['git','apply','--unidiff-zero','r.patch'],t)
 if snap(t)!=snap(base):raise SystemExit('FAIL exact rollback')
print('PASS 26684 deterministic full-index forward/rollback patches at core.abbrev 7/12/40; exact forward and rollback')
