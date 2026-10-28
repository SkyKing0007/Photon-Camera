#!/usr/bin/env python3
"""26886 exact successful 26885 compiled 2010-file authority, candidate-first only."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--root',type=Path);p.add_argument('--transform',action='store_true');a=p.parse_args()
R=(a.root or Path(__file__).parent).resolve();B=a.base.resolve();C=a.candidate.resolve()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def man(name):
 out={}
 for s in (R/name).read_text().splitlines():
  h,k=s.split('  ',1);assert k not in out and len(h)==64;out[k]=h
 return out
old=man('26886_BASE_26885_FULL_APP.sha256');new=man('26886_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=man('26886_UNCHANGED_PROTECTED.sha256');allow=(R/'26886_CHANGED_ALLOWLIST.txt').read_text().splitlines()
expected={'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp','app/version.properties'}
assert len(old)==2010 and len(new)==2010 and len(protected)==2008
assert set(old)==set(new) and set(allow)==expected and allow==sorted(expected)
assert set(protected)==set(old)-expected and not set(old)-set(new)
assert set(k for k in set(old)|set(new) if old.get(k)!=new.get(k))==expected
assert all(old[k]==new[k]==h for k,h in protected.items())
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx')}
assert universe(B)==set(old),('unexpected prior successful runtime-source universe',sorted(universe(B)^set(old))[:10])
assert all((B/k).is_file() and sha(B/k)==h for k,h in old.items()),'26885 real compiled candidate hash mismatch'
if a.transform:
 payload=R/'handoff_payload_26886'
 actual={'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}
 assert actual==expected,('handoff overlay unexpected files',sorted(actual^expected))
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for k in allow:
  assert sha(payload/k)==new[k]
  (C/k).write_bytes((payload/k).read_bytes())
assert universe(C)==set(new),('unexpected new app/src files or missing source',sorted(universe(C)^set(new))[:10])
assert all((C/k).is_file() and sha(C/k)==h for k,h in new.items()),'26886 frozen candidate bytes mismatch'
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726886','VERSION_BUILD=26886']
assert sha(C/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')==old['app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so']
print('PASS 26886 successful 26885 2010-file authority, 2 exact scoped runtime changes, 2008 protected, native/vendor/Spektra/DNG invariant')
