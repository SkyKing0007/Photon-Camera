#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26751.py BASE26750 CAND26751')
b,c=map(Path,sys.argv[1:])
vp=(c/'app/version.properties').read_text(); assert vp.count('VERSION_BUILD=26751')==1 and 'VERSION_NAME=0.9726751' in vp
expected={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823,(len(B),len(C)); assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
print('PASS 26751 semantic validation: exact 2-file scope/version from successful 26750 runtime authority')
