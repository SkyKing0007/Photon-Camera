#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26634_r1_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
changed=[x for x in (pkg/'R1_26634_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert len(changed)==8 and len(set(changed))==8

def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_manifest(name):
    out=[]
    for line in (pkg/name).read_text().splitlines():
        if line.strip():
            d,rel=line.split('  ',1); out.append((d,rel))
    return out
def verify(where,name,count):
    rows=load_manifest(name); assert len(rows)==count,(name,len(rows),count)
    for d,rel in rows:
        p=where/rel; assert p.is_file(),f'{name} missing {rel}'; assert H(p)==d,f'{name} hash {rel}'
    return rows
verify(base,'R1_26634_BASE_26633_R1_FULL_APP.sha256',1713)
verify(cand,'R1_26634_EXPECTED_CANDIDATE_FULL_APP.sha256',1713)
verify(base,'R1_26634_PROTECTED_UNCHANGED_BASE.sha256',1705)
verify(cand,'R1_26634_PROTECTED_UNCHANGED_CANDIDATE.sha256',1705)
verify(base,'R1_26634_NATIVE_PROTECTED_BASE.sha256',802); verify(cand,'R1_26634_NATIVE_PROTECTED_CANDIDATE.sha256',802)
verify(base,'R1_26634_VENDOR_PROTECTED_BASE.sha256',778); verify(cand,'R1_26634_VENDOR_PROTECTED_CANDIDATE.sha256',778)
verify(base,'R1_26634_DNG_BASE.sha256',7); verify(cand,'R1_26634_DNG_CANDIDATE.sha256',7)
verify(base,'R1_26634_PREWRITE_SOURCE_HASHES.sha256',8); verify(cand,'R1_26634_EXPECTED_CHANGED_SOURCE_HASHES.sha256',8)
# full universe must differ exactly on allowlist
bf={str(p.relative_to(base)):H(p) for p in sorted((base/'app').rglob('*')) if p.is_file()}
cf={str(p.relative_to(cand)):H(p) for p in sorted((cand/'app').rglob('*')) if p.is_file()}
assert set(bf)==set(cf)
actual={p for p in bf if bf[p]!=cf[p]}
assert actual==set(changed), sorted(actual^set(changed))
# protected manifests must be byte-identical by contract
for pair in [('R1_26634_PROTECTED_UNCHANGED_BASE.sha256','R1_26634_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26634_NATIVE_PROTECTED_BASE.sha256','R1_26634_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26634_VENDOR_PROTECTED_BASE.sha256','R1_26634_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26634_DNG_BASE.sha256','R1_26634_DNG_CANDIDATE.sha256')]:
    assert (pkg/pair[0]).read_bytes()==(pkg/pair[1]).read_bytes(),pair
print('PASS 26634 authority: exact successful-26633 1713-file base + exact 8-file candidate delta + 1705/802/778/7 invariance')
