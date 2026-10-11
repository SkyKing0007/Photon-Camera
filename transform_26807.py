#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26807.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/version.properties',
]
PRIOR={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt':'c39e42fa00c07f0fe5bcc7d5f0424c8fea7f11fb0b14485b8ec9c14caa276956',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java':'41b53d406d4c0bab159e314563703dd1e9ecf972a499d9a588e17ae04dfc69b0',
'app/version.properties':'fee24d00802b6fb4f371c546b00fefe5a399a493ce7c12adaf0e7c68e77f1a91',
}
EXPECTED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt':'50514a5b1aed75bf9784105c78d4d87d6d01cc4e7f9415fbb8d63e85f1e8c7f1',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java':'47bcd8ab3f9d06a89f01ba2781f979c2fafbf32059dfddc78afad715e1507e51',
'app/version.properties':'0138c128cc9a721b3c22eb34a1a245f847ab0554e517b12cc5a871fab864c7d5',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1782: raise SystemExit(f'base file count {len(base_files)} != 1782')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26806 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26807 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26807 deterministic authority-seeded candidate reconstruction: 1782 base -> 1782 candidate; exact 3-file payload overlay')
