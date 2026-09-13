#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26636_r1_authority.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent
changed=[x for x in (pkg/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; added=set(x for x in (pkg/'R1_26636_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x)
assert len(changed)==18 and len(set(changed))==18 and len(added)==3
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
verify(B,'R1_26636_BASE_26635_R1_FULL_APP.sha256',1713); verify(C,'R1_26636_EXPECTED_CANDIDATE_FULL_APP.sha256',1716)
verify(B,'R1_26636_PROTECTED_UNCHANGED_BASE.sha256',1698); verify(C,'R1_26636_PROTECTED_UNCHANGED_CANDIDATE.sha256',1698)
verify(B,'R1_26636_NATIVE_PROTECTED_BASE.sha256',801); verify(C,'R1_26636_NATIVE_PROTECTED_CANDIDATE.sha256',801)
verify(B,'R1_26636_VENDOR_PROTECTED_BASE.sha256',778); verify(C,'R1_26636_VENDOR_PROTECTED_CANDIDATE.sha256',778)
verify(B,'R1_26636_DNG_BASE.sha256',7); verify(C,'R1_26636_DNG_CANDIDATE.sha256',7)
verify(B,'R1_26636_PREWRITE_SOURCE_HASHES.sha256',15); verify(C,'R1_26636_EXPECTED_CHANGED_SOURCE_HASHES.sha256',18)
for rel in added: assert not (B/rel).exists(),f'added path exists in base {rel}'
bf={str(p.relative_to(B)):H(p) for p in sorted((B/'app').rglob('*')) if p.is_file()}; cf={str(p.relative_to(C)):H(p) for p in sorted((C/'app').rglob('*')) if p.is_file()}
assert len(bf)==1713 and len(cf)==1716; actual={p for p in set(bf)|set(cf) if bf.get(p)!=cf.get(p)}; assert actual==set(changed),sorted(actual^set(changed)); assert set(cf)-set(bf)==added and not(set(bf)-set(cf))
for a,b in [('R1_26636_PROTECTED_UNCHANGED_BASE.sha256','R1_26636_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26636_NATIVE_PROTECTED_BASE.sha256','R1_26636_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26636_VENDOR_PROTECTED_BASE.sha256','R1_26636_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26636_DNG_BASE.sha256','R1_26636_DNG_CANDIDATE.sha256')]: assert (pkg/a).read_bytes()==(pkg/b).read_bytes(),(a,b)
print('PASS 26636 authority: exact successful-26635 1713-file base + exact 18-path candidate delta + 1698/801/778/7 protected invariance')
