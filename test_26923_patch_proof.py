#!/usr/bin/env python3
"""Full-index 26922 compiled -> 26923 forward/rollback, 7/12/40, mutation."""
from pathlib import Path
import subprocess,tempfile,shutil,hashlib
R=Path(__file__).resolve().parent
A=R/'.photon_26923_work/authority_26922';B=R/'.photon_26923_work/candidate_26923'
changed=set((R/'26923_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
added=set((R/'26923_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
P=R/'26923_FORWARD_FULLINDEX.patch'
assert len(changed)==7 and len(added)==1 and A.is_dir() and B.is_dir()
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='p26923_patch_') as d:
  t=Path(d)
  for name in changed:
   target=t/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/name,target)
  def apply(*args):return subprocess.run(['git','-c','core.abbrev='+str(n),'apply',*args,str(P)],cwd=t,capture_output=True,text=True)
  for args in (('--check',),(),('--reverse','--check'),('--reverse',)):
   r=apply(*args)
   assert r.returncode==0,(n,args,r.stderr)
   if args==():
    assert all(sha(t/x)==sha(B/x) for x in changed|added)
   if args==('--reverse',):
    assert all(sha(t/x)==sha(A/x) for x in changed) and all(not(t/x).exists() for x in added)
  victim=sorted(changed)[0]
  p=t/victim;s=p.read_text();needle='thread_local Iris26920Arm iris26920Arm{};'
  assert needle in s
  p.write_text(s.replace(needle,'INJECTED_MUTATED_PRIOR_SOURCE',1))
  assert apply('--check').returncode!=0
print('PASS 26923 full index forward/reverse 7/12/40, added shader revoked, changed hunk mutation rejected')
