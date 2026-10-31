#!/usr/bin/env python3
"""Compile the exact three modified runtime GLES shader units with pinned real glslang.
Static-only result is NOT a real compiler PASS.
"""
import argparse,hashlib,pathlib,re,subprocess
p=argparse.ArgumentParser(allow_abbrev=False)
p.add_argument('candidate',type=pathlib.Path)
p.add_argument('--compiler')
p.add_argument('--out',type=pathlib.Path)
a=p.parse_args()
assert bool(a.compiler)==bool(a.out),'real tool needs --compiler and --out together'
app=a.candidate/'app'
paths=['motionv2/render.glsl','motionv2/local_laplacian_global_log_26621.glsl','motionv2/gainmap.glsl']
# Exact GLInterface's source-level prefix, 26889 compiled source preserved.
gl=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java').read_text()
assert '#line 1' in gl
prog=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
assert 'glVersion = "#version 310 es' in prog
reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine highp mediump lowp precision in out inout const struct if else do while switch case default for return discard break continue asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource namespace using'.split())
out=a.out or pathlib.Path('/tmp/26890_glsl_source_only')
if a.out:out.mkdir(parents=True,exist_ok=True)
for n in paths:
 f=app/'src/main/assets/shaders'/n
 s=f.read_text();assert '#version' not in s and '#include' not in s and s.count('{')==s.count('}')
 assert 'IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE' in s
 assert 'uniform /* IRIS_26890' not in s, 'invalid GLSL insertion inside uniform declaration'
 assert s.index('uniform float iris26623ToneBroadNearFraction;') < s.index('/* IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE'), 'tone helper must follow shader uniforms'
 assert s.count('uniform int iris26890BToeEnabled;')==1
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 pat=r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D)\s+([A-Za-z_][A-Za-z0-9_]*)'
 names=re.findall(pat,code)
 assert not (set(names)&reserved),('GLSL reserved',n,set(names)&reserved)
 assert not any(k.startswith('gl_') or '__' in k for k in names),('GLSL illegal identifiers',n)
 full='#version 310 es\n#line 1\n'+s
 if a.compiler:
  dest=out/(pathlib.Path(n).stem+'.frag');dest.write_text(full)
  cp=subprocess.run([str(a.compiler),'-S','frag',str(dest)],capture_output=True,text=True)
  assert cp.returncode==0,('real 26890 GLSL compilation failed',n,cp.stdout,cp.stderr)
 print('PASS 26890 runtime-expanded GLES310 source',n,'SHA',hashlib.sha256(full.encode()).hexdigest(),
       'REAL_PINNED_GLSLANG='+('PASS' if a.compiler else 'NOT RUN'))
if a.compiler:
 print('PASS 26890 all THREE current exact runtime-expanded GLES fragment programs REAL PINNED COMPILE')
else:print('PASS 26890 3 shaders source declaration/reserved scan; real pinned GLSL NOT RUN')
