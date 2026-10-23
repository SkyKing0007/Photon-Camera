#!/usr/bin/env python3
"""Exact expanded GL preview vertex/fragment and embedded OES measurement shaders."""
from pathlib import Path
import argparse,hashlib,re,ast,subprocess
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
app=a.candidate/'app';out=a.out;out.mkdir(parents=True,exist_ok=True)
main=(app/'src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
shader=(app/'src/main/assets/shaders/preview/main_fs.glsl').read_text()
vs=(app/'src/main/assets/shaders/preview/main_vs.glsl').read_text()
assert 'IRIS_26872_B_DISPLAY_ONLY' in shader and 'IRIS_26872_PREVIEW_FLICKER_GL_OWNER' in main
assert shader.count('uniform vec4 iris26872PreviewStripe;')==1
assert '#version' not in shader and '#version' not in vs
m=re.search(r'String vs = ("(?:\\.|[^"\\])*");\s*String fs =\s*((?:"(?:\\.|[^"\\])*"\s*\+\s*)*"(?:\\.|[^"\\])*");',main,re.S)
assert m,'cannot reconstruct exact runtime embedded OES probe GLSL'
probe_vs=ast.literal_eval(m.group(1))
probe_fs=''.join(ast.literal_eval(x) for x in re.findall(r'"(?:\\.|[^"\\])*"',m.group(2)))
assert probe_fs.startswith('#extension GL_OES_EGL_image_external_essl3 : require\n')
assert 'vec2(12.0,96.0)' in probe_fs
units={
 'iris_26872_preview_main.vert':'#version 300 es\n#line 1\n'+vs,
 'iris_26872_preview_main.frag':'#version 300 es\n#line 1\n'+shader,
 'iris_26872_probe.vert':'#version 300 es\n#line 1\n'+probe_vs,
 'iris_26872_probe.frag':'#version 300 es\n#line 1\n'+probe_fs,
}
reserved=set('attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise subroutine highp mediump lowp precision in out inout uniform const struct asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource superp cast sizeof namespace using switch default case break continue return discard'.split())
reserved|={'input','output','filter','sample','double','sampler1D','sampler3D','sampler2DArray','samplerCube','sampler2DShadow','samplerCubeShadow'}
pat=re.compile(r'\b(?:const\s+)?(?:highp\s+|mediump\s+|lowp\s+)?(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|usampler2D)\s+([A-Za-z_]\w*)')
for sample in ('float coherent=0.1;','vec2 fixed=vec2(0.0);'):
 assert set(pat.findall(sample))&reserved
for name,source in units.items():
 assert source.count('#version')==1 and source.count('{')==source.count('}'),name
 bad=set(pat.findall(source))&reserved;assert not bad,(name,'GLSL reserved identifier',bad)
 f=out/name;f.write_text(source)
 if a.compiler:
  compiler=Path(a.compiler);assert compiler.is_file() and compiler.stat().st_size>0
  res=subprocess.run([str(compiler),'-S',('vert' if name.endswith('.vert') else 'frag'),str(f)],capture_output=True,text=True)
  assert res.returncode==0,(name,res.stdout,res.stderr)
 print('PASS 26872 runtime-expanded preview shader',name,'sha256='+hashlib.sha256(source.encode()).hexdigest(),
       'GLSL reserved scan PASS','pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
