#!/usr/bin/env python3
"""Three exact full-index patches, forward/reverse, core.abbrev 7/12/40,
actual successful 26918 authority only, never stale repository source.
"""
from pathlib import Path
import hashlib,re,subprocess,shutil,tempfile,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
changed=(R/'26919_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
before={p:h for h,p in (line.split('  ',1) for line in (R/'26919_BASE_26918_FULL_APP.sha256').read_text().splitlines())}
after={p:h for h,p in (line.split('  ',1) for line in (R/'26919_PRECOMPILE_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
patch=R/'26919_FULL_INDEX_FORWARD.patch';s=patch.read_text()
assert len(changed)==3 and len(set(changed))==3 and s.count('diff --git ')==3 and s.count('index ')==3
assert {p for p in before if before[p]!=after[p]}==set(changed)
indices=re.findall(r'^diff --git a/([^\n]+) b/([^\n]+)\nindex ([0-9a-f]{40})\.\.([0-9a-f]{40}) 100644$',s,re.M)
assert len(indices)==3,indices
for a,b,old,new in indices:
 assert a==b and a in changed
 f=R/'handoff_payload_26919'/a
 assert hashlib.sha256(f.read_bytes()).hexdigest()==after[a]
 blob=subprocess.run(['git','hash-object',str(f)],capture_output=True,text=True,check=True).stdout.strip()
 assert blob==new,(a,blob,new)
if not LIVE:
 print('PASS 26919 SHA-bound full-index patch/overlay, real forward/rollback deferred to authority-seeded live')
 sys.exit(0)
base=R/'.photon_26919_work/authority_26918'
assert base.is_dir(),'successful 26918 compiled candidate not prepared'
for n in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26919_fuzz0_{n}_') as d:
  root=Path(d)
  for p in changed:
   f=base/p;assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==before[p]
   q=root/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,q)
  for flags in (['--check'],[],['--reverse','--check'],['--reverse']):
   result=subprocess.run(['git','-c',f'core.abbrev={n}','apply','--whitespace=error','-p1',*flags,str(patch)],cwd=root,capture_output=True,text=True)
   assert result.returncode==0,(n,flags,result.stderr)
   if flags==[]:assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==after[p] for p in changed)
   if flags==['--reverse']:assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==before[p] for p in changed)
print('PASS 26919 exact actual successful 26918 base full-index forward/reverse, fuzz=0 at 7/12/40')
