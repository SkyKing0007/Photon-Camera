#!/usr/bin/env python3
"""26915 exact real successful predecessor source forward+rollback patch proof.
Freeze changed-file scope and enforce git --full-index --binary fuzz=0 at
core.abbrev=7/12/40. Actual 26914 V2 source required, not a fake fixture.
"""
from pathlib import Path
import tempfile,shutil,subprocess,hashlib,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
BASE=(R/'.photon_26915_work/authority_26914_v2') if LIVE and (R/'.photon_26915_work/authority_26914_v2').is_dir() else R/'authority_26914'
AFTER=(R/'.photon_26915_work/candidate_26915') if LIVE and (R/'.photon_26915_work/candidate_26915').is_dir() else R/'candidate_26915'
PATCH=R/'26915_FULL_INDEX_FORWARD.patch'
def parse(name):
 d={}
 for row in (R/name).read_text().splitlines():
  h,p=row.split('  ',1);d[p]=h
 return d
B=parse('26915_BASE_26914_V2_FULL_APP.sha256');A=parse('26915_PRECOMPILE_EXPECTED_FULL_APP.sha256')
changed=(R/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
added=(R/'26915_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
assert len(B)==2035 and len(A)==2036 and len(changed)==7 and len(added)==1
patch=PATCH.read_bytes();assert patch.count(b'diff --git ')==len(changed) and patch.count(b'index ')==len(changed)
for path in changed:
 assert (AFTER/path).is_file() and hashlib.sha256((AFTER/path).read_bytes()).hexdigest()==A[path],path
 if path not in added:assert (BASE/path).is_file() and hashlib.sha256((BASE/path).read_bytes()).hexdigest()==B[path],path
# Before upload no access to successful Actions TAR can be expected. In Actions
# this runs AFTER strict full-source SHA authority seeding, not in place of it.
def run(args,**kw):return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,**kw)
with tempfile.TemporaryDirectory(prefix='26915_fullindex_') as td:
 root=Path(td);run(['git','init','-q',str(root)])
 for p in changed:
  if p in added:continue
  f=root/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/p,f)
 run(['git','-C',str(root),'add','-A'])
 run(['git','-C',str(root),'-c','user.name=Photon','-c','user.email=photon@localhost','commit','-q','-m','26914-v2-successful-authority'])
 for p in changed:
  f=root/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(AFTER/p,f)
 run(['git','-C',str(root),'add','-A'])
 diffs=[run(['git','-C',str(root),'-c',f'core.abbrev={n}','diff','--cached','--binary','--full-index','--no-ext-diff','HEAD']).stdout for n in [7,12,40]]
 assert all(x==patch for x in diffs),'generated patch differs from exact successful source candidate'
 for n in [7,12,40]:
  run(['git','-C',str(root),'reset','-q','--hard','HEAD'])
  run(['git','-C',str(root),'clean','-q','-f','-d'])
  run(['git','-C',str(root),'-c',f'core.abbrev={n}','apply','--check','--index','--binary',str(PATCH)])
  run(['git','-C',str(root),'-c',f'core.abbrev={n}','apply','--index','--binary',str(PATCH)])
  for p in changed:
   assert (root/p).is_file() and hashlib.sha256((root/p).read_bytes()).hexdigest()==A[p],('forward',n,p)
  run(['git','-C',str(root),'-c',f'core.abbrev={n}','apply','--check','--reverse','--index','--binary',str(PATCH)])
  run(['git','-C',str(root),'-c',f'core.abbrev={n}','apply','--reverse','--index','--binary',str(PATCH)])
  for p in changed:
   if p in added:assert not (root/p).exists(),('reverse added',n,p)
   else:assert hashlib.sha256((root/p).read_bytes()).hexdigest()==B[p],('reverse',n,p)
  # Malicious partially modified baseline must fail before patch (no 3-way/fuzz).
  target=root/'app/version.properties';target.write_bytes(target.read_bytes()+b'\nCORRUPTED')
  bad=subprocess.run(['git','-C',str(root),'apply','--check','--index','--binary',str(PATCH)],capture_output=True)
  assert bad.returncode!=0,('bad baseline accepted',n)
print('PASS 26915 actual source diff and exact forward/rollback at core.abbrev=7/12/40, fuzz=0, hostile baseline rejection')
