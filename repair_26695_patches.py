#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4:raise SystemExit('usage: repair_26695_patches.py ROOT BASE CANDIDATE')
base=Path(sys.argv[2]);cand=Path(sys.argv[3]);pkg=Path(__file__).resolve().parent;f=pkg/'26695_RUNTIME_DELTA_FROM_26694.patch';r=pkg/'26695_RUNTIME_ROLLBACK_TO_26694.patch'
def H(x):return {str(p.relative_to(x)):hashlib.sha256(p.read_bytes()).hexdigest() for p in x.rglob('*') if p.is_file() and '.git' not in p.parts}
with tempfile.TemporaryDirectory(prefix='i26695_') as td:
 d=Path(td);shutil.copytree(base/'app',d/'app');subprocess.run(['git','init','-q'],cwd=d,check=True);subprocess.run(['git','config','user.email','p@l'],cwd=d);subprocess.run(['git','config','user.name','P'],cwd=d);subprocess.run(['git','add','-f','-A','app'],cwd=d,check=True);subprocess.run(['git','commit','-q','-m','b'],cwd=d,check=True);shutil.rmtree(d/'app');shutil.copytree(cand/'app',d/'app');subprocess.run(['git','add','-f','-A','app'],cwd=d,check=True);gs=[];rs=[]
 for a in (7,12,40):
  gs.append(subprocess.run(['git','-c',f'core.abbrev={a}','diff','--cached','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=d,check=True,stdout=subprocess.PIPE).stdout);rs.append(subprocess.run(['git','-c',f'core.abbrev={a}','diff','--cached','-R','--binary','--full-index','--no-ext-diff','HEAD','--','app'],cwd=d,check=True,stdout=subprocess.PIPE).stdout)
 assert gs[0]==gs[1]==gs[2]==f.read_bytes() and rs[0]==rs[1]==rs[2]==r.read_bytes();subprocess.run(['git','reset','--hard','-q','HEAD'],cwd=d,check=True);subprocess.run(['git','apply','--check',str(f)],cwd=d,check=True);subprocess.run(['git','apply',str(f)],cwd=d,check=True);assert H(d)==H(cand);subprocess.run(['git','apply','--check',str(r)],cwd=d,check=True);subprocess.run(['git','apply',str(r)],cwd=d,check=True);assert H(d)==H(base)
print('PASS 26695 full-index patch proof: core.abbrev 7/12/40 identical, fuzz=0, exact forward+rollback')
