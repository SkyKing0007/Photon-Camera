#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,tempfile
from pathlib import Path

SOURCE='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'
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
    p=a.root/SOURCE
    if not p.is_file(): raise SystemExit('missing released embedded shader source: '+str(p))
    text=p.read_text()
    if text.count('IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT')!=1:
        raise SystemExit('continuous finest-LK marker cardinality mismatch')
    m=re.search(r'val\s+convertBayerAlignment\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    if not m: raise SystemExit('convertBayerAlignment shader missing')
    block=m.group(1)
    for tok in ('vec2 resampledFlow(vec2 sourceGrid)','vec2 flow = resampledFlow(sourceGrid)','mix(flow00, flow10, fraction.x)'):
        if tok not in block: raise SystemExit('continuous transport token missing: '+tok)
    for tok in ('cancelInterpolation','uInterpolationFlowTolerance','uAlignmentToBayerQuads'):
        if tok in block: raise SystemExit('forbidden coarse-grid gate/legacy transport token: '+tok)
    merge=re.search(r'val\s+mergeBayer\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    if not merge or 'cancelInterpolation' not in merge.group(1):
        raise SystemExit('native merge-domain discontinuity gate missing')
    total=0
    with tempfile.TemporaryDirectory(prefix='iris26520_glsl_') as td:
        td=Path(td)
        for mat in TRIPLE.finditer(text):
            name,body=mat.group(1),trim_indent(mat.group(2))
            if '#version ' not in body: continue
            if '${' in body: raise SystemExit(f'unresolved Kotlin interpolation in shader {SOURCE}:{name}')
            stage='comp' if re.search(r'layout\s*\(\s*local_size_',body) else 'frag'
            f=td/f'{name}.{stage}'; f.write_text(body)
            cp=subprocess.run([a.validator,'-S',stage,str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if cp.returncode!=0:
                print(cp.stdout); raise SystemExit(f'glslang failed {SOURCE}:{name}')
            total+=1
        if total==0: raise SystemExit('no complete embedded GLSL programs found')
        for version in (300,310):
            body=f'''#version {version} es\nprecision highp float;\nout vec2 vTexCoord;\nvoid main() {{\n vec2 positions[3]=vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));\n vec2 texCoords[3]=vec2[3](vec2(0.0,0.0),vec2(2.0,0.0),vec2(0.0,2.0));\n gl_Position=vec4(positions[gl_VertexID],0.0,1.0); vTexCoord=texCoords[gl_VertexID];\n}}\n'''
            f=td/f'fullscreen_{version}.vert'; f.write_text(body)
            cp=subprocess.run([a.validator,'-S','vert',str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if cp.returncode!=0:
                print(cp.stdout); raise SystemExit(f'glslang failed fullscreen vertex {version}')
            total+=1
    print(f'PASS: glslang compiled {total} released 26520 V5 embedded runtime shader programs')

if __name__=='__main__': main()
