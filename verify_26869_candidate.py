#!/usr/bin/env python3
"""26869 authority-seeded deterministic 1992 -> 1996 file candidate proof."""
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
def snapshot(root):return {str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'app').rglob('*') if f.is_file()}
prior=manifest('26869_BASE_26868_FULL_APP.sha256');post=manifest('26869_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=manifest('26869_UNCHANGED_PROTECTED.sha256');new=manifest('26869_NEW_CHANGED_SHA256.txt');old=manifest('26869_PRIOR_CHANGED_SHA256.txt');allow=(root/'26869_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==1992 and len(post)==1996,(len(prior),len(post))
assert len(allow)==12 and allow==sorted(set(allow)),allow
assert set(new)==set(allow) and set(old)==set(prior)&set(allow)
assert set(post)-set(prior)==set(new)-set(old) and len(post.keys()-prior.keys())==4
assert set(protected)==set(prior)-set(old) and len(protected)==1984
assert set(allow)=={f for f in set(prior)|set(post) if prior.get(f)!=post.get(f)}
assert all(x.startswith('app/src/') or x=='app/version.properties' for x in allow)
assert not any(x.startswith(('app/build/','app/.cxx/')) for x in allow)
assert 'app/version.properties' in allow and 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26869Sharpest.kt' in allow
assert snapshot(base)==prior,'exact compiled authority not matching 26868 manifest'
if a.transform:
 assert base!=cand
 shutil.rmtree(cand,ignore_errors=True);shutil.copytree(base,cand)
 for f in allow:
  src=root/'handoff_payload_26869'/f;assert src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==post[f],f
  dst=cand/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
assert snapshot(cand)==post,'frozen 26869 candidate not matching compiled intended file universe'
assert all(prior[f]==post[f]==protected[f] for f in protected)
v=(cand/'app/version.properties').read_text()
assert v.count('VERSION_NAME=0.9726869')==1 and v.count('VERSION_BUILD=26869')==1
print('PASS 26869 exact 26868 successful compiled-candidate authority 1992 -> 1996, 12 changed paths, 1984 protected bytes, no unlisted runtime sources, version')
