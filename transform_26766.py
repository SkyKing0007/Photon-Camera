#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26766.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
prior={
expected[0]:'336fc4bac85ca9599700f98f2eca1d9b2e1c7dfa2df4008527ec00f427e7d1cc',
expected[1]:'77a1e444a09cbb330330e51a183d4f34697f5d6eb220de4d64634e49ddaaef9b',
}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); assert got==prior[rel],f'26765 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==expected,(changed,expected)
print('PASS 26766 deterministic candidate transform; exact 2-file runtime allowlist')
