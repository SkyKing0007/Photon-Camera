#!/usr/bin/env python3
"""26874 exact 26873 successful compiled-candidate authority; B-only JPEG + SR package scope."""
from pathlib import Path
import argparse, hashlib, shutil
p=argparse.ArgumentParser()
p.add_argument('base',type=Path);p.add_argument('candidate',type=Path)
p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--transform',action='store_true')
a=p.parse_args();root=a.root.resolve();base=a.base.resolve();cand=a.candidate.resolve()
def manifest(n):
 out={}
 for line in (root/n).read_text().splitlines():
  h,f=line.split('  ',1)
  assert len(h)==64 and f.startswith('app/') and f not in out
  bytes.fromhex(h);out[f]=h
 return out
def snapshot(path):
 return {str(f.relative_to(path)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (path/'app').rglob('*') if f.is_file()}
prior=manifest('26874_BASE_26873_FULL_APP.sha256')
post=manifest('26874_EXPECTED_CANDIDATE_FULL_APP.sha256')
protected=manifest('26874_UNCHANGED_PROTECTED.sha256')
old=manifest('26874_PRIOR_CHANGED_SHA256.txt')
new=manifest('26874_NEW_CHANGED_SHA256.txt')
allow=(root/'26874_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==1995 and len(post)==1997 and set(prior).issubset(set(post))
assert len(allow)==7 and allow==sorted(set(allow))
assert set(old)==(set(allow)&set(prior)) and len(old)==5
assert set(new)==set(allow) and len(new)==7
assert set(protected)==set(prior)-set(allow) and len(protected)==1990
assert {f for f in prior.keys()|post.keys() if prior.get(f)!=post.get(f)}==set(allow)
assert allow==[
 'app/src/main/cpp/CMakeLists.txt',
 'app/src/main/cpp/iris26874_b_jpeg_writer.cpp',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26874BJpegPublisher.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
 'app/version.properties'
]
assert not any(x.startswith(('app/build/','app/.cxx/')) for x in allow)
assert snapshot(base)==prior,'successful 26873 compiled artifact authority mismatch'
if a.transform:
 assert base!=cand;shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
 for f in allow:
  src=root/'handoff_payload_26874'/f;assert hashlib.sha256(src.read_bytes()).hexdigest()==new[f]
  dest=cand/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
assert snapshot(cand)==post,'26874 frozen candidate mismatch; unexpected app/src must fail'
assert all(prior[f]==post[f]==protected[f] for f in protected)
v=(cand/'app/version.properties').read_text()
assert v.count('VERSION_NAME=0.9726874')==v.count('VERSION_BUILD=26874')==1
print('PASS 26874 authority seeded successful 26873 1995->1997 files; exact 7 allowlisted; 1990 protected; version exact')
