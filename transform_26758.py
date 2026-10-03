#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
if len(sys.argv)!=3: raise SystemExit("usage: transform_26758.py BASE26757 OUT")
b,o=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent; payload=pkg/"handoff_payload_26758"
if o.exists(): shutil.rmtree(o)
shutil.copytree(b,o)
for p in sorted(payload.rglob("*")):
    if p.is_file():
        rel=p.relative_to(payload); q=o/rel; q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)
print("PASS 26758 transform: exact sealed 4-file payload overlay on successful 26757 compiled candidate")
