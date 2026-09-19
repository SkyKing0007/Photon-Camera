#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26669.py BASE OUT')
base = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
root = Path(__file__).resolve().parent
payload = root / 'handoff_payload_26669'
prewrite = root / 'R1_26669_PREWRITE_SOURCE_HASHES.sha256'
expected = root / 'R1_26669_EXPECTED_CHANGED_SOURCE_HASHES.sha256'
changed_file = root / 'R1_26669_RUNTIME_CHANGED_PATHS.txt'

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
def parse_manifest(p: Path):
    rows={}
    for line in p.read_text().splitlines():
        if line.strip():
            h,rel=line.split('  ',1); rows[rel]=h
    return rows
changed=[x for x in changed_file.read_text().splitlines() if x]
assert len(changed)==6 and len(set(changed))==6
pre=parse_manifest(prewrite); exp=parse_manifest(expected)
assert set(pre)==set(exp)==set(changed)
for rel in changed:
    p=base/rel
    if not p.is_file() or sha(p)!=pre[rel]:
        raise SystemExit(f'FAIL prewrite authority hash: {rel}')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in changed:
    src=payload/rel; dst=out/rel
    if not src.is_file(): raise SystemExit(f'FAIL missing 26669 payload: {rel}')
    if sha(src)!=exp[rel]: raise SystemExit(f'FAIL payload hash: {rel}')
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
for rel in changed:
    if sha(out/rel)!=exp[rel]: raise SystemExit(f'FAIL transformed candidate hash: {rel}')
print('TRANSFORM_26669_OK exact successful-26668 authority -> frozen 6-path candidate (6 modified / 0 added)')
