#!/usr/bin/env python3
from pathlib import Path
import argparse, tempfile

REL = Path('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
OLD = '            ByteBuffer source = plane.getBuffer().duplicate();\n'
NEW = '            java.nio.ByteBuffer source = plane.getBuffer().duplicate();\n'

def apply(root: Path):
    p = root / REL
    s = p.read_text()
    n = s.count(OLD)
    if n != 1:
        raise RuntimeError(f'Night spool ByteBuffer anchor: expected exactly 1, found {n}')
    if NEW in s:
        raise RuntimeError('Night spool ByteBuffer correction already present before V1.4 transform')
    s = s.replace(OLD, NEW, 1)
    p.write_text(s)
    print('PASS: 26543 V1.4 javac ByteBuffer symbol correction applied')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root')
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    if a.self_test:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / REL
            p.parent.mkdir(parents=True)
            p.write_text('class X {\n' + OLD + '}\n')
            apply(Path(td))
            out = p.read_text()
            assert NEW in out and OLD not in out
        print('PASS: 26543 V1.4 javac ByteBuffer correction self-test')
        return
    if not a.root:
        ap.error('--root required')
    apply(Path(a.root).resolve())

if __name__ == '__main__':
    main()
