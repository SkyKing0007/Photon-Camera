#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
EXPECTED={
 'V1_26567_BASE_26566_AUDITED_RUNTIME.sha256':(931,'d850f74e7ab2f08838c963bc85353ef3eba903fc5ae7130c34a3fa6a44597e26'),
 'V1_26567_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256':(931,'1b22d9090bed3ebad167f64ee0343ebcd99014d2e593c703b789314446094cc5'),
 'V1_26567_BASE_26566_FULL_APP.sha256':(1708,'2b3ebde793a48527d21d9eabbcb14f3bb40d455f06aa3579e1f4985efd4744dd'),
 'V1_26567_EXPECTED_CANDIDATE_FULL_APP.sha256':(1708,'1c1a0eefd7de5f6f2b5f5e82d1724670291eef4b41f2073eab9d03a86dfa8dff'),
 'V1_26567_BASE_26566_NATIVE_VENDOR.sha256':(778,'7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'),
 'V1_26567_EXPECTED_NATIVE_VENDOR.sha256':(778,'7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'),
 'V1_26567_DNG_PROTECTED_BASE.sha256':(7,'de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592'),
 'V1_26567_DNG_PROTECTED_CANDIDATE.sha256':(7,'de9ccc599a5a31f150ba4b3c3f91028cbb9b98a4938db8fd22eef5cb1c94f592'),
 'V1_26567_PROTECTED_UNCHANGED_BASE.sha256':(1686,'e03a9eef0ad8638bd89967cfc4ba5f902cc59eca2919b984a8cd035b6ccc6e1c'),
 'V1_26567_PROTECTED_UNCHANGED_CANDIDATE.sha256':(1686,'e03a9eef0ad8638bd89967cfc4ba5f902cc59eca2919b984a8cd035b6ccc6e1c'),
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
 if len(sys.argv)!=4: fail('usage: verify_26567_authority.py PACKAGE_DIR BASE_ROOT CANDIDATE_ROOT')
 package=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3])
 for name,(count,digest) in EXPECTED.items():
  p=package/name
  if not p.is_file(): fail('missing authority manifest '+name)
  if sha(p)!=digest: fail(f'manifest SHA mismatch {name}')
  if len(parse(p))!=count: fail(f'manifest count mismatch {name}')
 verify_tree(base,package/'V1_26567_BASE_26566_AUDITED_RUNTIME.sha256')
 verify_tree(base,package/'V1_26567_BASE_26566_FULL_APP.sha256')
 verify_tree(base,package/'V1_26567_BASE_26566_NATIVE_VENDOR.sha256')
 verify_tree(base,package/'V1_26567_DNG_PROTECTED_BASE.sha256')
 verify_tree(base,package/'V1_26567_PROTECTED_UNCHANGED_BASE.sha256')
 verify_tree(cand,package/'V1_26567_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256')
 verify_tree(cand,package/'V1_26567_EXPECTED_CANDIDATE_FULL_APP.sha256')
 verify_tree(cand,package/'V1_26567_EXPECTED_NATIVE_VENDOR.sha256')
 verify_tree(cand,package/'V1_26567_DNG_PROTECTED_CANDIDATE.sha256')
 verify_tree(cand,package/'V1_26567_PROTECTED_UNCHANGED_CANDIDATE.sha256')
 # Invariance manifests must themselves be byte identical.
 for a,b in [
  ('V1_26567_BASE_26566_NATIVE_VENDOR.sha256','V1_26567_EXPECTED_NATIVE_VENDOR.sha256'),
  ('V1_26567_DNG_PROTECTED_BASE.sha256','V1_26567_DNG_PROTECTED_CANDIDATE.sha256'),
  ('V1_26567_PROTECTED_UNCHANGED_BASE.sha256','V1_26567_PROTECTED_UNCHANGED_CANDIDATE.sha256')]:
  if (package/a).read_bytes()!=(package/b).read_bytes(): fail(f'invariance manifest mismatch {a} vs {b}')
 print('PASS authority completeness: 931 audited / 1708 full / 778 vendor / 7 DNG / 1686 protected exact bytes')
if __name__=='__main__': main()
