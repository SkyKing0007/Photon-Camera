#!/usr/bin/env python3
from pathlib import Path
import shutil, sys
if len(sys.argv)!=4:
    raise SystemExit('usage: transform_26771.py BASE26770 CAND26771 PAYLOAD')
base, out, payload = map(Path, sys.argv[1:4])
root=Path(__file__).resolve().parent
changed=[x for x in (root/'26771_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'26771_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
if out.exists(): shutil.rmtree(out)
shutil.copytree(base/'app', out/'app')
for rel in added:
    if (base/rel).exists(): raise SystemExit(f'added path unexpectedly exists in authority: {rel}')
payload_files=sorted(str(p.relative_to(payload)) for p in payload.rglob('*') if p.is_file())
if payload_files!=sorted(changed):
    raise SystemExit(f'payload allowlist mismatch\nactual={payload_files}\nexpected={sorted(changed)}')
for rel in changed:
    src=payload/rel
    if not src.is_file(): raise SystemExit(f'missing payload: {rel}')
    dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print(f'PASS 26771 deterministic candidate transform: {len(changed)} runtime paths / {len(added)} addition')
