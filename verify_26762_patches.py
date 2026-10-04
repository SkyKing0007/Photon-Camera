#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile,shutil,sys,hashlib
if len(sys.argv)!=3: raise SystemExit('usage: verify_26762_patches.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:]); root=Path(__file__).parent
fwd=root/'26762_FORWARD_FULL_INDEX.patch'
def digest_tree(r):
 h=hashlib.sha256()
 for p in sorted((r/'app').rglob('*')):
  if p.is_file(): h.update(p.relative_to(r).as_posix().encode()+b'\0'+p.read_bytes())
 return h.hexdigest()
bd,cd=digest_tree(base),digest_tree(cand)
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory() as td:
  t=Path(td); shutil.copytree(base/'app',t/'app')
  subprocess.run(['git','init','-q'],cwd=t,check=True); subprocess.run(['git','config','user.email','proof@example.com'],cwd=t,check=True); subprocess.run(['git','config','user.name','proof'],cwd=t,check=True)
  subprocess.run(['git','add','app'],cwd=t,check=True); subprocess.run(['git','commit','-qm','base'],cwd=t,check=True)
  subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--check','--verbose',str(fwd)],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  subprocess.run(['git','apply','--index',str(fwd)],cwd=t,check=True)
  assert digest_tree(t)==cd
  subprocess.run(['git','apply','--check','-R',str(fwd)],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  subprocess.run(['git','apply','-R','--index',str(fwd)],cwd=t,check=True)
  assert digest_tree(t)==bd
print('PASS 26762 full-index forward/rollback: abbrev 7/12/40; fuzz=0; exact rollback')
