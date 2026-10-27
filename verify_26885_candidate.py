#!/usr/bin/env python3
"""Candidate-first 26885 validator against exact successful compiled 26884 universe."""
from pathlib import Path
import sys,hashlib,shutil,argparse
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--transform',action='store_true');p.add_argument('--root',type=Path);a=p.parse_args()
R=Path(__file__).resolve().parent;ROOT=(a.root or R).resolve();B=a.base.resolve();C=a.candidate.resolve();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def get(n):return {k:h for h,k in (s.split('  ',1) for s in (R/n).read_text().splitlines())}
base=get('26885_BASE_26884_FULL_APP.sha256');cand=get('26885_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=get('26885_UNCHANGED_PROTECTED.sha256');allow=(R/'26885_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(base)==2009 and len(cand)==2010 and len(allow)==8 and len(protect)==2002
assert allow==sorted(set(allow)) and set(base).issubset(set(cand)) and set(protect)==set(base)-set(allow)
expected=set(['app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc', 'app/src/main/cpp/iris26864/Iris26864NativeBridgeShaders.cpp', 'app/src/main/cpp/iris26864/Iris26864NativeBridgeShaders.hpp', 'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake', 'app/src/main/cpp/iris26864/Iris26864Wronski2xSingleOwnerBridge.cpp', 'app/src/main/cpp/iris26864/Iris26864Wronski2xSingleOwnerBridge.hpp', 'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp', 'app/version.properties'])
assert set(allow)==expected
assert set(cand)-set(base)=={'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'}
assert not set(base)-set(cand)
assert set(protect)==set(base)-set(allow)
assert all(base[k]==cand[k]==h for k,h in protect.items())
assert all(not k.startswith('app/src/main/java/com/unspektrawesome/') and 'spektra' not in k.lower() for k in allow)
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx')}
assert universe(B)==set(base),('successful compiled authority mismatch',len(universe(B)^set(base)))
assert all((B/k).is_file() and sha(B/k)==v for k,v in base.items()),'successful 26884 source bytes drift'
if a.transform:
 payload=ROOT/'handoff_payload_26885'
 assert {'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}==set(allow)
 assert all(sha(payload/k)==cand[k] for k in allow)
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for k in allow:
  (C/k).write_bytes((payload/k).read_bytes())
assert universe(C)==set(cand),('candidate file universe drift',len(universe(C)^set(cand)))
assert all(sha(C/k)==h for k,h in cand.items())
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726885','VERSION_BUILD=26885']
assert sha(C/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')==base['app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so']
print('PASS 26885 exact 2009-file successful 26884 source, 8 scoped changes, 2002 immutable, candidate 2010, version 26885; original native unchanged')
