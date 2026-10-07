#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=3: raise SystemExit('usage: verify_26785_patches.py BASE CAND')
BASE=Path(sys.argv[1]); CAND=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
FWD=(ROOT/'26785_FORWARD_FULL_INDEX.patch').read_bytes(); RB=(ROOT/'26785_ROLLBACK_FULL_INDEX.patch').read_bytes(); allowed=(ROOT/'26785_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
def run(cwd,*args): return subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True).stdout
baseU,candU=U(BASE),U(CAND); assert len(baseU)==1779 and len(candU)==1779
assert sorted(k for k in baseU if baseU[k]!=candU[k])==allowed; assert not(set(candU)^set(baseU))
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26785_patch_{abbrev}_') as td:
  td=Path(td); run(td,'git','init','-q'); run(td,'git','config','user.email','a@b.c'); run(td,'git','config','user.name','Photon')
  shutil.copytree(BASE/'app',td/'app'); run(td,'git','add','app'); run(td,'git','commit','-q','-m','base')
  shutil.rmtree(td/'app'); shutil.copytree(CAND/'app',td/'app')
  gen=run(td,'git','-c',f'core.abbrev={abbrev}','diff','--binary','--full-index','--no-renames','HEAD','--','app')
  rev=run(td,'git','-c',f'core.abbrev={abbrev}','diff','--binary','--full-index','--no-renames','-R','HEAD','--','app')
  assert gen==FWD,f'forward patch bytes differ core.abbrev={abbrev}'; assert rev==RB,f'rollback patch bytes differ core.abbrev={abbrev}'
  run(td,'git','reset','--hard','-q','HEAD')
  run(td,'git','apply','--check',str(ROOT/'26785_FORWARD_FULL_INDEX.patch')); run(td,'git','apply',str(ROOT/'26785_FORWARD_FULL_INDEX.patch')); assert U(td)==candU
  run(td,'git','apply','--check',str(ROOT/'26785_ROLLBACK_FULL_INDEX.patch')); run(td,'git','apply',str(ROOT/'26785_ROLLBACK_FULL_INDEX.patch')); assert U(td)==baseU
  print(f'PASS 26785 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback; 3 modifications')
print('PASS 26785 canonical patch proof')
