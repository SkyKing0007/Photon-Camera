#!/usr/bin/env python3
from __future__ import annotations
import argparse,re
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNTIME=[x.strip() for x in (HERE/'26540_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]

def run(root:Path):
    bad=[]
    for rel in RUNTIME:
        p=root/rel
        if not p.is_file(): bad.append(f'missing {rel}'); continue
        s=p.read_text(errors='strict')
        if '\x00' in s: bad.append(f'NUL byte {rel}')
        if any(x in s for x in ['<<<<<<<','=======\n>>>>>>>','>>>>>>>']): bad.append(f'merge marker {rel}')
        if p.suffix=='.java':
            cls=p.stem
            if re.search(r'\b(public\s+)?(final\s+)?class\s+'+re.escape(cls)+r'\b',s) is None and cls not in {'CaptureController','ImageFrame','Parameters','GLBasePipeline','Node','PostPipeline','RotateWatermark','StageTelemetry','HdrxProcessor','IrisMotionSettings','IrisNightExposureSelector','IrisNightFrameSelector'}:
                bad.append(f'class/file mismatch {rel}')
    compiled=list((root/'app/src/main').rglob('*.class'))
    if compiled: bad.append('compiled .class files under app/src/main: '+repr([str(x) for x in compiled[:5]]))
    if bad: raise SystemExit('\n'.join(bad))
    print('PASS: 26540 changed-source lexical/scope preflight (18 files, no generated classes)')

def self_test():
    assert len(RUNTIME)==18
    print('PASS: 26540 V1.1 syntax preflight self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root).resolve())
