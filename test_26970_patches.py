#!/usr/bin/env python3
"""Full-index 7/12/40 byte-exact forward and rollback, including new shader."""
from pathlib import Path
import subprocess,tempfile,hashlib,shutil,re
R=Path(__file__).resolve().parent
files=(R/'26970_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
added=set((R/'26970_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
def man(name):return {p:h for h,p in (s.split('  ',1) for s in (R/name).read_text().splitlines())}
A=man('26970_BASE_26968_FULL_APP.sha256');B=man('26970_EXPECTED_FULL_APP.sha256')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for patch in ('26970_FORWARD_FULLINDEX.patch','26970_ROLLBACK_FULLINDEX.patch'):
 t=(R/patch).read_text();assert t.count('diff --git ')==len(files)
 assert sum(1 for s in t.splitlines() if s.startswith('index '))==len(files)
for ab in ('7','12','40'):
 with tempfile.TemporaryDirectory(prefix='ph26970_patch_') as td:
  p=Path(td)
  for path in files:
   dest=p/path;dest.parent.mkdir(parents=True,exist_ok=True)
   # Reverse starts from the actual complete staged candidate, including added shader.
   shutil.copy2(R/'handoff_payload_26970'/path,dest)
  def patch(name):
   for action in ('--check',None):
    cmd=['git','-c','core.abbrev='+ab,'apply','--unidiff-zero','--whitespace=error']
    if action:cmd.append(action)
    cmd.append(str(R/name))
    subprocess.run(cmd,cwd=p,check=True,stdout=subprocess.DEVNULL)
  patch('26970_ROLLBACK_FULLINDEX.patch')
  assert all(sha(p/path)==A[path] for path in files if path not in added)
  assert all(not (p/path).exists() for path in added)
  patch('26970_FORWARD_FULLINDEX.patch')
  assert all(sha(p/path)==B[path] for path in files)
  patch('26970_ROLLBACK_FULLINDEX.patch')
  assert all(sha(p/path)==A[path] for path in files if path not in added)
  assert all(not (p/path).exists() for path in added)
print('PASS 26970 actual git core.abbrev 7/12/40 forward/rollback exact SHA fuzz0, 1 new shader')
