#!/usr/bin/env python3
"""26971 full-index git patch replay and SHA identity 7/12/40 (including 1 new file)."""
from pathlib import Path
import tempfile,hashlib,subprocess,shutil
R=Path(__file__).resolve().parent
def hashes(name):return {n:h for h,n in (line.split('  ',1) for line in (R/name).read_text().splitlines())}
a=hashes('26971_BASE_26970_FULL_APP.sha256');b=hashes('26971_EXPECTED_FULL_APP.sha256')
changed=(R/'26971_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines();added=set((R/'26971_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert len(changed)==3 and len(added)==1
for patch in ('26971_FORWARD_FULLINDEX.patch','26971_ROLLBACK_FULLINDEX.patch'):
 t=(R/patch).read_text();assert sum(line.startswith('diff --git ') for line in t.splitlines())==3 and sum(line.startswith('index ') for line in t.splitlines())==3
for abbrev in ('7','12','40'):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)
  for n in changed:
   dest=root/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26971'/n,dest)
  def apply(name):
   cmd=['git','-c','core.abbrev='+abbrev,'apply','--unidiff-zero']
   subprocess.run(cmd+['--check',str(R/name)],cwd=root,check=True,stdout=subprocess.DEVNULL)
   subprocess.run(cmd+[str(R/name)],cwd=root,check=True,stdout=subprocess.DEVNULL)
  def check(h):
   for n in changed:
    path=root/n
    if n not in h:assert not path.exists()
    else:assert hashlib.sha256(path.read_bytes()).hexdigest()==h[n],n
  apply('26971_ROLLBACK_FULLINDEX.patch');check(a)
  apply('26971_FORWARD_FULLINDEX.patch');check(b)
  apply('26971_ROLLBACK_FULLINDEX.patch');check(a)
print('PASS 26971 real git full-index forward+rollback SHA exact 7/12/40, new shader-free Kotlin helper added/deleted, zero fuzz')
