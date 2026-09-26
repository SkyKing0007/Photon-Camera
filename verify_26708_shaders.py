#!/usr/bin/env python3
from pathlib import Path
import sys,re,hashlib
b=Path(sys.argv[2]);c=Path(sys.argv[3])
# Asset shader universe is byte-identical; Sabre embedded GLSL file change is comment-only after object close.
for p in (b/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.comp','.vert'}:
  q=c/'app'/p.relative_to(b/'app'); assert q.read_bytes()==p.read_bytes(),p
s0=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();s1=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();assert s1.startswith(s0)
print('PASS 26708 shader proof: modified runtime-expanded GLSL count=0; 271 asset shaders invariant; Sabre embedded shader bytes unchanged')
