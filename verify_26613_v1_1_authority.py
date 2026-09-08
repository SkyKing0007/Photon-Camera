#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26613_v1_1_authority.py PACKAGE_ROOT BASE CAND')
P=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
    lines=[x for x in (P/manifest).read_text().splitlines() if x.strip()]
    for line in lines:
        sha,rel=line.split('  ',1); assert (root/rel).is_file(), rel; assert h(root/rel)==sha, rel
    return len(lines)
assert verify(B,'V1_1_26613_BASE_26612_V1_FULL_APP.sha256')==1708
assert verify(C,'V1_1_26613_EXPECTED_CANDIDATE_FULL_APP.sha256')==1708
assert verify(B,'V1_1_26613_PROTECTED_UNCHANGED_BASE.sha256')==1698
assert verify(C,'V1_1_26613_PROTECTED_UNCHANGED_CANDIDATE.sha256')==1698
assert (P/'V1_1_26613_PROTECTED_UNCHANGED_BASE.sha256').read_bytes()==(P/'V1_1_26613_PROTECTED_UNCHANGED_CANDIDATE.sha256').read_bytes()
assert verify(B,'V1_1_26613_DNG_BASE.sha256')==7 and verify(C,'V1_1_26613_DNG_CANDIDATE.sha256')==7
assert (P/'V1_1_26613_DNG_BASE.sha256').read_bytes()==(P/'V1_1_26613_DNG_CANDIDATE.sha256').read_bytes()
for a,b in [('V1_1_26613_NATIVE_PROTECTED_BASE.sha256','V1_1_26613_NATIVE_PROTECTED_CANDIDATE.sha256'),('V1_1_26613_VENDOR_PROTECTED_BASE.sha256','V1_1_26613_VENDOR_PROTECTED_CANDIDATE.sha256')]: assert (P/a).read_bytes()==(P/b).read_bytes()
assert len((P/'V1_1_26613_NATIVE_PROTECTED_BASE.sha256').read_text().splitlines())==802
assert len((P/'V1_1_26613_VENDOR_PROTECTED_BASE.sha256').read_text().splitlines())==778
print('PASS 26613 authority manifests 1708 full / 1698 protected / 802 native / 778 vendor / 7 DNG')
