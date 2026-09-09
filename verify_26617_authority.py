#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=4: raise SystemExit('usage: verify_26617_authority.py ROOT BASE CAND')
P=Path(sys.argv[1]); B=Path(sys.argv[2]); C=Path(sys.argv[3])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readm(name): return [(sha,rel) for sha,rel in (line.split('  ',1) for line in (P/name).read_text().splitlines() if line.strip())]
def check(root,name,count=None):
    m=readm(name)
    if count is not None and len(m)!=count: raise SystemExit(f'{name} count {len(m)} != {count}')
    for sha,rel in m:
        q=root/rel
        if not q.is_file() or h(q)!=sha: raise SystemExit(f'{name} mismatch {rel}')
    return m
check(B,'R1_26617_BASE_26616_R1_FULL_APP.sha256',1716)
check(C,'R1_26617_EXPECTED_CANDIDATE_FULL_APP.sha256',1716)
check(B,'R1_26617_PROTECTED_UNCHANGED_BASE.sha256',1709); check(C,'R1_26617_PROTECTED_UNCHANGED_CANDIDATE.sha256',1709)
check(B,'R1_26617_NATIVE_PROTECTED_BASE.sha256',803); check(C,'R1_26617_NATIVE_PROTECTED_CANDIDATE.sha256',803)
check(B,'R1_26617_VENDOR_PROTECTED_BASE.sha256',778); check(C,'R1_26617_VENDOR_PROTECTED_CANDIDATE.sha256',778)
check(B,'R1_26617_DNG_BASE.sha256',7); check(C,'R1_26617_DNG_CANDIDATE.sha256',7)
changed=[x for x in (P/'R1_26617_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
if len(changed)!=7 or len(set(changed))!=7: raise SystemExit('changed allowlist')
def H(root): return {str(p.relative_to(root)):h(p) for p in (root/'app').rglob('*') if p.is_file()}
hb,hc=H(B),H(C); actual=sorted(k for k in set(hb)|set(hc) if hb.get(k)!=hc.get(k))
if actual!=sorted(changed): raise SystemExit('runtime allowlist mismatch\nactual='+repr(actual)+'\nexpected='+repr(sorted(changed)))
for rel in changed:
    if not rel.startswith('app/'): raise SystemExit('non-app runtime path')
for root in (B,C):
    if (root/'app/build').exists() and any(p.is_file() for p in (root/'app/build').rglob('*')): raise SystemExit('generated app/build in authority')
    if (root/'app/.cxx').exists() and any(p.is_file() for p in (root/'app/.cxx').rglob('*')): raise SystemExit('generated app/.cxx in authority')
print('PASS 26617 exact successful-26616-R1.2 authority + 7-file allowlist + 1716 candidate + protected/DNG/native/vendor completeness')
