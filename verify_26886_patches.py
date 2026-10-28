#!/usr/bin/env python3
"""Full-index deterministic 7/12/40 real source forward/rollback, zero fuzz."""
from pathlib import Path
import hashlib,subprocess,sys,tempfile,shutil
assert len(sys.argv)==3
B,C=map(Path,sys.argv[1:]);R=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
f=(R/'26886_FORWARD_FULL_INDEX.patch').read_bytes();back=(R/'26886_ROLLBACK_FULL_INDEX.patch').read_bytes()
assert f and back and b'index ' in f and b'index ' in back
allow=(R/'26886_CHANGED_ALLOWLIST.txt').read_text().splitlines()
def run(w,*args):return subprocess.run(['git',*args],cwd=w,check=True,capture_output=True,text=True).stdout
with tempfile.TemporaryDirectory(prefix='photon26886_full_index_') as temp:
 w=Path(temp);shutil.copytree(B/'app',w/'app')
 run(w,'init','-q');run(w,'config','user.email','proof@example.invalid');run(w,'config','user.name','Photon Proof');run(w,'config','core.autocrlf','false');run(w,'add','-f','--all');run(w,'commit','-qm','exact successful 26885 source')
 for n in (7,12,40):
  run(w,'reset','--hard','HEAD')
  run(w,'apply','--check','--index',str(R/'26886_FORWARD_FULL_INDEX.patch'))
  run(w,'apply','--index',str(R/'26886_FORWARD_FULL_INDEX.patch'))
  assert run(w,'diff','--cached','--name-only').splitlines()==allow
  assert all(sha(w/k)==sha(C/k) for k in allow)
  emitted=subprocess.run(['git','-c',f'core.abbrev={n}','diff','--cached','--full-index','--binary','HEAD'],cwd=w,check=True,capture_output=True).stdout
  assert emitted==f,('non-deterministic forward',n)
  emitted_back=subprocess.run(['git','-c',f'core.abbrev={n}','diff','--cached','--full-index','--binary','-R','HEAD'],cwd=w,check=True,capture_output=True).stdout
  assert emitted_back==back,('non-deterministic rollback',n)
  run(w,'apply','--check','--index',str(R/'26886_ROLLBACK_FULL_INDEX.patch'))
  run(w,'apply','--index',str(R/'26886_ROLLBACK_FULL_INDEX.patch'))
  assert not run(w,'status','--porcelain'),('rollback mismatch',n)
print('PASS 26886 real compiled-candidate source, full-index deterministic 7/12/40 forward/rollback, 0 fuzz, protected universe')
