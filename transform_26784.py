#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26784.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
allowed=(Path(__file__).resolve().parent/'26784_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
if out.exists(): shutil.rmtree(out)
shutil.copytree(base/'app',out/'app')
files=sorted(str(p.relative_to(payload)) for p in payload.rglob('*') if p.is_file())
assert files==allowed,(files,allowed)
for rel in allowed:
 src=payload/rel; dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print(f'PASS 26784 deterministic authority-seeded transform: {len(allowed)} intended runtime files over exact successful 26783 candidate')
