#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26688.py BASE OUT')
root=Path(__file__).resolve().parent
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); payload=root/'handoff_payload_26688'
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mf(path):
    d={}
    for line in Path(path).read_text().splitlines():
        if line.strip(): hh,rel=line.split('  ',1); d[rel]=hh
    return d
changed=[x for x in (root/'R1_26688_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'R1_26688_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
pre=mf(root/'R1_26688_PREWRITE_SOURCE_HASHES.sha256')
for rel,hh in pre.items():
    p=base/rel
    if not p.is_file() or h(p)!=hh: raise SystemExit('FAIL exact 26687 R1.1 prewrite '+rel)
for rel in added:
    if (base/rel).exists(): raise SystemExit('FAIL added path unexpectedly exists in 26687 R1.1 authority '+rel)
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in changed:
    src=payload/rel
    if not src.is_file(): raise SystemExit('FAIL payload missing '+rel)
    dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
exp=mf(root/'R1_26688_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
for rel,hh in exp.items():
    if h(out/rel)!=hh: raise SystemExit('FAIL transformed changed hash '+rel)
v=(out/'app/version.properties').read_text()
for tok in ['VERSION_NAME=0.9726688','VERSION_BUILD=26688']:
    if tok not in v: raise SystemExit('FAIL version '+tok)
print('PASS 26688 transform: exact successful 26687 R1.1 authority -> exact 10-path Spektra RAW-frontend replacement candidate')
