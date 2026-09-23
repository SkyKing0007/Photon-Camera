#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26691_patches.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
forward=pkg/'R1_26691_RUNTIME_DELTA_FROM_26690_R1.patch'; rollback=pkg/'R1_26691_RUNTIME_ROLLBACK_TO_26690_R1.patch'
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file() and '.git' not in p.parts}
def force_add_all(cwd): subprocess.run(['git','add','-f','-A','app'],cwd=cwd,check=True)
base_h=H(base); cand_h=H(cand)
with tempfile.TemporaryDirectory(prefix='iris26691_patch_') as td:
 d=Path(td); shutil.copytree(base/'app',d/'app')
 subprocess.run(['git','init','-q'],cwd=d,check=True); subprocess.run(['git','config','user.email','photon@local'],cwd=d,check=True); subprocess.run(['git','config','user.name','Photon'],cwd=d,check=True); force_add_all(d); subprocess.run(['git','commit','-q','-m','base'],cwd=d,check=True)
 shutil.rmtree(d/'app'); shutil.copytree(cand/'app',d/'app'); force_add_all(d)
 gens=[]; revs=[]
 for a in (7,12,40):
  g=subprocess.run(['git','-c','core.abbrev='+str(a),'diff','--cached','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=d,check=True,stdout=subprocess.PIPE).stdout
  r=subprocess.run(['git','-c','core.abbrev='+str(a),'diff','--cached','-R','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=d,check=True,stdout=subprocess.PIPE).stdout
  gens.append(g); revs.append(r)
 assert gens[0]==gens[1]==gens[2]==forward.read_bytes(),'forward patch nondeterministic/mismatch'
 assert revs[0]==revs[1]==revs[2]==rollback.read_bytes(),'rollback patch nondeterministic/mismatch'
 subprocess.run(['git','reset','--hard','-q','HEAD'],cwd=d,check=True)
 subprocess.run(['git','apply','--check',str(forward)],cwd=d,check=True); subprocess.run(['git','apply',str(forward)],cwd=d,check=True); assert H(d)==cand_h
 subprocess.run(['git','apply','--check',str(rollback)],cwd=d,check=True); subprocess.run(['git','apply',str(rollback)],cwd=d,check=True); assert H(d)==base_h
print('PASS 26691 full-index patch proof: core.abbrev 7/12/40 identical, fuzz=0, exact full-universe forward+rollback')
