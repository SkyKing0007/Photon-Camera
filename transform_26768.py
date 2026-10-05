#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26768.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties']
prior={
 expected[0]:'257a6c68e2fe30f634c2f8003d0c77cfd72a1ed3383762f7e6e636e2b4b248e3',
 expected[1]:'f9bdab92e3f71dbc57476d5d9c10c017260dcb42628a2dfc2ee5758c466a2197',
}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); assert got==prior[rel],f'26767 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==expected,(changed,expected)
print('PASS 26768 deterministic candidate transform; exact 2-file runtime allowlist')
