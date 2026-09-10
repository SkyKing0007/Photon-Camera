#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26619_r2_authority.py PACKAGE_ROOT BASE CAND')
P=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
    lines=[x for x in (P/manifest).read_text().splitlines() if x.strip()]
    for line in lines:
        sha,rel=line.split('  ',1); q=root/rel
        assert q.is_file(),rel; assert h(q)==sha,(rel,h(q),sha)
    return len(lines)
assert verify(B,'R2_26619_BASE_26618_R1_FULL_APP.sha256')==1712
assert verify(C,'R2_26619_EXPECTED_CANDIDATE_FULL_APP.sha256')==1711
assert verify(B,'R2_26619_PROTECTED_UNCHANGED_BASE.sha256')==1701
assert verify(C,'R2_26619_PROTECTED_UNCHANGED_CANDIDATE.sha256')==1701
assert (P/'R2_26619_PROTECTED_UNCHANGED_BASE.sha256').read_bytes()==(P/'R2_26619_PROTECTED_UNCHANGED_CANDIDATE.sha256').read_bytes()
assert verify(B,'R2_26619_DNG_BASE.sha256')==7 and verify(C,'R2_26619_DNG_CANDIDATE.sha256')==7
assert (P/'R2_26619_DNG_BASE.sha256').read_bytes()==(P/'R2_26619_DNG_CANDIDATE.sha256').read_bytes()
for a,b,n in [
('R2_26619_NATIVE_PROTECTED_BASE.sha256','R2_26619_NATIVE_PROTECTED_CANDIDATE.sha256',802),
('R2_26619_VENDOR_PROTECTED_BASE.sha256','R2_26619_VENDOR_PROTECTED_CANDIDATE.sha256',778)]:
    assert len([x for x in (P/a).read_text().splitlines() if x.strip()])==n
    assert (P/a).read_bytes()==(P/b).read_bytes()
    verify(B,a); verify(C,b)
changed=[x.strip() for x in (P/'R2_26619_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
assert len(changed)==13 and len(set(changed))==13
added=[x.strip() for x in (P/'R2_26619_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
deleted=[x.strip() for x in (P/'R2_26619_DELETED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
assert len(added)==2 and len(deleted)==3
for rel in added: assert not (B/rel).exists() and (C/rel).is_file(),rel
for rel in deleted: assert (B/rel).is_file() and not (C/rel).exists(),rel
print('PASS 26619 authority manifests 1712 base / 1711 candidate / 1701 protected / 802 native / 778 vendor / 7 DNG / 13 runtime paths')
