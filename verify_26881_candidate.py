#!/usr/bin/env python3
"""26881: exact 26880 successful candidate; authority-seeded, source-deletion-aware."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--transform',action='store_true');p.add_argument('--root',type=Path);a=p.parse_args()
R=Path(__file__).resolve().parent;ROOT=(a.root or R).resolve();B=a.base.resolve();C=a.candidate.resolve()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def manifest(n):
 d={}
 for s in (R/n).read_text().splitlines():
  h,k=s.split('  ',1);assert k not in d;d[k]=h
 return d
prior=manifest('26881_BASE_26880_FULL_APP.sha256');expected=manifest('26881_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=manifest('26881_UNCHANGED_PROTECTED.sha256')
allow=(R/'26881_CHANGED_ALLOWLIST.txt').read_text().splitlines();removed=(R/'26881_DELETIONS.txt').read_text().splitlines()
assert len(prior)==2015 and len(expected)==2009 and len(protect)==1997 and len(allow)==18 and len(removed)==6
assert allow==sorted(set(allow)) and removed==sorted(set(removed))
assert set(allow)=={k for k in (set(prior)|set(expected)) if prior.get(k)!=expected.get(k)}
assert set(removed)==set(prior)-set(expected)
assert set(protect)==set(prior)-set(allow)
assert all(prior[k]==expected[k]==v for k,v in protect.items())
def universe(root):
 return {'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx') and '.git' not in f.parts}
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
assert universe(B)==set(prior),('unexpected files inside exact successful base',len(universe(B)^set(prior)))
assert all((B/k).is_file() and sha(B/k)==v for k,v in prior.items())
if a.transform:
 payload=ROOT/'handoff_payload_26881'
 assert {'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}==set(allow)-set(removed)
 assert all(sha(payload/k)==expected[k] for k in set(allow)-set(removed))
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for k in removed:(C/k).unlink()
 for k in sorted(set(allow)-set(removed)):
  dst=C/k;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(payload/k,dst)
assert universe(C)==set(expected),('unexpected runtime source file',sorted(universe(C)^set(expected))[:10])
assert all(sha(C/k)==v for k,v in expected.items())
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726881','VERSION_BUILD=26881']
assert sha(C/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
print('PASS 26881 2015 exact 26880 authority; 2009 candidate; 18 changed including 6 deletions; 1997 protected byte-identical; version 26881')
