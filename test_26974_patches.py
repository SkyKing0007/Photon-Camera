#!/usr/bin/env python3
"""Real 26974 complete SHA exact patch forward/rollback using git 7/12/40, no fuzz."""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import subprocess,tempfile,shutil,hashlib,sys
R=Path(__file__).resolve().parent
b=SourceFileLoader('build26974',str(R/'build_26974_incremental.py')).load_module()
changed,a,c=b.scope()
assert len(changed)==4 and not set(changed)-set(a)
for p in ('26974_FORWARD_FULLINDEX.patch','26974_ROLLBACK_FULLINDEX.patch'):
 t=(R/p).read_text()
 assert t.count('diff --git ')==4 and len([ln for ln in t.splitlines() if ln.startswith('index ')])==4
 assert all(len(ln.split('..')[0].split('index ')[1])==40 for ln in t.splitlines() if ln.startswith('index '))
for abbr in ('7','12','40'):
 with tempfile.TemporaryDirectory(prefix='p26974_patch_') as td:
  T=Path(td)
  for n in changed:
   dest=T/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26974'/n,dest)
  def check(manifest):
   for name in changed:
    assert hashlib.sha256((T/name).read_bytes()).hexdigest()==manifest[name],(abbr,name)
  def apply(patch):
   cmd=['git','-c','core.abbrev='+abbr,'apply','--unidiff-zero','--whitespace=error']
   for extra in ('--check',''):
    subprocess.run(cmd+([extra] if extra else [])+[str(R/patch)],cwd=T,check=True,stdout=subprocess.DEVNULL)
  check(c)
  apply('26974_ROLLBACK_FULLINDEX.patch');check(a)
  apply('26974_FORWARD_FULLINDEX.patch');check(c)
  apply('26974_ROLLBACK_FULLINDEX.patch');check(a)
  apply('26974_FORWARD_FULLINDEX.patch');check(c)
if '--frozen' in sys.argv:
 b.exact(b.BASE,'26974_BASE_26973_FULL_APP.sha256','26974 real frozen successful 26973 source SHA')
 b.exact(b.CAND,'26974_EXPECTED_FULL_APP.sha256','26974 frozen transformed candidate SHA')
if '--live' in sys.argv:
 b.exact(R,'26974_EXPECTED_FULL_APP.sha256','26974 live full 2132 app source SHA')
print('PASS 26974 full-index git forward/rollback at core.abbrev 7/12/40, zero fuzz, 4 exact original edits')
