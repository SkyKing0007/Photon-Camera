#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26744.py BASE26743 OUT26744')
base=Path(sys.argv[1]); out=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent; payload=pkg/'handoff_payload_26744'
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for p in payload.rglob('*'):
    if p.is_file():
        rel=p.relative_to(payload); q=out/rel; q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)
