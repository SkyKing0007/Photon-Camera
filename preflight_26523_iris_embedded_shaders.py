#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,tempfile
from pathlib import Path
SOURCE='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
TRIPLE=re.compile(r'(?:(?:const\s+)?val)\s+(\w+)\s*(?::\s*String)?\s*=\s*"""(.*?)"""(?:\.trimIndent\(\))?',re.S)
def trim_indent(s:str)->str:
    lines=s.splitlines()
    if lines and not lines[0].strip(): lines=lines[1:]
    if lines and not lines[-1].strip(): lines=lines[:-1]
    non=[len(x)-len(x.lstrip()) for x in lines if x.strip()]; n=min(non) if non else 0
    return '\n'.join(x[n:] if len(x)>=n else '' for x in lines)+'\n'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True,type=Path); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    p=a.root/SOURCE
    if not p.is_file(): raise SystemExit('missing Iris embedded shader source')
    text=p.read_text()
    for marker in ('IRIS_26521_V4_DIRECTIONAL_GREEN','IRIS_26521_V4_ROBUST_SPATIAL_KERNEL','IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE','IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT','IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE','IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS','IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8'):
        if text.count(marker)!=1: raise SystemExit(f'{marker} count={text.count(marker)} expected=1')
    for old in ('IRIS_26522_DNG_EFFECTIVE_SUPPORT_ACCUMULATOR','IRIS_26522_DNG_EFFECTIVE_SUPPORT_Q8'):
        if old in text: raise SystemExit('obsolete 26522 support marker survived: '+old)
    m=re.search(r'val\s+convertBayerAlignment\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    if not m: raise SystemExit('convertBayerAlignment missing')
    for tok in ('vec2 resampledFlow(vec2 sourceGrid)','vec2 flow = resampledFlow(sourceGrid)','mix(flow00, flow10, fraction.x)'):
        if tok not in m.group(1): raise SystemExit('continuous transport token missing '+tok)
    for tok in ('cancelInterpolation','uInterpolationFlowTolerance','uAlignmentToBayerQuads'):
        if tok in m.group(1): raise SystemExit('coarse-grid/legacy transport token '+tok)
    total=0
    with tempfile.TemporaryDirectory(prefix='iris26523_glsl_') as td:
        td=Path(td)
        for mat in TRIPLE.finditer(text):
            name,body=mat.group(1),trim_indent(mat.group(2))
            if '#version ' not in body: continue
            if '${' in body: raise SystemExit(f'unresolved Kotlin interpolation in {name}')
            stage='comp' if re.search(r'layout\s*\(\s*local_size_',body) else 'frag'
            f=td/f'{name}.{stage}'; f.write_text(body)
            cp=subprocess.run([a.validator,'-S',stage,str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if cp.returncode!=0:
                print(cp.stdout); raise SystemExit(f'glslang failed {name}')
            total+=1
        if total==0: raise SystemExit('no embedded GLSL programs found')
        for version in (300,310):
            body='#version %d es\nprecision highp float;\nout vec2 vTexCoord;\nvoid main(){ vec2 p[3]=vec2[3](vec2(-1.),vec2(3.,-1.),vec2(-1.,3.)); vec2 t[3]=vec2[3](vec2(0.),vec2(2.,0.),vec2(0.,2.)); gl_Position=vec4(p[gl_VertexID],0.,1.); vTexCoord=t[gl_VertexID]; }\n' % version
            f=td/f'fullscreen_{version}.vert'; f.write_text(body)
            cp=subprocess.run([a.validator,'-S','vert',str(f)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if cp.returncode!=0:
                print(cp.stdout); raise SystemExit('fullscreen vertex failed')
            total+=1
    print(f'PASS: glslang compiled {total} Iris26523 embedded runtime shader programs')
if __name__=='__main__': main()
