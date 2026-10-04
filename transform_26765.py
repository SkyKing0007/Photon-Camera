#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26765.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
prior={
expected[0]:'ca68892e5ba3b5b4bd7eda4dab56cd6ae5d85a7c77f1c3c17e5bcf8fce8e11e9',
expected[1]:'ae23e46bf82bd5df8c8f71321695aaf3021c2b1acf1d8445f160dc910edf73aa',
}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); assert got==prior[rel],f'26764 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out); changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==expected,(changed,expected)
print('PASS 26765 deterministic candidate transform; exact 2-file runtime allowlist')
