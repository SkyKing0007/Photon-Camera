#!/usr/bin/env python3
"""Verify all bytes and full-index forward & rollback at 7/12/40 against real 26875 authority."""
from pathlib import Path
import tempfile,subprocess,hashlib,shutil,sys
P=Path(__file__).resolve().parent
base=Path(sys.argv[1]);cand=Path(sys.argv[2])
def entries(fn):return {k:v for v,k in (x.split('  ',1) for x in (P/fn).read_text().splitlines())}
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=entries('26876_BASE_26875_FULL_APP.sha256');latest=entries('26876_EXPECTED_CANDIDATE_FULL_APP.sha256')
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='iris26876_true_real_scope_') as td:
  root=Path(td);shutil.copytree(base/'app',root/'app');subprocess.run(['git','init','-q'],cwd=root,check=True)
  for patch,expect in (('26876_FORWARD_FULL_INDEX.patch',latest),('26876_ROLLBACK_FULL_INDEX.patch',prior)):
   def run(*cmd):subprocess.run(['git','-c',f'core.abbrev={abbrev}',*cmd],cwd=root,check=True,stdout=subprocess.DEVNULL)
   p=str(P/patch);run('apply','--check','--whitespace=nowarn',p);run('apply','--whitespace=nowarn',p)
   found={'app/'+p.relative_to(root/'app').as_posix() for p in (root/'app').rglob('*') if p.is_file()}
   assert set(expect)==found,(abbrev,patch,'universe changed')
   for name,digest in expect.items():assert sh(root/name)==digest,(abbrev,patch,name)
print('PASS deterministic full-index binary forward & rollback 7/12/40; fuzz=0; exact file universe/hash')
