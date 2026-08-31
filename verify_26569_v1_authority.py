#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
EXPECTED={
 'V1_26569_BASE_26568_AUDITED_RUNTIME.sha256':(931,'39853125f987417670b565dffb454e24046499aeea5149a09dc131294ddde435'),
 'V1_26569_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256':(931,'10e0d2b9d46861e69d0373c4d51a42da4043a163558e263e5146e2e64954aa61'),
 'V1_26569_BASE_26568_FULL_APP.sha256':(1708,'3bfae4fa481b21cf9528c8dd6ec894cb2b11f93d193bc05daf4b03056be151aa'),
 'V1_26569_EXPECTED_CANDIDATE_FULL_APP.sha256':(1708,'198f7750156f9decd7504acf282d395854c1908f6ac357abc35790c344b45788'),
 'V1_26569_BASE_26568_NATIVE_VENDOR.sha256':(778,'7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'),
 'V1_26569_EXPECTED_NATIVE_VENDOR.sha256':(778,'7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'),
 'V1_26569_DNG_PROTECTED_BASE.sha256':(7,'de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592'),
 'V1_26569_DNG_PROTECTED_CANDIDATE.sha256':(7,'de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592'),
 'V1_26569_PROTECTED_UNCHANGED_BASE.sha256':(1704,'8b1910f1948b09ecc50ce335f286f77765fb65b463e3df814c4be36724614a84'),
 'V1_26569_PROTECTED_UNCHANGED_CANDIDATE.sha256':(1704,'8b1910f1948b09ecc50ce335f286f77765fb65b463e3df814c4be36724614a84'),
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fail(m): raise SystemExit('FAIL: '+m)
def parse(p):
 lines=Path(p).read_text().splitlines(); out=[]; seen=set()
 for line in lines:
  if not line.strip(): continue
  try:h,r=line.split('  ',1)
  except ValueError: fail(f'malformed manifest line in {p}: {line!r}')
  if len(h)!=64 or r in seen: fail(f'invalid/duplicate manifest entry {r} in {p}')
  seen.add(r); out.append((h,r))
 return out
def verify_tree(root,manifest):
 for h,r in parse(manifest):
  p=Path(root)/r
  if not p.is_file(): fail(f'missing {r} under {root}')
  if sha(p)!=h: fail(f'byte mismatch {r} under {root}')
def main():
 if len(sys.argv)!=4: fail('usage: verify_26569_v1_authority.py PACKAGE_DIR BASE_ROOT CANDIDATE_ROOT')
 package=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3])
 for name,(count,digest) in EXPECTED.items():
  p=package/name
  if not p.is_file(): fail('missing authority manifest '+name)
  if sha(p)!=digest: fail(f'manifest SHA mismatch {name}')
  if len(parse(p))!=count: fail(f'manifest count mismatch {name}')
 verify_tree(base,package/'V1_26569_BASE_26568_AUDITED_RUNTIME.sha256')
 verify_tree(base,package/'V1_26569_BASE_26568_FULL_APP.sha256')
 verify_tree(base,package/'V1_26569_BASE_26568_NATIVE_VENDOR.sha256')
 verify_tree(base,package/'V1_26569_DNG_PROTECTED_BASE.sha256')
 verify_tree(base,package/'V1_26569_PROTECTED_UNCHANGED_BASE.sha256')
 verify_tree(cand,package/'V1_26569_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256')
 verify_tree(cand,package/'V1_26569_EXPECTED_CANDIDATE_FULL_APP.sha256')
 verify_tree(cand,package/'V1_26569_EXPECTED_NATIVE_VENDOR.sha256')
 verify_tree(cand,package/'V1_26569_DNG_PROTECTED_CANDIDATE.sha256')
 verify_tree(cand,package/'V1_26569_PROTECTED_UNCHANGED_CANDIDATE.sha256')
 for a,b in [
  ('V1_26569_BASE_26568_NATIVE_VENDOR.sha256','V1_26569_EXPECTED_NATIVE_VENDOR.sha256'),
  ('V1_26569_DNG_PROTECTED_BASE.sha256','V1_26569_DNG_PROTECTED_CANDIDATE.sha256'),
  ('V1_26569_PROTECTED_UNCHANGED_BASE.sha256','V1_26569_PROTECTED_UNCHANGED_CANDIDATE.sha256')]:
  if (package/a).read_bytes()!=(package/b).read_bytes(): fail(f'invariance manifest mismatch {a} vs {b}')
 print('PASS authority completeness: 931 audited / 1708 full / 778 vendor / 7 DNG / 1704 protected exact bytes')
if __name__=='__main__': main()
