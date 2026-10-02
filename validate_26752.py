#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26752.py BASE26733 CAND26752')
b,c=map(Path,sys.argv[1:])
expected=set(Path(__file__).with_name('26752_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823,(len(B),len(C)); actual={k for k in B|C if B.get(k)!=C.get(k)}; assert actual==expected,(actual^expected)
assert not (set(C)-set(B)) and not (set(B)-set(C))
vp=(c/'app/version.properties').read_text(); assert vp.count('VERSION_BUILD=26752')==1 and vp.count('VERSION_NAME=0.9726752')==1
print('PASS 26752 semantic validation: exact 11-file scope/version from successful 26733 runtime authority')
