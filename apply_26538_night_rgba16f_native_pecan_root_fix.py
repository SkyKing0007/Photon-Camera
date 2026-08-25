#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PATCH=HERE/'26538_RUNTIME_DELTA_FROM_26537.patch'
EXPECTED=[x.strip() for x in (HERE/'26538_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]
def patch_files(text:str):
    return [line.split()[2][2:] for line in text.splitlines() if line.startswith('diff --git a/')]
def self_test():
    text=PATCH.read_text(); files=patch_files(text)
    assert files==EXPECTED,(files,EXPECTED)
    assert text.count('diff --git a/')==len(EXPECTED)
    assert all(('--- a/'+f) in text or ('--- /dev/null' in text and ('+++ b/'+f) in text) for f in EXPECTED)
    print(f'PASS: 26538 apply self-test exact {len(EXPECTED)}-file patch inventory')
def apply(root:Path):
    if not (root/'app/src/main').is_dir(): raise SystemExit(f'candidate root missing app/src/main: {root}')
    subprocess.run(['patch','-d',str(root),'-p1','--batch','--forward','--fuzz=0','--no-backup-if-mismatch'],stdin=PATCH.open('rb'),check=True)
    print('PASS: 26538 runtime patch applied with fuzz=0')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test(); return
    if not a.root: ap.error('root is required unless --self-test')
    apply(Path(a.root).resolve())
if __name__=='__main__': main()
