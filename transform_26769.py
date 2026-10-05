#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26769.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/version.properties']
prior={
 expected[0]:'7f8424a7e50858b7e5b3098964146e27f8fd943fd8a58fe7cc9189373387192c',
 expected[1]:'ba318a90099f7aa8d231f67ab53c03d16e6252399883276f2ab21177d895e911',
 expected[2]:'a29aaf3cd04e083467a8ef6c66cb8f310990f5a1f55360e50bd19f2cdfa8bb95',
}
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
 p=base/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); assert got==prior[rel],f'26768 prior hash mismatch {rel}: {got}'
 src=payload/rel; assert src.is_file(),f'missing payload {rel}'
 dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==sorted(expected),(changed,expected)
print('PASS 26769 deterministic candidate transform; exact 3-file runtime allowlist')
