#!/usr/bin/env python3
"""Candidate-first 26884 validator against exact successful compiled 26883 universe."""
from pathlib import Path
import sys,hashlib,shutil,argparse
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--transform',action='store_true');p.add_argument('--root',type=Path);a=p.parse_args()
R=Path(__file__).resolve().parent;ROOT=(a.root or R).resolve();B=a.base.resolve();C=a.candidate.resolve();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def get(n):return {k:h for h,k in (s.split('  ',1) for s in (R/n).read_text().splitlines())}
base=get('26884_BASE_26883_FULL_APP.sha256');cand=get('26884_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=get('26884_UNCHANGED_PROTECTED.sha256');allow=(R/'26884_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(base)==len(cand)==2009 and len(allow)==3 and len(protect)==2006
assert allow==sorted(set(allow)) and set(base)==set(cand) and set(protect)==set(base)-set(allow)
assert set(allow)=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt', 'app/version.properties'}
assert all(base[k]==cand[k]==h for k,h in protect.items())
assert set(allow)=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt', 'app/version.properties'}
assert all(not q.startswith('app/src/main/java/com/unspektrawesome/') and 'spektra' not in q.lower() for q in allow)
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx')}
assert universe(B)==set(base),('successful compiled authority mismatch',len(universe(B)^set(base)))
assert all((B/k).is_file() and sha(B/k)==v for k,v in base.items()),'successful 26883 source bytes drift'
if a.transform:
 payload=ROOT/'handoff_payload_26884'
 assert {'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}==set(allow)
 assert all(sha(payload/k)==cand[k] for k in allow)
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for k in allow:
  (C/k).write_bytes((payload/k).read_bytes())
assert universe(C)==set(cand),('candidate file universe drift',len(universe(C)^set(cand)))
assert all(sha(C/k)==h for k,h in cand.items())
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726884','VERSION_BUILD=26884']
assert sha(C/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')==base['app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so']
print('PASS 26884 exact 2009-file successful 26883 source, 3 scoped changes, 2006 immutable, candidate 2009, version 26884; original native unchanged')
