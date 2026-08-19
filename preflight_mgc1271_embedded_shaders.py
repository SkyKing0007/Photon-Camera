#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,tempfile
from pathlib import Path

SOURCES=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcStrengthReadbackShaders.kt',
]
TRIPLE=re.compile(r'(?:(?:const\s+)?val)\s+(\w+)\s*(?::\s*String)?\s*=\s*"""(.*?)"""(?:\.trimIndent\(\))?',re.S)

def trim_indent(s:str)->str:
    lines=s.splitlines()
    if lines and not lines[0].strip(): lines=lines[1:]
    if lines and not lines[-1].strip(): lines=lines[:-1]
    non=[len(x)-len(x.lstrip()) for x in lines if x.strip()]
    n=min(non) if non else 0
    return '\n'.join(x[n:] if len(x)>=n else '' for x in lines)+'\n'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True,type=Path); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    total=0
    with tempfile.TemporaryDirectory(prefix='mgc1271_glsl_') as td:
        td=Path(td)
        for rel in SOURCES:
            p=a.root/rel; text=p.read_text()
            found=0
            for m in TRIPLE.finditer(text):
                name,body=m.group(1),trim_indent(m.group(2))
                if '#version ' not in body: continue
                # Upstream shader sources are intended to be complete runtime programs. Refuse
                # unresolved Kotlin interpolation rather than validating a different shader.
                if '${' in body:
                    raise SystemExit(f'unresolved Kotlin interpolation in shader {rel}:{name}')
                stage='comp' if re.search(r'layout\s*\(\s*local_size_',body) else 'frag'
                f=td/f'{Path(rel).stem}_{name}.{stage}'
                f.write_text(body)
                subprocess.run([a.validator,'-S',stage,str(f)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                found+=1; total+=1
            if found==0: raise SystemExit(f'no complete embedded GLSL programs found in {rel}')
            print(f'PASS: {rel} embedded GLSL programs={found}')
        # Runtime fullscreen vertex source is generated from fragment version and is fixed.
        for version in (300,310):
            body=f'''#version {version} es\nprecision highp float;\nout vec2 vTexCoord;\nvoid main() {{\n vec2 positions[3]=vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));\n vec2 texCoords[3]=vec2[3](vec2(0.0,0.0),vec2(2.0,0.0),vec2(0.0,2.0));\n gl_Position=vec4(positions[gl_VertexID],0.0,1.0); vTexCoord=texCoords[gl_VertexID];\n}}\n'''
            f=td/f'fullscreen_{version}.vert'; f.write_text(body)
            subprocess.run([a.validator,'-S','vert',str(f)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); total+=1
    print(f'PASS: glslang compiled {total} pinned MGC 1.27.1 runtime shader programs')
if __name__=='__main__': main()
