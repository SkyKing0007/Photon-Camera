#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
FILES=[x.strip() for x in (HERE/'26537_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]

def balanced_source(text:str,path:str):
    # Lightweight lexical balance check; Android/Kotlin/Java real compilation remains a mandatory Actions gate.
    pairs={')':'(',']':'[','}':'{'}; opens=set(pairs.values()); stack=[]
    i=0; n=len(text); quote=None; line=False; block=False
    while i<n:
        c=text[i]; d=text[i+1] if i+1<n else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and d=='/': block=False; i+=1
        elif quote:
            if c=='\\': i+=1
            elif c==quote: quote=None
        else:
            if c=='/' and d=='/': line=True; i+=1
            elif c=='/' and d=='*': block=True; i+=1
            elif c in ('"',"'"): quote=c
            elif c in opens: stack.append(c)
            elif c in pairs:
                if not stack or stack.pop()!=pairs[c]: raise SystemExit(f'{path}: unbalanced {c}')
        i+=1
    if quote or block or stack: raise SystemExit(f'{path}: unterminated lexical structure quote={quote} block={block} stack={stack[-8:]}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); r=Path(a.root)
    for rel in FILES:
        p=r/rel
        if not p.is_file(): raise SystemExit(f'missing changed source: {rel}')
        b=p.read_bytes()
        if b'\x00' in b: raise SystemExit(f'NUL byte in {rel}')
        balanced_source(b.decode('utf-8'),rel)
    print(f'PASS: 26537 changed-source lexical syntax preflight files={len(FILES)}')
if __name__=='__main__': main()
