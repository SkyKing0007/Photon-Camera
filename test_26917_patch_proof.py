#!/usr/bin/env python3
"""26917 true full-index forward/rollback, core.abbrev 7/12/40, fuzz=0.
--payload verifies seven exact staged blobs; --live replays real compiled
26916 authority, NEVER stale repository app/src.
"""
from pathlib import Path
import subprocess,tempfile,shutil,re,sys,hashlib
R=Path(__file__).resolve().parent
live='--live' in sys.argv
staged=(R/'26917_STAGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
allowed=(R/'26917_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(staged)==7 and len(allowed)==8
before={p:h for h,p in (line.split('  ',1) for line in (R/'26917_BASE_26916_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (line.split('  ',1) for line in (R/'26917_PRECOMPILE_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
patch=R/'26917_FULL_INDEX_FORWARD.patch'
s=patch.read_text()
assert s.count('diff --git ')==len(staged)==s.count('index ')
assert s.count('@@ ' )>=len(staged)
assert set(staged)=={p for p in before if before[p]!=after[p]}
indices=re.findall(r'^diff --git a/([^\n]+) b/([^\n]+)\nindex ([0-9a-f]{40})\.\.([0-9a-f]{40}) 100644$',s,re.M)
assert len(indices)==7
for a,b,old,new in indices:
 assert a==b and a in staged
 overlay=R/'handoff_payload_26917'/a
 assert overlay.is_file() and hashlib.sha256(overlay.read_bytes()).hexdigest()==after[a]
 blob=subprocess.run(['git','hash-object',str(overlay)],check=True,capture_output=True,text=True).stdout.strip()
 assert blob==new,(a,'stale overlay blob SHA')
if not live:
 print('PASS 26917 seven full-index patch headers and sha-sealed overlay blobs; real forward/rollback deferred to authority-seeded live stage')
 sys.exit(0)
base=R/'.photon_26917_work/authority_26916'
assert base.is_dir(),'missing exact 26916 successful compiled source'
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26917_patch_{abbrev}_') as td:
  root=Path(td)
  for p in staged:
   f=base/p
   assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==before[p],p
   dst=root/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
  for flags in (['--check'],[],['--reverse','--check'],['--reverse']):
   result=subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--whitespace=error','-p1',*flags,str(patch)],cwd=root,capture_output=True,text=True)
   assert result.returncode==0,(abbrev,flags,result.stderr)
   if flags==[]:
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==after[p] for p in staged)
   if flags==['--reverse']:
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==before[p] for p in staged)
print('PASS 26917 actual successful 26916 candidate full-index exact forward/rollback fuzz=0 core.abbrev=7/12/40')
