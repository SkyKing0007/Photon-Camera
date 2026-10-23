#!/usr/bin/env python3
"""Compile each exact 26871 runtime-expanded 300/310 shader with pinned real glslang."""
from pathlib import Path
import argparse,hashlib,re,subprocess
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
app=a.candidate/'app';out=a.out;out.mkdir(parents=True,exist_ok=True)
ktgpu=(app/'src/main/java/com/hinnka/mycamera/processor/GlesIris26870GpuSharpest.kt').read_text()
ktc=(app/'src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
asset=(app/'src/main/assets/shaders/motionv2/iris_tone_controls.glsl').read_text()
def extract(s,pattern,name):
 m=re.search(pattern,s,re.S);assert m,('missing exact Kotlin runtime shader',name)
 src=m.group(1);assert src.count('#version')==1 and src.lstrip().startswith('#version 300 es'),name
 return src
units={
 'iris_tone_controls': '#version 310 es\n\n#line 1\n'+asset,
 'iris_26870_gpu_reference.vert':extract(ktgpu,r'private val vertex\s*=\s*"""(.*?)"""\.trimIndent\(\)','gpu vertex'),
 'iris_26870_gpu_reference.frag':extract(ktgpu,r'private val fragment\s*=\s*"""(.*?)"""\.trimIndent\(\)','gpu fragment'),
 'iris_26870_post_amaze_chroma':extract(ktc,r'val shader\s*=\s*"""(.*?)"""\.trimIndent\(\)','post AMaZE'),
}
assert 'glVersion = "#version 310 es' in (app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
assert '#line 1' in (app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java').read_text()
assert '#version' not in asset and '#line' not in asset
reserved=set('attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise subroutine highp mediump lowp precision in out inout uniform const struct asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource superp cast sizeof namespace using switch default case break continue return discard'.split())
reserved|={'input','output','filter','sample','double','sampler1D','sampler3D','sampler2DArray','samplerCube','sampler2DShadow','samplerCubeShadow'}
pat=re.compile(r'\b(?:const\s+)?(?:highp\s+|mediump\s+|lowp\s+)?(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|usampler2D)\s+([A-Za-z_]\w*)')
for failed in ('float coherent=0.1;', 'vec2 fixed=vec2(0.0);'):
 assert set(pat.findall(failed))&reserved,('lost historical reserved-identifier regression',failed)
assert 'IRIS_26871_B_MULTISCALE_CHROMA' in ktc
for n,src in units.items():
 assert src.count('#version')==1 and src.count('{')==src.count('}'),n
 names=pat.findall(src);assert not set(names)&reserved,(n,'GLSL reserved',set(names)&reserved)
 suffix='.vert' if n.endswith('.vert') else '.frag'
 f=out/(n+('' if n.endswith(suffix) else suffix));f.write_text(src)
 if a.compiler:
  compiler=Path(a.compiler);assert compiler.is_file() and compiler.stat().st_size>0
  res=subprocess.run([str(compiler),'-S',('vert' if suffix=='.vert' else 'frag'),str(f)],capture_output=True,text=True)
  assert res.returncode==0,(n,res.stdout,res.stderr)
 print('PASS 26871 exact runtime-expanded',n,'sha256='+hashlib.sha256(src.encode()).hexdigest(),
       'GLSL identifier scan PASS','pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
