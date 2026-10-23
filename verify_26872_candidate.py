#!/usr/bin/env python3
"""Exact successful 26871 authority seeded 1994->1995 candidate; never live-app diff."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--transform',action='store_true');a=p.parse_args()
root=a.root.resolve();base=a.base.resolve();cand=a.candidate.resolve()
def manifest(name):
 out={}
 for ln in (root/name).read_text().splitlines():
  h,f=ln.split('  ',1);assert f.startswith('app/') and len(h)==64 and f not in out,(name,f)
  bytes.fromhex(h);out[f]=h
 return out
def snapshot(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
prior=manifest('26872_BASE_26871_FULL_APP.sha256');post=manifest('26872_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=manifest('26872_UNCHANGED_PROTECTED.sha256');new=manifest('26872_NEW_CHANGED_SHA256.txt');old=manifest('26872_PRIOR_CHANGED_SHA256.txt');allow=(root/'26872_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==1994 and len(post)==1995
assert len(allow)==5 and allow==sorted(set(allow)),allow
assert set(new)==set(allow) and set(old)==set(prior)&set(allow)
assert len(set(post)-set(prior))==1 and not set(prior)-set(post)
assert set(protected)==set(prior)-set(old) and len(protected)==1990
assert set(allow)=={f for f in set(prior)|set(post) if prior.get(f)!=post.get(f)}
assert all(x.startswith('app/src/') or x=='app/version.properties' for x in allow)
assert not any(x.startswith(('app/build/','app/.cxx/')) for x in allow)
assert 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/Iris26872PreviewStripe.java' in allow
assert snapshot(base)==prior,'exact 26871 compiled authority mismatch'
if a.transform:
 assert base!=cand
 shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
 for f in allow:
  src=root/'handoff_payload_26872'/f;assert src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==post[f]
  dst=cand/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
assert snapshot(cand)==post,'frozen 26872 candidate mismatch'
assert all(prior[f]==post[f]==protected[f] for f in protected)
v=(cand/'app/version.properties').read_text()
assert v.count('VERSION_NAME=0.9726872')==1 and v.count('VERSION_BUILD=26872')==1
print('PASS 26872 compiled 26871 source authority 1994->1995, five changes, 1990 protected, exact version')
