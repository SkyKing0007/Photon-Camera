#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26682_patches.py ROOT BASE CAND')
root,base,cand=map(Path,sys.argv[1:])
fwd=(root/'R1_26682_RUNTIME_DELTA_FROM_26681_R1.patch').read_bytes(); rb=(root/'R1_26682_RUNTIME_ROLLBACK_TO_26681_R1.patch').read_bytes()
def run(cmd,cwd):return subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
def snap(r):
 out={}
 for p in sorted((Path(r)/'app').rglob('*')):
  if p.is_file():out[str(p.relative_to(r))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return out
with tempfile.TemporaryDirectory() as td:
 t=Path(td); shutil.copytree(base/'app',t/'app'); run(['git','init','-q'],t); run(['git','config','user.email','a@b.c'],t); run(['git','config','user.name','x'],t); run(['git','add','app'],t); run(['git','commit','-qm','base'],t); bc=run(['git','rev-parse','HEAD'],t).decode().strip()
 for rel in (root/'R1_26682_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines(): shutil.copy2(cand/rel,t/rel)
 run(['git','add','app'],t); run(['git','commit','-qm','cand'],t); cc=run(['git','rev-parse','HEAD'],t).decode().strip()
 for ab in ('7','12','40'):
  a=run(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',bc,cc,'--','app'],t)
  b=run(['git','-c',f'core.abbrev={ab}','diff','--binary','--full-index','--no-ext-diff',cc,bc,'--','app'],t)
  if a!=fwd or b!=rb: raise SystemExit(f'FAIL deterministic patch core.abbrev={ab}')
 # fuzz=0/exact forward then rollback from working base
 run(['git','checkout','-q',bc],t); (t/'f.patch').write_bytes(fwd); run(['git','apply','--check','f.patch'],t); run(['git','apply','f.patch'],t)
 if snap(t)!=snap(cand): raise SystemExit('FAIL forward exact candidate')
 (t/'r.patch').write_bytes(rb); run(['git','apply','--check','r.patch'],t); run(['git','apply','r.patch'],t)
 if snap(t)!=snap(base): raise SystemExit('FAIL rollback exact base')
print('PASS 26682 deterministic full-index forward/rollback patches at core.abbrev 7/12/40; exact forward and rollback')
