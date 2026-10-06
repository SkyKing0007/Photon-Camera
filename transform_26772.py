#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4:
    raise SystemExit('usage: transform_26772.py BASE26771 OUT26772 PAYLOAD')
base, out, payload = map(Path, sys.argv[1:])
root = Path(__file__).resolve().parent
modified = [x for x in (root/'26772_MODIFIED_PATHS.txt').read_text().splitlines() if x]
deleted = [x for x in (root/'26772_DELETED_PATHS.txt').read_text().splitlines() if x]
expected = [x for x in (root/'26772_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
if sorted(modified + deleted) != sorted(expected) or set(modified) & set(deleted):
    raise SystemExit('26772 scope manifests inconsistent')
# Authority-seeded reconstruction: copy exact successful compiled-candidate app universe only.
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True)
shutil.copytree(base/'app', out/'app')
# Delete only the frozen Gallery paths.
for rel in deleted:
    p = out/rel
    if not p.is_file(): raise SystemExit(f'deletion authority missing: {rel}')
    p.unlink()
# Overlay only the frozen modified payload.
for rel in modified:
    src = payload/rel
    if not src.is_file(): raise SystemExit(f'payload missing: {rel}')
    dst = out/rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src,dst)
# No payload extras.
payload_files = sorted(str(p.relative_to(payload)) for p in payload.rglob('*') if p.is_file())
if payload_files != sorted(modified): raise SystemExit('payload allowlist mismatch')
print(f'PASS 26772 deterministic candidate transform: {len(expected)} runtime paths / {len(modified)} modifications / {len(deleted)} deletions / 0 additions')
