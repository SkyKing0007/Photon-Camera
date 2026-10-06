#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

EXPECTED = [
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/model/CameraFragmentModel.java',
'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java',
'app/src/main/res/layout/camera_fragment.xml',
'app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/layout/layout_main_topbar.xml',
'app/version.properties',
]
if len(sys.argv) != 4:
    raise SystemExit('usage: transform_26773.py BASE OUT PAYLOAD')
base,out,payload = map(Path, sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base, out)
files=sorted(str(p.relative_to(payload)) for p in payload.rglob('*') if p.is_file())
if files != EXPECTED:
    raise SystemExit(f'payload allowlist mismatch: {files}')
for rel in EXPECTED:
    src=payload/rel; dst=out/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src,dst)
print('PASS 26773 deterministic candidate reconstruction: exactly 7 modified files, 0 additions, 0 deletions')
