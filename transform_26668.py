#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26668.py BASE OUT')
base = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
root = Path(__file__).resolve().parent
payload = root / 'handoff_payload_26668'
prewrite = root / 'R1_26668_PREWRITE_SOURCE_HASHES.sha256'
expected = root / 'R1_26668_EXPECTED_CHANGED_SOURCE_HASHES.sha256'
changed_file = root / 'R1_26668_RUNTIME_CHANGED_PATHS.txt'

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_prewrite(p: Path):
    rows = {}
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        h, rel = line.split('  ', 1)
        rows[rel] = h
    return rows

def parse_manifest(p: Path):
    rows = {}
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        h, rel = line.split('  ', 1)
        rows[rel] = h
    return rows

changed = [x for x in changed_file.read_text().splitlines() if x]
assert len(changed) == 18 and len(set(changed)) == 18
pre = parse_prewrite(prewrite)
exp = parse_manifest(expected)
assert set(pre) == set(changed) == set(exp)

# Authority-seeded prewrite proof. Added paths must be absent; every modified source byte must
# match the exact successful 26667 compiled candidate before any replacement is installed.
for rel in changed:
    p = base / rel
    h = pre[rel]
    if h == 'ABSENT':
        if p.exists():
            raise SystemExit(f'FAIL prewrite added path already exists in 26667 authority: {rel}')
    else:
        if not p.is_file() or sha(p) != h:
            raise SystemExit(f'FAIL prewrite authority hash: {rel}')

if out.exists():
    shutil.rmtree(out)
shutil.copytree(base, out)

# Candidate-first exact replacements. Payload bytes are themselves sealed by the handoff hash and
# candidate manifest; binary assets are copied byte-for-byte rather than re-encoded.
for rel in changed:
    src = payload / rel
    dst = out / rel
    if not src.is_file():
        raise SystemExit(f'FAIL missing 26668 payload: {rel}')
    if sha(src) != exp[rel]:
        raise SystemExit(f'FAIL payload hash: {rel}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

for rel in changed:
    if sha(out / rel) != exp[rel]:
        raise SystemExit(f'FAIL transformed candidate hash: {rel}')

print('TRANSFORM_26668_OK exact successful-26667 authority -> frozen 18-path candidate (14 modified / 4 added)')
