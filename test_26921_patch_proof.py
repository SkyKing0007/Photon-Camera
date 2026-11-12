#!/usr/bin/env python3
"""Exact two-file full-index git apply/rollback and corrupted-source fail-closed proof."""
from pathlib import Path
import subprocess,tempfile,shutil,hashlib,sys
R=Path.cwd(); old=R/'.photon_26921_work/authority_26920'; new=R/'.photon_26921_work/candidate_26921'
paths=sorted((R/'26921_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
patch=R/'26921_FORWARD_FULLINDEX.patch'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,cwd):return subprocess.run(['git',*args],cwd=cwd,capture_output=True,text=True)
assert old.is_dir() and new.is_dir() and len(paths)==2
for size in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='proof26921_') as temp:
  d=Path(temp)
  for p in paths:
   q=d/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/p,q)
  assert git('-c',f'core.abbrev={size}','apply','--check',str(patch),cwd=d).returncode==0,'forward fails '+str(size)
  assert git('-c',f'core.abbrev={size}','apply',str(patch),cwd=d).returncode==0,'forward apply fails '+str(size)
  assert all(digest(d/p)==digest(new/p) for p in paths),'forward wrong bytes'
  assert git('-c',f'core.abbrev={size}','apply','--reverse','--check',str(patch),cwd=d).returncode==0,'rollback check fails'
  assert git('-c',f'core.abbrev={size}','apply','--reverse',str(patch),cwd=d).returncode==0,'rollback apply fails'
  assert all(digest(d/p)==digest(old/p) for p in paths),'rollback wrong bytes'
  q=d/paths[0];q.write_bytes(q.read_bytes().replace(b'if (iris26920Arm.armed) {',b'if (iris26920Arm.armed) /*tampered*/ {',1))
  assert git('-c',f'core.abbrev={size}','apply','--check',str(patch),cwd=d).returncode!=0,'unexpected success on tampered source'
print('PASS 26921 full-index forward/rollback core.abbrev 7/12/40 fuzz=0, mutated input rejected')
