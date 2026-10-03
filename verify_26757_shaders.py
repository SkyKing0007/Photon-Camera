#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv) not in (4,6): raise SystemExit("usage: verify_26757_shaders.py PACKAGE BASE CANDIDATE [--compiler PATH]")
root,base,cand=map(Path,sys.argv[1:4]); compiler=None
if len(sys.argv)==6: assert sys.argv[4]=="--compiler"; compiler=Path(sys.argv[5]); assert compiler.is_file()
def H(r): return {p.relative_to(r/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/"app/src/main/assets/shaders").rglob("*") if p.is_file()}
a,b=H(base),H(cand); assert len(a)==len(b)==271 and a==b
print("PASS 26757 shader universe: 271 files byte-identical to successful 26756 authority; modified GLSL count=0; reserved-identifier/glslang modified-shader gates N/A")
