#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26806.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties',
]
PRIOR={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt':'4b5b4b71e670281f40b38f8a51ad7e744b64f6dfee33e44df6b19879dac53d88',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'2ebf051306f75db6b60cd4272e0a853fe37c5be6c336b823695aa3b54d8f8fc0',
'app/version.properties':'b8eeed119c6120768df677c88ed85e9a2d07c431cae079b00ecc953b1a09394e',
}
EXPECTED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt':'c39e42fa00c07f0fe5bcc7d5f0424c8fea7f11fb0b14485b8ec9c14caa276956',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'a8facb37ac3ad43b5b11853e7355f8908e22d574757e48f23b4d367e817af41e',
'app/version.properties':'fee24d00802b6fb4f371c546b00fefe5a399a493ce7c12adaf0e7c68e77f1a91',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1782: raise SystemExit(f'base file count {len(base_files)} != 1782')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26805 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26806 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26806 deterministic authority-seeded candidate reconstruction: 1782 base -> 1782 candidate; exact 3-file payload overlay')
