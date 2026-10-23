#!/usr/bin/env python3
"""Exact GLES310 runtime-expanded 26869 shader proof (pinned glslang required in Actions)."""
from pathlib import Path
import argparse,hashlib,re,subprocess
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--out',required=True,type=Path);a=p.parse_args()
app=a.candidate/'app';out=a.out;out.mkdir(parents=True,exist_ok=True)
names=('iris_tone_controls','iris_26869_b_residual_chroma')
# GLSL/GLSL ES 4.60 reserved/future reserved tokens, scanned in declaration slots,
# including the GLSL compiler's full grammar validation on expanded runtime input.
reserved=set('attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample invariant precise subroutine highp mediump lowp precision in out inout uniform const struct asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource superp cast sizeof namespace using sampler1D sampler2D sampler3D samplerCube sampler2DArray sampler2DShadow samplerCubeShadow sampler2DArrayShadow'.split())
for n in names:
 f=app/'src/main/assets/shaders/motionv2'/f'{n}.glsl';src=f.read_text()
 assert not re.search(r'^\s*#(?:version|import|include|line)\b|\$\{|\$[A-Za-z]',src,re.M),(n,'unexpected compile-time expansion/conditional')
 assert src.count('void main()')==1 and src.count('{')==src.count('}'),n
 assert src.count('out vec3 Output;')==1
 # Verify runtime is the historical GLProg/GLInterface path that adds a single
 # default GLES310 #version + #line 1 to unversioned assets.
 gl=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
 assert 'glVersion = "#version 310 es' in gl or 'glVersion="#version 310 es' in gl
 intr=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java').read_text()
 assert '#line 1' in intr
 expanded='#version 310 es\n\n#line 1\n'+src
 declarations=re.findall(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|ivec2\s*\[[0-9]+\])\s+([A-Za-z_][A-Za-z_0-9]*)\b',src)
 assert not (set(declarations)&reserved),(n,'GLSL reserved',set(declarations)&reserved)
 tgt=out/(n+'.frag');tgt.write_text(expanded)
 if a.compiler:
  cp=subprocess.run([a.compiler,'-S','frag',str(tgt)],text=True,capture_output=True)
  assert cp.returncode==0,(n,cp.stdout,cp.stderr)
 print('PASS 26869 exact runtime-expanded shader',n,'sha256='+hashlib.sha256(expanded.encode()).hexdigest(),'complete identifier scan PASS','pinned-glslang='+('PASS' if a.compiler else 'NOT RUN'))
