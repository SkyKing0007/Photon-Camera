#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, subprocess, sys

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_manifest(p:Path):
    out=[]
    for raw in p.read_text().splitlines():
        if not raw.strip(): continue
        v,rel=raw.split('  ',1); out.append((v,rel))
    return out

def verify_pre(root:Path,pin:Path):
    for want,rel in parse_manifest(pin):
        p=root/rel
        if want=='ABSENT':
            if p.exists(): raise SystemExit(f'prewrite expected absent: {rel}')
        else:
            if not p.is_file() or sha(p)!=want: raise SystemExit(f'prewrite hash mismatch: {rel}')

def verify_post(root:Path,pin:Path):
    for want,rel in parse_manifest(pin):
        p=root/rel
        if not p.is_file() or sha(p)!=want: raise SystemExit(f'candidate hash mismatch: {rel}')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--patch',type=Path,required=True)
    ap.add_argument('--prewrite',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,required=True)
    a=ap.parse_args()
    verify_pre(a.root,a.prewrite)
    subprocess.run(['git','apply','--check',str(a.patch.resolve())],cwd=a.root,check=True)
    subprocess.run(['git','apply',str(a.patch.resolve())],cwd=a.root,check=True)
    verify_post(a.root,a.candidate)
    print('PASS 26564 candidate-first exact patch transform + pre/post hashes')
if __name__=='__main__': main()
