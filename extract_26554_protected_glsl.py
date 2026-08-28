#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

NAMES=("directionalSmooth","iirRgb")

def kotlin_trim_indent(s: str) -> str:
    # Kotlin's trimIndent(): trim blank first/last lines, find minimum indent among
    # remaining nonblank lines, remove up to that indent from every line.
    lines=s.splitlines()
    while lines and lines[0].strip()=="": lines.pop(0)
    while lines and lines[-1].strip()=="": lines.pop()
    if not lines: return ""
    indents=[]
    for line in lines:
        if line.strip():
            indents.append(len(line)-len(line.lstrip()))
    m=min(indents) if indents else 0
    out=[]
    for line in lines:
        cut=min(m,len(line)-len(line.lstrip())) if line.strip() else min(m,len(line))
        out.append(line[cut:])
    return "\n".join(out)

def raw_value(text: str, name: str) -> str:
    pat=re.compile(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',re.S)
    m=pat.search(text)
    if not m: raise SystemExit(f"missing raw-string shader/value {name}")
    return kotlin_trim_indent("\n"+m.group(1)+"\n")

def extract(source: Path):
    text=source.read_text()
    common=raw_value(text,"common")
    result={}
    for name in NAMES:
        body=raw_value(text,name)
        # raw_value already applies outer trimIndent too early if interpolation isn't expanded.
        # Re-extract raw source, perform Kotlin interpolation first, then outer trimIndent.
        pat=re.compile(r'(?m)^\s*val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',re.S)
        m=pat.search(text)
        if not m: raise SystemExit(f"missing shader {name}")
        interpolated=("\n"+m.group(1)+"\n").replace("$common",common)
        result[name]=kotlin_trim_indent(interpolated)
    return common,result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source',type=Path)
    ap.add_argument('outdir',type=Path)
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test:
        assert kotlin_trim_indent("\n    a\n      b\n    ") == "a\n  b"
        assert kotlin_trim_indent("\n  a\n\nb\n") == "  a\n\nb"
        print("PASS extractor self-test")
        return
    common,shaders=extract(a.source)
    a.outdir.mkdir(parents=True,exist_ok=True)
    for name,src in shaders.items():
        if not re.match(r'^\s*#version 310 es(?:\n|$)', src):
            raise SystemExit(f'{name}: exact expanded shader does not start with #version after whitespace')
        if '$common' in src or '${' in src:
            raise SystemExit(f'{name}: unresolved Kotlin interpolation')
        if '#import' in src:
            raise SystemExit(f'{name}: unexpected import/preprocess dependency')
        out=a.outdir/(name+'.comp')
        out.write_text(src+'\n')
        print(f'{name}\t{len(src.splitlines())} lines\t{out}')

if __name__=='__main__': main()
