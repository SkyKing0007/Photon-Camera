#!/usr/bin/env python3
"""26873 exact 26872 compiled-source authority, six-file GPU input scope; never live repo comparisons."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--transform',action='store_true');a=p.parse_args()
root=a.root.resolve();base=a.base.resolve();cand=a.candidate.resolve()
def manifest(n):
 out={}
 for row in (root/n).read_text().splitlines():
  h,f=row.split('  ',1);assert len(h)==64 and f.startswith('app/') and f not in out;(bytes.fromhex(h));out[f]=h
 return out
def snapshot(path):return {str(x.relative_to(path)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (path/'app').rglob('*') if x.is_file()}
prior=manifest('26873_BASE_26872_FULL_APP.sha256');post=manifest('26873_EXPECTED_CANDIDATE_FULL_APP.sha256')
protected=manifest('26873_UNCHANGED_PROTECTED.sha256');old=manifest('26873_PRIOR_CHANGED_SHA256.txt');new=manifest('26873_NEW_CHANGED_SHA256.txt')
allow=(root/'26873_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==len(post)==1995 and set(prior)==set(post)
assert len(allow)==6 and allow==sorted(set(allow))
assert set(old)==set(new)==set(allow)
assert set(protected)==set(prior)-set(allow) and len(protected)==1989
assert {f for f in prior if prior[f]!=post[f]}==set(allow)
assert all(x.startswith('app/src/main/cpp/iris26864/') for x in allow[:-1]) and allow[-1]=='app/version.properties'
assert not any(x.startswith(('app/build/','app/.cxx/')) for x in allow)
assert snapshot(base)==prior,'exact successful 26872 compiled authority mismatch'
if a.transform:
 assert base!=cand;shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
 for f in allow:
  source=root/'handoff_payload_26873'/f
  assert hashlib.sha256(source.read_bytes()).hexdigest()==new[f],f
  destination=cand/f;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
assert snapshot(cand)==post,'frozen 26873 candidate mismatch'
assert all(prior[f]==post[f]==protected[f] for f in protected)
v=(cand/'app/version.properties').read_text()
assert v.count('VERSION_NAME=0.9726873')==v.count('VERSION_BUILD=26873')==1
print('PASS 26873 authority-seeded successful 26872 1995->1995 files; 6 changed; 1989 protected; version exact')
