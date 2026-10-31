#!/usr/bin/env python3
"""Compile exact runtime-expanded GLES310 THREE 26889-reverted tone shaders.
Copied compile strategy from successful 26890 verifier; with the new candidate's
26889 owner bytes and without any rejected editor toe marker.
"""
import argparse,hashlib,pathlib,re,subprocess
p=argparse.ArgumentParser(allow_abbrev=False)
p.add_argument('candidate',type=pathlib.Path)
p.add_argument('--compiler');p.add_argument('--out',type=pathlib.Path)
a=p.parse_args();assert bool(a.compiler)==bool(a.out)
app=a.candidate/'app'; paths=['motionv2/render.glsl','motionv2/local_laplacian_global_log_26621.glsl','motionv2/gainmap.glsl']
gl=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java').read_text()
assert '#line 1' in gl
prog=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
assert 'glVersion = "#version 310 es' in prog
reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine highp mediump lowp precision in out inout const struct if else do while switch case default for return discard break continue asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource namespace using'.split())
out=a.out or pathlib.Path('/tmp/26891_reverted_tone_source_only')
if a.out:out.mkdir(parents=True,exist_ok=True)
for n in paths:
 s=(app/'src/main/assets/shaders'/n).read_text()
 assert '#version' not in s and '#include' not in s and s.count('{')==s.count('}')
 assert 'IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE' not in s
 assert 'iris26890BToeEnabled' not in s
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 pat=r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D)\s+([A-Za-z_][A-Za-z0-9_]*)'
 names=re.findall(pat,code)
 assert not(set(names)&reserved),('GLSL reserved',n,set(names)&reserved)
 assert not any(k.startswith('gl_') or '__' in k for k in names),('bad GLSL identifiers',n)
 full='#version 310 es\n#line 1\n'+s
 if a.compiler:
  dest=out/(pathlib.Path(n).stem+'.frag');dest.write_text(full)
  cp=subprocess.run([str(a.compiler),'-S','frag',str(dest)],capture_output=True,text=True)
  assert cp.returncode==0,('real pin GLSL failed',n,cp.stdout,cp.stderr)
 print('PASS 26891 exact runtime-expanded reverted 26889 shader',n,'SHA',hashlib.sha256(full.encode()).hexdigest(),'REAL_PINNED_GLSLANG='+('PASS' if a.compiler else 'NOT RUN'))
if a.compiler:print('PASS 26891 THREE current reverted 26889 tone GLES310 REAL PINNED COMPILE')
else:print('PASS 26891 THREE current reverted tone GLES310 source; REAL COMPILER NOT RUN')
