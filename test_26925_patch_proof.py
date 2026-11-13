#!/usr/bin/env python3
"""Source-independent real git full-index patch, 7/12/40, negative mutation.
Actual authority and candidate are reconstructed by run-authorized builder.
"""
from pathlib import Path
import subprocess,tempfile,shutil,hashlib,sys
R=Path(__file__).resolve().parent
A=R/'.photon_26925_work/authority_26924';B=R/'.photon_26925_work/candidate_26925'
changed=set((R/'26925_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
added=set((R/'26925_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert len(changed)==13 and len(added)==3 and A.is_dir() and B.is_dir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'p26925_patch_{n}_') as d:
  q=Path(d)
  for name in changed:
   dest=q/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/name,dest)
  def apply(patch,*args):return subprocess.run(['git','-c',f'core.abbrev={n}','apply',*args,str(R/patch)],cwd=q,capture_output=True,text=True)
  p='26925_FORWARD_FULLINDEX.patch';back='26925_ROLLBACK_FULLINDEX.patch'
  assert apply(p,'--check').returncode==0
  assert apply(p).returncode==0
  assert all(sha(q/x)==sha(B/x) for x in changed|added)
  assert apply(back,'--check').returncode==0
  assert apply(back).returncode==0
  assert all(sha(q/x)==sha(A/x) for x in changed)
  assert all(not (q/x).exists() for x in added)
  # Real negative: changed prior hunk prevents forward application.
  victim='app/version.properties';v=q/victim;s=v.read_text()
  assert 'VERSION_BUILD=26924' in s
  v.write_text(s.replace('VERSION_BUILD=26924','VERSION_BUILD=00000'))
  assert apply(p,'--check').returncode!=0
print('PASS 26925 2048->2051 full SHA-seeded patch forward+rollback 7/12/40, added shaders removed, mismatch mutation rejected')
