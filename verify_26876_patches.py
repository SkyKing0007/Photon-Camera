#!/usr/bin/env python3
"""Exact full-index deterministic forward/rollback proof at three abbreviations."""
import hashlib,pathlib,shutil,subprocess,sys,tempfile
P=pathlib.Path(__file__).resolve().parent
base=pathlib.Path(sys.argv[1]);cand=pathlib.Path(sys.argv[2]);allow=(P/'26876_CHANGED_ALLOWLIST.txt').read_text().splitlines()
fwd=P/'26876_FORWARD_FULL_INDEX.patch';back=P/'26876_ROLLBACK_FULL_INDEX.patch'
assert fwd.exists() and back.exists() and len(allow)==3

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,cwd):subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.DEVNULL)
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix='iris26876patch_') as tmp:
  t=pathlib.Path(tmp);shutil.copytree(base/'app',t/'app');run(['git','init','-q'],t)
  for patch in (fwd,back):
   run(['git','-c',f'core.abbrev={abbrev}','apply','--check','--whitespace=nowarn',str(patch)],t)
   run(['git','-c',f'core.abbrev={abbrev}','apply','--whitespace=nowarn',str(patch)],t)
   for x in allow:assert sha(t/x)==sha((cand if patch==fwd else base)/x),f'abbrev={abbrev} {x}'
print('26876 FULL-INDEX FORWARD/ROLLBACK EXACT: PASS 7/12/40 fuzz=0')
