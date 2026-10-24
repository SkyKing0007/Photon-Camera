#!/usr/bin/env python3
"""26875 exact successful 26874 source authority; three-file B device correction."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path)
p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--transform',action='store_true')
a=p.parse_args();root=a.root.resolve();base=a.base.resolve();cand=a.candidate.resolve()
def manifest(n):
 out={}
 for line in (root/n).read_text().splitlines():
  h,f=line.split('  ',1); assert len(h)==64 and f.startswith('app/') and f not in out
  bytes.fromhex(h);out[f]=h
 return out
def snapshot(path):
 return {str(f.relative_to(path)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (path/'app').rglob('*') if f.is_file()}
prior=manifest('26875_BASE_26874_FULL_APP.sha256');post=manifest('26875_EXPECTED_CANDIDATE_FULL_APP.sha256')
protected=manifest('26875_UNCHANGED_PROTECTED.sha256')
old=manifest('26875_PRIOR_CHANGED_SHA256.txt');new=manifest('26875_NEW_CHANGED_SHA256.txt')
allow=(root/'26875_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==len(post)==1997 and set(prior)==set(post)
assert len(allow)==3 and allow==sorted(set(allow))
assert set(old)==set(new)==set(allow) and len(protected)==1994
assert set(protected)==set(prior)-set(allow)
assert {f for f in prior if prior[f]!=post[f]}==set(allow)
assert allow==[
 'app/src/main/cpp/iris26874_b_jpeg_writer.cpp',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/version.properties']
assert not any(x.startswith(('app/build/','app/.cxx/')) for x in allow)
assert snapshot(base)==prior,'exact successful 26874 compiled artifact mismatch'
if a.transform:
 assert base!=cand;shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
 for f in allow:
  src=root/'handoff_payload_26875'/f
  assert hashlib.sha256(src.read_bytes()).hexdigest()==new[f]
  dst=cand/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
assert snapshot(cand)==post,'26875 frozen candidate mismatch; unexpected app/src must fail'
assert all(prior[f]==post[f]==protected[f] for f in protected)
assert all(old[f]==prior[f] and new[f]==post[f] for f in allow)
v=(cand/'app/version.properties').read_text()
assert v.count('VERSION_NAME=0.9726875')==v.count('VERSION_BUILD=26875')==1
print('PASS 26875 authority seeded 1997 compiled files; exact three-file diff; 1994 protected; version')
