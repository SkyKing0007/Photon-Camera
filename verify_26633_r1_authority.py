#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26633_r1_authority.py ROOT BASE CAND')
ROOT=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(name):
 out=[]
 for line in (ROOT/name).read_text().splitlines():
  if line.strip(): h,rel=line.split('  ',1); out.append((h,rel))
 return out
def verify(root,name,count):
 r=rows(name)
 if len(r)!=count: raise SystemExit(f'FAIL {name} count {len(r)} != {count}')
 for h,rel in r:
  p=root/rel
  if not p.is_file() or sha(p)!=h: raise SystemExit(f'FAIL {name}: {rel}')
 return r
base=verify(B,'R1_26633_BASE_26632_R1_FULL_APP.sha256',1713); cand=verify(C,'R1_26633_EXPECTED_CANDIDATE_FULL_APP.sha256',1713)
def files(root): return sorted(str(p.relative_to(root)) for p in (root/'app').rglob('*') if p.is_file())
if files(B)!=sorted(rel for _,rel in base): raise SystemExit('FAIL base manifest universe completeness')
if files(C)!=sorted(rel for _,rel in cand): raise SystemExit('FAIL candidate manifest universe completeness')
for n,count,root in [
('R1_26633_PROTECTED_UNCHANGED_BASE.sha256',1708,B),('R1_26633_PROTECTED_UNCHANGED_CANDIDATE.sha256',1708,C),
('R1_26633_NATIVE_PROTECTED_BASE.sha256',802,B),('R1_26633_NATIVE_PROTECTED_CANDIDATE.sha256',802,C),
('R1_26633_VENDOR_PROTECTED_BASE.sha256',778,B),('R1_26633_VENDOR_PROTECTED_CANDIDATE.sha256',778,C),
('R1_26633_DNG_BASE.sha256',7,B),('R1_26633_DNG_CANDIDATE.sha256',7,C),
('R1_26633_PREWRITE_SOURCE_HASHES.sha256',5,B),('R1_26633_EXPECTED_CHANGED_SOURCE_HASHES.sha256',5,C)]: verify(root,n,count)
for a,b in [('R1_26633_PROTECTED_UNCHANGED_BASE.sha256','R1_26633_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26633_NATIVE_PROTECTED_BASE.sha256','R1_26633_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26633_VENDOR_PROTECTED_BASE.sha256','R1_26633_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26633_DNG_BASE.sha256','R1_26633_DNG_CANDIDATE.sha256')]:
 if (ROOT/a).read_bytes()!=(ROOT/b).read_bytes(): raise SystemExit(f'FAIL invariance manifest differs {a} {b}')
changed=[x for x in (ROOT/'R1_26633_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
if len(changed)!=5: raise SystemExit('FAIL runtime allowlist count')
added=[x for x in (ROOT/'R1_26633_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
if added: raise SystemExit('FAIL added-path list must be empty')
native_paths={r for _,r in rows('R1_26633_NATIVE_PROTECTED_BASE.sha256')}
if 'app/src/main/cpp/motionv2_jpeg444_jni.cpp' in native_paths: raise SystemExit('FAIL changed JNI in protected-native universe')
print('PASS 26633 authority manifests 1713 base / 1713 candidate / 1708 protected / 802 native / 778 vendor / 7 DNG / 5 runtime delta')
