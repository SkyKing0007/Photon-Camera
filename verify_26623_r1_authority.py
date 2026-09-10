#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26623_r1_authority.py PACKAGE_ROOT BASE CAND')
P=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
    lines=[x for x in (P/manifest).read_text().splitlines() if x.strip()]
    for line in lines:
        sha,rel=line.split('  ',1); q=root/rel
        assert q.is_file(),rel; assert h(q)==sha,rel
    return len(lines)
assert verify(B,'R1_26623_BASE_26622_R1_FULL_APP.sha256')==1713
assert verify(C,'R1_26623_EXPECTED_CANDIDATE_FULL_APP.sha256')==1713
assert verify(B,'R1_26623_PROTECTED_UNCHANGED_BASE.sha256')==1706
assert verify(C,'R1_26623_PROTECTED_UNCHANGED_CANDIDATE.sha256')==1706
assert (P/'R1_26623_PROTECTED_UNCHANGED_BASE.sha256').read_bytes()==(P/'R1_26623_PROTECTED_UNCHANGED_CANDIDATE.sha256').read_bytes()
assert verify(B,'R1_26623_DNG_BASE.sha256')==7 and verify(C,'R1_26623_DNG_CANDIDATE.sha256')==7
assert (P/'R1_26623_DNG_BASE.sha256').read_bytes()==(P/'R1_26623_DNG_CANDIDATE.sha256').read_bytes()
for a,b,n in [
('R1_26623_NATIVE_PROTECTED_BASE.sha256','R1_26623_NATIVE_PROTECTED_CANDIDATE.sha256',802),
('R1_26623_VENDOR_PROTECTED_BASE.sha256','R1_26623_VENDOR_PROTECTED_CANDIDATE.sha256',778)]:
    assert len([x for x in (P/a).read_text().splitlines() if x.strip()])==n
    assert (P/a).read_bytes()==(P/b).read_bytes(); verify(B,a); verify(C,b)
changed=[x.strip() for x in (P/'R1_26623_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
added=[x.strip() for x in (P/'R1_26623_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
assert len(changed)==7 and len(set(changed))==7 and len(added)==0
pre=[x for x in (P/'R1_26623_PREWRITE_SOURCE_HASHES.sha256').read_text().splitlines() if x.strip()]
post=[x for x in (P/'R1_26623_EXPECTED_CHANGED_SOURCE_HASHES.sha256').read_text().splitlines() if x.strip()]
assert len(pre)==7 and len(post)==7
print('PASS 26623 authority manifests 1713 base / 1713 candidate / 1706 protected / 802 native / 778 vendor / 7 DNG / 7 runtime delta')
