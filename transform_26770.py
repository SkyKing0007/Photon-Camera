#!/usr/bin/env python3
from pathlib import Path
import shutil,sys,hashlib
if len(sys.argv)!=4: raise SystemExit('usage: transform_26770.py BASE OUT PAYLOAD')
base,out,payload=map(Path,sys.argv[1:])
expected=[p for p in Path(__file__).resolve().parent.joinpath('26770_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if p]
prior={}
for line in Path(__file__).resolve().parent.joinpath('26770_PRIOR_RUNTIME_HASHES.txt').read_text().splitlines():
    if line.strip():
        h,rel=line.split('  ',1); prior[rel]=h
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in expected:
    p=base/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); assert got==prior[rel],f'26769 prior hash mismatch {rel}: {got}'
    src=payload/rel; assert src.is_file(),f'missing payload {rel}'
    dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(out); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==sorted(expected),(changed,expected)
print('PASS 26770 deterministic candidate transform; exact 5-file runtime allowlist')
