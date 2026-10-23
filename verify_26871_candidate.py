#!/usr/bin/env python3
"""Authority-seeded exactly-1994 26870 -> 26871 candidate proof."""
from pathlib import Path
import argparse,hashlib,shutil
ap=argparse.ArgumentParser()
ap.add_argument('base',type=Path);ap.add_argument('candidate',type=Path)
ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--transform',action='store_true')
a=ap.parse_args();root=a.root.resolve();base=a.base.resolve();cand=a.candidate.resolve()
def man(name):
 lines=(root/name).read_text().splitlines();result={}
 for line in lines:
  h,f=line.split('  ',1);assert f.startswith('app/') and len(h)==64 and f not in result
  bytes.fromhex(h);result[f]=h
 return result
def snap(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B=man('26871_BASE_26870_FULL_APP.sha256');C=man('26871_EXPECTED_CANDIDATE_FULL_APP.sha256');P=man('26871_UNCHANGED_PROTECTED.sha256')
prior=man('26871_PRIOR_CHANGED_SHA256.txt');new=man('26871_NEW_CHANGED_SHA256.txt');allow=(root/'26871_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(B)==len(C)==1994 and len(P)==1991
assert len(allow)==3 and allow==sorted(set(allow)) and set(allow)==set(prior)==set(new)
assert set(B)==set(C) and set(P)==set(B)-set(allow)
assert all(B[k]==C[k]==P[k] for k in P)
assert set(allow)=={k for k in B if B[k]!=C[k]}
assert all(k.startswith('app/src/') or k=='app/version.properties' for k in allow)
assert not any(k.startswith(('app/build/','app/.cxx/')) for k in allow)
assert snap(base)==B,'prior successful compiled candidate does not match 26870 manifest'
if a.transform:
 assert base!=cand
 shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
 for f in allow:
  p=root/'handoff_payload_26871'/f
  assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==C[f],f
  dst=cand/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
assert snap(cand)==C,'candidate differs from sealed transformed source universe'
v=(cand/'app/version.properties').read_text()
assert v.count('VERSION_NAME=0.9726871')==1 and v.count('VERSION_BUILD=26871')==1
print('PASS 26871 exact successful 26870 1994-file compiled candidate / strict 3 changed / 1991 protected / version')
