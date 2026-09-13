#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26635_r1_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
changed=[x for x in (pkg/'R1_26635_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; assert len(changed)==3 and len(set(changed))==3
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
    out=[]
    for line in (pkg/name).read_text().splitlines():
        if line.strip(): d,rel=line.split('  ',1); out.append((d,rel))
    return out
def verify(where,name,count):
    rows=load(name); assert len(rows)==count,(name,len(rows),count)
    for d,rel in rows:
        p=where/rel; assert p.is_file(),f'{name} missing {rel}'; assert H(p)==d,f'{name} hash {rel}'
    return rows
verify(B,'R1_26635_BASE_26634_R1_FULL_APP.sha256',1713); verify(C,'R1_26635_EXPECTED_CANDIDATE_FULL_APP.sha256',1713)
verify(B,'R1_26635_PROTECTED_UNCHANGED_BASE.sha256',1710); verify(C,'R1_26635_PROTECTED_UNCHANGED_CANDIDATE.sha256',1710)
verify(B,'R1_26635_NATIVE_PROTECTED_BASE.sha256',802); verify(C,'R1_26635_NATIVE_PROTECTED_CANDIDATE.sha256',802)
verify(B,'R1_26635_VENDOR_PROTECTED_BASE.sha256',778); verify(C,'R1_26635_VENDOR_PROTECTED_CANDIDATE.sha256',778)
verify(B,'R1_26635_DNG_BASE.sha256',7); verify(C,'R1_26635_DNG_CANDIDATE.sha256',7)
verify(B,'R1_26635_PREWRITE_SOURCE_HASHES.sha256',3); verify(C,'R1_26635_EXPECTED_CHANGED_SOURCE_HASHES.sha256',3)
bf={str(p.relative_to(B)):H(p) for p in sorted((B/'app').rglob('*')) if p.is_file()}; cf={str(p.relative_to(C)):H(p) for p in sorted((C/'app').rglob('*')) if p.is_file()}; assert set(bf)==set(cf); actual={p for p in bf if bf[p]!=cf[p]}; assert actual==set(changed),sorted(actual^set(changed))
for a,b in [('R1_26635_PROTECTED_UNCHANGED_BASE.sha256','R1_26635_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26635_NATIVE_PROTECTED_BASE.sha256','R1_26635_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26635_VENDOR_PROTECTED_BASE.sha256','R1_26635_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26635_DNG_BASE.sha256','R1_26635_DNG_CANDIDATE.sha256')]: assert (pkg/a).read_bytes()==(pkg/b).read_bytes(),(a,b)
print('PASS 26635 authority: exact successful-26634 1713-file base + exact 3-file candidate delta + 1710/802/778/7 invariance')
