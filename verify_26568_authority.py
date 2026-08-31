#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
EXPECTED={
 'V1_26568_BASE_26567_AUDITED_RUNTIME.sha256':(931,'9686ff804df15d291fb14fb12c0a75bba43c711e08b815d03fe9ccf92d8ca4f3'),
 'V1_26568_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256':(931,'e350aa5e7ee0286f4dac87673fbb225b17caf74bdbea8ac8aa10f0afbad1771c'),
 'V1_26568_BASE_26567_FULL_APP.sha256':(1708,'a13a7ef25b83551063e003a6c8a021795f31f005910026970ea386c2fe734b9e'),
 'V1_26568_EXPECTED_CANDIDATE_FULL_APP.sha256':(1708,'ca854f08ed1e08ca0620438a09636b8ebcaac29a1d6b889851f2d4a559537d14'),
 'V1_26568_BASE_26567_NATIVE_VENDOR.sha256':(778,'7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'),
 'V1_26568_EXPECTED_NATIVE_VENDOR.sha256':(778,'7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'),
 'V1_26568_DNG_PROTECTED_BASE.sha256':(7,'de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592'),
 'V1_26568_DNG_PROTECTED_CANDIDATE.sha256':(7,'de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592'),
 'V1_26568_PROTECTED_UNCHANGED_BASE.sha256':(1702,'eb074632e4673137187745e3c71ec99f9b5c48f54555dea054293bf3226a4f36'),
 'V1_26568_PROTECTED_UNCHANGED_CANDIDATE.sha256':(1702,'eb074632e4673137187745e3c71ec99f9b5c48f54555dea054293bf3226a4f36'),
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
 if len(sys.argv)!=4: fail('usage: verify_26568_authority.py PACKAGE_DIR BASE_ROOT CANDIDATE_ROOT')
 package=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3])
 for name,(count,digest) in EXPECTED.items():
  p=package/name
  if not p.is_file(): fail('missing authority manifest '+name)
  if sha(p)!=digest: fail(f'manifest SHA mismatch {name}')
  if len(parse(p))!=count: fail(f'manifest count mismatch {name}')
 verify_tree(base,package/'V1_26568_BASE_26567_AUDITED_RUNTIME.sha256')
 verify_tree(base,package/'V1_26568_BASE_26567_FULL_APP.sha256')
 verify_tree(base,package/'V1_26568_BASE_26567_NATIVE_VENDOR.sha256')
 verify_tree(base,package/'V1_26568_DNG_PROTECTED_BASE.sha256')
 verify_tree(base,package/'V1_26568_PROTECTED_UNCHANGED_BASE.sha256')
 verify_tree(cand,package/'V1_26568_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256')
 verify_tree(cand,package/'V1_26568_EXPECTED_CANDIDATE_FULL_APP.sha256')
 verify_tree(cand,package/'V1_26568_EXPECTED_NATIVE_VENDOR.sha256')
 verify_tree(cand,package/'V1_26568_DNG_PROTECTED_CANDIDATE.sha256')
 verify_tree(cand,package/'V1_26568_PROTECTED_UNCHANGED_CANDIDATE.sha256')
 for a,b in [
  ('V1_26568_BASE_26567_NATIVE_VENDOR.sha256','V1_26568_EXPECTED_NATIVE_VENDOR.sha256'),
  ('V1_26568_DNG_PROTECTED_BASE.sha256','V1_26568_DNG_PROTECTED_CANDIDATE.sha256'),
  ('V1_26568_PROTECTED_UNCHANGED_BASE.sha256','V1_26568_PROTECTED_UNCHANGED_CANDIDATE.sha256')]:
  if (package/a).read_bytes()!=(package/b).read_bytes(): fail(f'invariance manifest mismatch {a} vs {b}')
 print('PASS authority completeness: 931 audited / 1708 full / 778 vendor / 7 DNG / 1702 protected exact bytes')
if __name__=='__main__': main()
