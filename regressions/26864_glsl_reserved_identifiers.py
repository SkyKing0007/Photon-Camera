#!/usr/bin/env python3
"""Permanent 26864 regression for illegal Vulkan-GLSL shader local identifiers.

This lexical gate is additive. It NEVER substitutes for the inherited
pinned real glslangValidator on runtime-expanded shader source.
"""
from pathlib import Path
import argparse
import re

RESERVED = {
    'packed','common','partition','active','asm','class','union','enum',
    'typedef','template','this','resource','goto','inline','noinline',
    'public','static','extern','external','interface','long','short',
    'half','fixed','unsigned','superp','input','output','filter',
    'sizeof','cast','namespace','using','sampler3DRect','row_major',
}
DECL = re.compile(
    r'\b(?:const\s+)?(?:highp\s+|mediump\s+|lowp\s+)?'
    r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|'
    r'bvec[234]|mat[234]|image2D|uimage2D|sampler2D)\s+'
    r'([A-Za-z_]\w*)\s*(?:[;=,\[])'
)

def bad_declarations(source: str) -> set[str]:
    source = re.sub(r'//[^\n]*|/\*.*?\*/', '', source, flags=re.S)
    return {s for s in DECL.findall(source) if s in RESERVED or s.startswith('gl_')}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('app_source_root', type=Path)
    args = ap.parse_args()
    root = args.app_source_root
    shaders = sorted((root/'src/main/cpp/iris26864').rglob('*.comp'))
    shaders += sorted((root/'src/main/cpp/iris26864/vendor/rawr/native').rglob('*.glsl'))
    assert shaders, '26864 shader universe absent'
    for shader in shaders:
        bad=bad_declarations(shader.read_text())
        assert not bad, f'{shader}: reserved shader identifiers: {sorted(bad)}'
    # Exact historic failure mode, not an unrelated artificial shader fixture.
    assert bad_declarations('void main() { vec4 packed=vec4(0.0); packed.r=1.0; }') == {'packed'}
    assert bad_declarations('void main() { uint packed=imageLoad(tex,ivec2(0)).r; }') == {'packed'}
    assert not bad_declarations('void main() { vec4 packedCfaCell=vec4(0.0); uint packedClipBits=0u; }')
    print(f'PASS 26864 GLSL reserved-identifier regression: {len(shaders)} shader source files; exact historical failing declarations rejected')

if __name__=='__main__':
    main()
