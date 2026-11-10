#!/usr/bin/env python3
"""Deterministic exact full-index forward/rollback with fuzz=0, core.abbrev 7/12/40.
For --payload before authority fetch, index headers and overlay bytes must match SHA
sealed manifests. For --live, replay against actual recovered 26915 authority bytes.
"""
from pathlib import Path
import subprocess,tempfile,shutil,re,sys,hashlib
R=Path(__file__).resolve().parent
live='--live' in sys.argv
changed=(R/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(changed)==len(set(changed))==3
before={p:h for h,p in (l.split('  ',1) for l in (R/'26916_BASE_26915_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (l.split('  ',1) for l in (R/'26916_PRECOMPILE_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
patch=R/'26916_FULL_INDEX_FORWARD.patch'
s=patch.read_text()
assert s.count('diff --git ')==len(changed)
for path in changed:
 assert f'diff --git a/{path} b/{path}\n' in s
 assert f'index ' in s
 matches=re.findall(r'^index ([0-9a-f]{40})\.\.([0-9a-f]{40}) 100644$',s,re.M)
 assert len(matches)==3,matches
 blob=R/'handoff_payload_26916'/path
 assert hashlib.sha256(blob.read_bytes()).hexdigest()==after[path]
 cp=subprocess.run(['git','hash-object',str(blob)],capture_output=True,text=True,check=True).stdout.strip()
 assert any(cp==v for _,v in matches),'patch new blob not actual overlay '+path
if live:
 base=R/'.photon_26916_work/authority_26915'
 assert base.is_dir(),'real successful 26915 compiled authority not yet recovered'
else:
 # The standalone payload-only proof cannot infer original bytes from stale app/src.
 # It checks patch index hashes and exactly replayed transformed blob hashes.
 assert len(matches)==3
 print('PASS 26916 --payload full-index source hashes and sealed overlays (actual forward/rollback deferred to authority-seeded live stage)')
 sys.exit(0)
for n in [7,12,40]:
 with tempfile.TemporaryDirectory(prefix=f'26916_patch_{n}_') as td:
  root=Path(td)
  for p in changed:
   f=base/p;assert f.is_file()
   assert hashlib.sha256(f.read_bytes()).hexdigest()==before[p]
   target=root/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
  for args in [['--check'],[],['--reverse','--check'],['--reverse']]:
   proc=subprocess.run(['git','-c',f'core.abbrev={n}','apply','--whitespace=error','-p1',*args,str(patch)],cwd=root,capture_output=True,text=True)
   assert proc.returncode==0,(n,args,proc.stderr)
   if args==[]:
    for p in changed:assert hashlib.sha256((root/p).read_bytes()).hexdigest()==after[p],('forward',n,p)
   if args==['--reverse']:
    for p in changed:assert hashlib.sha256((root/p).read_bytes()).hexdigest()==before[p],('reverse',n,p)
print('PASS 26916 actual successful-source full-index exact forward/rollback fuzz=0 at core.abbrev=7/12/40')
