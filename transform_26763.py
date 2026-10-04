#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26763.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
prior={
expected[0]:'70f44a78958362048cbd065962514de203fc454086aadf8fb8b936a1948a4f81',
expected[1]:'4caf055d180223df262c940a6784b92dbcabf6b54972a353b81067ec6c9990bd',
}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel
 got=hashlib.sha256(p.read_bytes()).hexdigest()
 assert got==prior[rel],f'26762 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
# Exact runtime changed-file equality.
def H(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out)
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==expected,(changed,expected)
print('PASS 26763 deterministic candidate transform; exact 2-file runtime allowlist')
