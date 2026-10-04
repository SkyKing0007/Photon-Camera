#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26762.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
allow=[x.strip() for x in (Path(__file__).parent/'26762_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
for rel in allow:
    src=payload/rel; dst=out/rel
    if not src.is_file(): raise SystemExit(f'missing payload {rel}')
    if not dst.is_file(): raise SystemExit(f'authority path missing {rel}')
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
print(f'PASS 26762 candidate-first overlay: {len(allow)} existing files')
