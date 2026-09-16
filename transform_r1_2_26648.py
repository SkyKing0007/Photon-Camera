#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_r1_2_26648.py BASE DEST')
base=Path(sys.argv[1]).resolve(); dest=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[x for x in (root/'R1_2_26648_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_2_26648_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
if changed or added: raise SystemExit(f'R1.2 packaging repair must be zero runtime delta: changed={changed} added={added}')
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest,copy_function=shutil.copy2)
payload=root/'handoff_payload_r1_2_26648'
files=sorted(p for p in payload.rglob('*') if p.is_file())
if len(files)!=8: raise SystemExit(f'expected 8 sealed runtime identity witnesses, got {len(files)}')
for p in files:
 rel=p.relative_to(payload); a=base/rel
 if not a.is_file() or sha(a)!=sha(p): raise SystemExit(f'R1.2 identity payload differs successful R1.1 authority: {rel}')
appfiles=[p for p in (dest/'app').rglob('*') if p.is_file()]
if len(appfiles)!=1720: raise SystemExit(f'candidate file count {len(appfiles)} != 1720')
print('PASS 26648 R1.2 identity transform: exact successful R1.1 compiled candidate retained byte-for-byte, 1720 files / 0 changed / 0 added')
