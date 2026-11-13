#!/usr/bin/env python3
"""Exact full-index forward/rollback, no fuzzy partial patch and absent-file rejection."""
from pathlib import Path
import sys,subprocess,re,tempfile,shutil
R=Path(__file__).resolve().parent
from build_26926_incremental import scope,parse,scan
changes,added,original,target=scope()
fwd=R/'26926_FORWARD_FULLINDEX.patch';back=R/'26926_ROLLBACK_FULLINDEX.patch'
for p,expected in ((fwd,changes|added),(back,changes|added)):
 lines=[x[len('diff --git a/'):].split(' b/',1)[0] for x in p.read_text().splitlines() if x.startswith('diff --git a/')]
 assert len(lines)==len(expected) and set(lines)==expected
 assert len(re.findall(r'(?m)^index [0-9a-f]{40}\.\.[0-9a-f]{40}',p.read_text()))==len(expected)
# Once authority is seeded, prove byte-for-byte patched source matches expected.
if '--live' in sys.argv:
 baseline=R/'.photon_26926_work/authority_26923'
 assert baseline.is_dir(),'actual downloaded 26923 compiled source absent'
 with tempfile.TemporaryDirectory(prefix='p26926_patch_') as d:
  root=Path(d);shutil.copytree(baseline/'app',root/'app')
  assert scan(root)==original
  for bits in ('7','12','40'):
   subprocess.run(['git','apply','--check','--unidiff-zero',fwd],cwd=root,check=True)
   subprocess.run(['git','-c',f'core.abbrev={bits}','apply','--no-index','--unidiff-zero',fwd],cwd=root,check=True)
   assert scan(root)==target,(bits,'forward')
   subprocess.run(['git','-c',f'core.abbrev={bits}','apply','--no-index','--unidiff-zero',back],cwd=root,check=True)
   assert scan(root)==original,(bits,'rollback')
   # Reject missing file after deliberate input mutation.
  (root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').unlink()
  neg=subprocess.run(['git','apply','--check',fwd],cwd=root,capture_output=True)
  assert neg.returncode!=0,'missing original source unexpectedly accepted'
print('PASS 26926 exact full-index source patch footprint, forward/rollback (live 7/12/40 when seeded)')
