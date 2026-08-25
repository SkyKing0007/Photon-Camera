#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,subprocess,tempfile,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
PATCH=HERE/'26539_RUNTIME_DELTA_FROM_26538.patch'
FILES=[x.strip() for x in (HERE/'26539_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run_patch(root:Path,dry=False):
    cmd=['patch','-d',str(root),'-p1','--batch','--forward','--fuzz=0','--no-backup-if-mismatch']
    if dry: cmd.append('--dry-run')
    subprocess.run(cmd,input=PATCH.read_bytes(),check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def check_base(root:Path):
    for rel in FILES:
        if not (root/rel).is_file(): raise SystemExit(f'missing runtime file: {rel}')
    text=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    if 'IRIS_26538_NIGHT_SPATIAL_RGB_PRODUCTION_AUTHORITY' not in text: raise SystemExit('not an exact 26538-lineage candidate')
    if 'IRIS_26539_NIGHT_PUBLICATION_OWNERSHIP' in text: raise SystemExit('26539 appears already applied')
def self_test():
    assert len(FILES)==4 and FILES==sorted(FILES) and len(set(FILES))==4
    assert PATCH.is_file() and PATCH.stat().st_size>0
    assert b'IRIS_26539_NIGHT_POST_OWNER_CLOSE_BEFORE_JIN' in PATCH.read_bytes()
    assert b'IRIS_26539_AUTOMATIC_PECAN_LUMA_FLOOR' in PATCH.read_bytes()
    print('PASS: 26539 apply self-test patch/inventory loaded')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--check',action='store_true'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test(); return
    if not a.root: ap.error('root required')
    root=Path(a.root).resolve(); check_base(root)
    run_patch(root,dry=a.check)
    print('PASS: 26539 patch '+('dry-run ' if a.check else '')+'applied with fuzz=0')
if __name__=='__main__': main()
