#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: repair_26693_patches.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
f=pkg/'26693_RUNTIME_DELTA_FROM_26692_R1_1.patch'; r=pkg/'26693_RUNTIME_ROLLBACK_TO_26692_R1_1.patch'
def H(x):return {str(p.relative_to(x)):hashlib.sha256(p.read_bytes()).hexdigest() for p in x.rglob('*') if p.is_file() and '.git' not in p.parts}
def add(cwd):subprocess.run(['git','add','-f','-A','app'],cwd=cwd,check=True)
with tempfile.TemporaryDirectory(prefix='iris26693_patch_') as td:
 d=Path(td); shutil.copytree(base/'app',d/'app'); subprocess.run(['git','init','-q'],cwd=d,check=True); subprocess.run(['git','config','user.email','photon@local'],cwd=d,check=True); subprocess.run(['git','config','user.name','Photon'],cwd=d,check=True); add(d); subprocess.run(['git','commit','-q','-m','base'],cwd=d,check=True)
 shutil.rmtree(d/'app'); shutil.copytree(cand/'app',d/'app'); add(d); gs=[];rs=[]
 for a in (7,12,40):
  gs.append(subprocess.run(['git','-c',f'core.abbrev={a}','diff','--cached','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=d,check=True,stdout=subprocess.PIPE).stdout)
  rs.append(subprocess.run(['git','-c',f'core.abbrev={a}','diff','--cached','-R','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=d,check=True,stdout=subprocess.PIPE).stdout)
 assert gs[0]==gs[1]==gs[2]==f.read_bytes(); assert rs[0]==rs[1]==rs[2]==r.read_bytes()
 subprocess.run(['git','reset','--hard','-q','HEAD'],cwd=d,check=True); subprocess.run(['git','apply','--check',str(f)],cwd=d,check=True); subprocess.run(['git','apply',str(f)],cwd=d,check=True); assert H(d)==H(cand)
 subprocess.run(['git','apply','--check',str(r)],cwd=d,check=True); subprocess.run(['git','apply',str(r)],cwd=d,check=True); assert H(d)==H(base)
print('PASS 26693 full-index patch proof: core.abbrev 7/12/40 identical, fuzz=0, exact forward+rollback')
