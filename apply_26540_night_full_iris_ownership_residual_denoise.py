#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, tarfile, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
META=HERE/'26540_RUNTIME_SHA256.json'
PAYLOAD=HERE/'26540_RUNTIME_PAYLOAD.tar.gz'

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load():
    rows=json.loads(META.read_text())
    if len(rows)!=18: raise SystemExit(f'expected 18 runtime entries, got {len(rows)}')
    paths=[r['path'] for r in rows]
    if paths!=sorted(paths) or len(set(paths))!=len(paths): raise SystemExit('runtime metadata not sorted/unique')
    return rows

def verify_payload(rows):
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        with tarfile.open(PAYLOAD,'r:gz') as tf:
            for m in tf.getmembers():
                q=Path(m.name)
                if q.is_absolute() or '..' in q.parts: raise SystemExit('unsafe payload member '+m.name)
            tf.extractall(td)
        for r in rows:
            p=td/r['path']
            if not p.is_file(): raise SystemExit('payload missing '+r['path'])
            if sha(p)!=r['target_sha256']: raise SystemExit('payload target hash mismatch '+r['path'])

def apply(root:Path):
    rows=load(); verify_payload(rows)
    for r in rows:
        p=root/r['path']
        if r['new_file']:
            if p.exists(): raise SystemExit('new 26540 file already exists in base: '+r['path'])
        else:
            if not p.is_file(): raise SystemExit('26539 base file missing: '+r['path'])
            if sha(p)!=r['base_sha256']: raise SystemExit('26539 base hash drift: '+r['path'])
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        with tarfile.open(PAYLOAD,'r:gz') as tf: tf.extractall(td)
        for r in rows:
            src=td/r['path']; dst=root/r['path']; dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            if sha(dst)!=r['target_sha256']: raise SystemExit('26540 installed hash mismatch: '+r['path'])
    print('PASS: exact 18-file 26539 -> 26540 V1.1 runtime payload applied')

def self_test():
    rows=load(); verify_payload(rows)
    assert sum(1 for r in rows if r['new_file'])==2
    print('PASS: 26540 apply self-test payload=18 files new=2')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.root: ap.error('root required')
        apply(Path(a.root).resolve())
