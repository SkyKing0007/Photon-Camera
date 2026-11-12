#!/usr/bin/env python3
"""7-file deterministic full-index forward/rollback fuzz=0, core abbrev 7/12/40.
Use 26921 compiled authority and 26922 current candidate, no older/repo source."""
from pathlib import Path
import subprocess,tempfile,shutil,hashlib
R=Path(__file__).resolve().parent
A=R/'.photon_26922_work/authority_26921';B=R/'.photon_26922_work/candidate_26922'
paths=(R/'26922_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines();patch=R/'26922_FORWARD_FULLINDEX.patch'
assert len(paths)==7 and A.is_dir() and B.is_dir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(d,*args):return subprocess.run(['git',*args],cwd=d,capture_output=True,text=True)
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='proof26922_') as tmp:
  d=Path(tmp)
  for p in paths:
   q=d/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/p,q)
  for args in (('apply','--check'),('apply',),('apply','--reverse','--check'),('apply','--reverse')):
   x=git(d,'-c','core.abbrev='+str(n),*args,str(patch))
   assert x.returncode==0,(n,args,x.stderr)
   if args==('apply',):assert all(sha(d/p)==sha(B/p) for p in paths)
   if args==('apply','--reverse'):assert all(sha(d/p)==sha(A/p) for p in paths)
  # Corrupt a changed hunk itself: appending unrelated bytes outside the
  # hunk is not a valid negative case because git apply allows extra content.
  q=d/paths[0];raw=q.read_text()
  marker='IRIS_26906_B_VISUAL_TONE_POST_FINISH'
  assert raw.count(marker)==1
  q.write_text(raw.replace(marker,'INJECTED_TAMPER_IN_PATCH_CONTEXT',1))
  assert git(d,'-c','core.abbrev='+str(n),'apply','--check',str(patch)).returncode!=0
print('PASS 26922 seven-file full-index patch forward/rollback 7/12/40, corrupted original rejected')
