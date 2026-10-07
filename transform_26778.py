#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
EXPECTED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java',
'app/version.properties',
]
if len(sys.argv)!=4: raise SystemExit('usage: transform_26778.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
files=sorted(str(p.relative_to(payload)) for p in payload.rglob('*') if p.is_file())
if files!=EXPECTED: raise SystemExit(f'payload allowlist mismatch: {files}')
for rel in EXPECTED:
    src=payload/rel; dst=out/rel
    if not dst.is_file(): raise SystemExit(f'expected prior runtime file missing: {rel}')
    shutil.copy2(src,dst)
print('PASS 26778 deterministic candidate reconstruction: exactly 8 modified files, 0 additions, 0 deletions')
