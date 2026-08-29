#!/usr/bin/env python3
from pathlib import Path
import argparse,re,textwrap,hashlib

def trim_indent(s: str) -> str:
    # Kotlin trimIndent(): drop leading/trailing blank line then remove minimum common indentation.
    lines=s.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    nonblank=[len(x)-len(x.lstrip()) for x in lines if x.strip()]
    n=min(nonblank) if nonblank else 0
    return '\n'.join((x[n:] if len(x)>=n else '') for x in lines)

def extract_literal(path: Path, name: str) -> str:
    s=path.read_text()
    m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
    if not m: raise SystemExit(f'missing exact Kotlin literal {name} in {path}')
    raw=m.group(1)
    if '${' in raw or re.search(r'(?<!\\)\$[A-Za-z_]',raw):
        raise SystemExit(f'{name} contains Kotlin interpolation; extractor must expand it exactly')
    return trim_indent(raw)

def vertex_for(fragment: str) -> str:
    m=re.search(r'^\s*#version\s+(300|310)\s+es\s*$',fragment,re.M)
    if not m: raise SystemExit('fragment GLSL ES version missing/unsupported')
    version=m.group(1)
    return trim_indent(f'''\n            #version {version} es
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

def write_exact(p:Path,s:str):
    p.write_bytes(s.encode())

def extract(root:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    sabre=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
    vgn=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    shaders={
      'sabre_super_res_detail_merge_26561.frag':extract_literal(sabre,'superResDetailMerge26561'),
      'sabre_super_res_detail_resolve_26561.frag':extract_literal(sabre,'superResDetailResolve26561'),
      'universal_adaptive_color_26561.comp':extract_literal(vgn,'universalAdaptiveColor26561'),
      'sabre_super_res_linear_raw_26562.frag':extract_literal(sabre,'superResLinearRaw26562'),
    }
    shaders['sabre_super_res_detail_merge_26561.vert']=vertex_for(shaders['sabre_super_res_detail_merge_26561.frag'])
    shaders['sabre_super_res_detail_resolve_26561.vert']=vertex_for(shaders['sabre_super_res_detail_resolve_26561.frag'])
    shaders['sabre_super_res_linear_raw_26562.vert']=vertex_for(shaders['sabre_super_res_linear_raw_26562.frag'])
    for name,src in shaders.items(): write_exact(out/name,src)
    for name in sorted(shaders):
        data=(out/name).read_bytes(); print(f'{name}\t{len(data.splitlines())} lines\t{hashlib.sha256(data).hexdigest()}')

def self_test():
    assert trim_indent('\n    a\n      b\n    ')=='a\n  b'
    f='#version 300 es\nprecision highp float;\nvoid main(){}'
    v=vertex_for(f)
    assert v.startswith('#version 300 es\nprecision highp float;') and 'gl_VertexID' in v
    print('PASS 26562 extractor self-test: Kotlin trimIndent + exact generated fullscreen vertex contract')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');ap.add_argument('--root',type=Path);ap.add_argument('--out',type=Path)
    a=ap.parse_args()
    if a.self_test: return self_test()
    if not a.root or not a.out: raise SystemExit('--root and --out required')
    extract(a.root,a.out)
if __name__=='__main__':main()
