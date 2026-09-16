#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile,os
if len(sys.argv)!=4: raise SystemExit('usage: verify_26649_patches.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:4])
fwd=root/'R1_26649_RUNTIME_DELTA_FROM_26648_R1_2.patch'; rev=root/'R1_26649_RUNTIME_ROLLBACK_TO_26648_R1_2.patch'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def treehash(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh=treehash(base); ch=treehash(cand); assert len(bh)==len(ch)==1720
for abbrev in [7,12,40]:
 with tempfile.TemporaryDirectory(prefix=f'iris26649_patch_{abbrev}_') as td:
  td=Path(td); shutil.copytree(base/'app',td/'app')
  subprocess.run(['git','init','-q'],cwd=td,check=True); subprocess.run(['git','config','user.email','iris@local'],cwd=td,check=True); subprocess.run(['git','config','user.name','Iris'],cwd=td,check=True); subprocess.run(['git','config',f'core.abbrev',str(abbrev)],cwd=td,check=True)
  subprocess.run(['git','add','app'],cwd=td,check=True)
  env=dict(os.environ,GIT_AUTHOR_DATE='1970-01-01T00:00:00Z',GIT_COMMITTER_DATE='1970-01-01T00:00:00Z')
  subprocess.run(['git','commit','-q','-m','base'],cwd=td,env=env,check=True)
  subprocess.run(['git','apply','--check','--whitespace=nowarn',str(fwd)],cwd=td,check=True)
  subprocess.run(['git','apply','--whitespace=nowarn',str(fwd)],cwd=td,check=True)
  got={str(p.relative_to(td)):sha(p) for p in sorted((td/'app').rglob('*')) if p.is_file()}; assert got==ch,(abbrev,'forward mismatch')
  subprocess.run(['git','apply','--check','--whitespace=nowarn',str(rev)],cwd=td,check=True)
  subprocess.run(['git','apply','--whitespace=nowarn',str(rev)],cwd=td,check=True)
  got={str(p.relative_to(td)):sha(p) for p in sorted((td/'app').rglob('*')) if p.is_file()}; assert got==bh,(abbrev,'rollback mismatch')
print('PASS 26649 deterministic full-index forward/rollback patch proof core.abbrev=7/12/40 fuzz=0 exact rollback')
