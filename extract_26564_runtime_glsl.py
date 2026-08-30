#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re

def trim_indent(s:str)->str:
    lines=s.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    inds=[len(x)-len(x.lstrip(' \t')) for x in lines if x.strip()]
    n=min(inds) if inds else 0
    return '\n'.join(x[n:] if x.strip() else '' for x in lines)

def get_val(src:str,name:str)->str:
    m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S)
    if not m: raise SystemExit(f'missing shader string {name}')
    return trim_indent(m.group(1))

def vertex_for(frag:str)->str:
    m=re.search(r'^\s*#version\s+(300|310)\s+es\s*$',frag,re.M)
    if not m: raise SystemExit('runtime fragment missing supported #version 300/310 es')
    v=m.group(1)
    return trim_indent(f'''\n        #version {v} es
        precision highp float;
        out vec2 vTexCoord;
        void main() {{
            vec2 positions[3] = vec2[3](
                vec2(-1.0, -1.0),
                vec2( 3.0, -1.0),
                vec2(-1.0,  3.0)
            );
            vec2 texCoords[3] = vec2[3](
                vec2(0.0, 0.0),
                vec2(2.0, 0.0),
                vec2(0.0, 2.0)
            );
            gl_Position = vec4(positions[gl_VertexID], 0.0, 1.0);
            vTexCoord = texCoords[gl_VertexID];
        }}
    ''')

def extract(root:Path,out:Path):
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
    src=p.read_text()
    out.mkdir(parents=True,exist_ok=True)
    pairs=[('true2x_merge_26564','true2xMerge26564'),('true2x_resolve_26564','true2xResolve26564')]
    for stem,name in pairs:
        frag=get_val(src,name); vert=vertex_for(frag)
        (out/(stem+'.frag')).write_text(frag)
        (out/(stem+'.vert')).write_text(vert)
    for p in sorted(out.iterdir()):
        b=p.read_bytes(); print(f'{p.name}\t{len(b.splitlines())} lines\t{hashlib.sha256(b).hexdigest()}')

def self_test():
    s='''\n        #version 300 es
        void main() { }
    '''
    assert trim_indent(s)=='#version 300 es\nvoid main() { }'
    v=vertex_for(trim_indent(s)); assert v.startswith('#version 300 es\nprecision highp float;') and v.endswith('}')
    print('PASS 26564 runtime GLSL extraction self-test')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--root',type=Path); ap.add_argument('--out',type=Path); a=ap.parse_args()
    if a.self_test: return self_test()
    if not a.root or not a.out: raise SystemExit('--root and --out required')
    extract(a.root,a.out)
if __name__=='__main__': main()
