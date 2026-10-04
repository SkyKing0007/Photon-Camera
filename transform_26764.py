#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26764.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
prior={
expected[0]:'9d5bdbdd8480cd9b9db0b7a50a936cc8913bac52ee66b219c1b72b415c7f5769',
expected[1]:'ee770316f205a8fbeffa3cbcf20f7e430505c497f037a9f3af3d71401a33e3b3',
}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel
 got=hashlib.sha256(p.read_bytes()).hexdigest()
 assert got==prior[rel],f'26763 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out)
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==expected,(changed,expected)
print('PASS 26764 deterministic candidate transform; exact 2-file runtime allowlist')
