#!/usr/bin/env python3
"""26881 exact root-only upload integrity and deletion-aware source staging.
Never write live repository app/src; guarded 17-stage transforms candidate only.
"""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def entries(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,k=line.split('  ',1);assert k not in d;d[k]=h
 return d
allowed=(R/'26881_CHANGED_ALLOWLIST.txt').read_text().splitlines()
del_paths=(R/'26881_DELETIONS.txt').read_text().splitlines()
expected=entries('26881_NEW_CHANGED_SHA256.txt')
assert len(allowed)==18 and allowed==sorted(set(allowed)) and len(del_paths)==6
assert set(expected)==set(allowed)-set(del_paths)
assert len({Path(k).name for k in expected})==len(expected),'flat runtime collision'
for path,h in expected.items():
 src=R/'handoff_payload_26881'/path
 assert src.is_file() and sha(src)==h,(path,'new runtime byte drift')
assert set('app/'+p.relative_to(R/'handoff_payload_26881/app').as_posix() for p in (R/'handoff_payload_26881/app').rglob('*') if p.is_file())==set(expected)
assert entries('26881_PAYLOAD_SHA256.txt')=={'handoff_payload_26881/'+k:h for k,h in expected.items()}
assert sha(R/'handoff_payload_26881/app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so')=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
# Previous successful 26880 17-stage packaging/root staging is reproduced by
# the unchanged stage_26880_root.py in Actions, not replaced by this validator.
assert (R/'generate_26881_build.py').is_file() and (R/'verify_26881_candidate.py').is_file()
print('PASS 26881 stage-root: 18 strict changed paths / 12 files / 6 deletions, no repo app/src writes, genuine prior 26692 Vulkan identity')
