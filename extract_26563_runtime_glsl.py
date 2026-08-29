#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib

GL_VERSION='#version 310 es\n'
VERTEX=(GL_VERSION+
        'precision mediump float;\n'+
        'in vec4 vPosition;\n'+
        'void main() {\n'+
        'gl_Position = vPosition;\n'+
        '}\n')

def runtime_fragment(asset: str) -> str:
    # Exact GLInterface.readProgram behavior for an asset with no #version/import/defines.
    lines=asset.splitlines()
    source=''.join(line+'\n' for line in lines)
    return GL_VERSION+'\n#line 1\n'+source

def extract(root:Path,out:Path):
    asset=root/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
    if not asset.is_file(): raise SystemExit('missing adaptive color asset shader')
    src=asset.read_text()
    if '#version' in src or '#import' in src or '#define' in src:
        raise SystemExit('26563 asset shader unexpectedly requires different runtime preprocessing')
    out.mkdir(parents=True,exist_ok=True)
    files={
      'adaptive_color_appearance_26563.vert':VERTEX,
      'adaptive_color_appearance_26563.frag':runtime_fragment(src),
    }
    for name,s in files.items(): (out/name).write_bytes(s.encode())
    for name in sorted(files):
        b=(out/name).read_bytes(); print(f'{name}\t{len(b.splitlines())} lines\t{hashlib.sha256(b).hexdigest()}')

def self_test():
    sample='precision highp float;\nout vec3 Output;\nvoid main(){Output=vec3(1.0);}\n'
    f=runtime_fragment(sample)
    assert f.startswith('#version 310 es\n\n#line 1\nprecision highp float;')
    assert f.endswith('}\n')
    assert VERTEX=='#version 310 es\nprecision mediump float;\nin vec4 vPosition;\nvoid main() {\ngl_Position = vPosition;\n}\n'
    print('PASS 26563 exact GLInterface runtime-expansion self-test')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--root',type=Path); ap.add_argument('--out',type=Path); a=ap.parse_args()
    if a.self_test: return self_test()
    if not a.root or not a.out: raise SystemExit('--root and --out required')
    extract(a.root,a.out)
if __name__=='__main__': main()
