#!/usr/bin/env python3
"""All modified runtime-expanded ESSL 310 fragment shader source + pinned real glslang."""
from pathlib import Path
import argparse,hashlib,re,subprocess
p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('candidate',type=Path)
p.add_argument('--compiler');p.add_argument('--out',type=Path)
a=p.parse_args();assert bool(a.compiler)==bool(a.out),'compiler+out must be supplied together'
app=a.candidate/'app'
gl=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java').read_text()
prog=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
assert '#line 1' in gl and 'glVersion = "#version 310 es' in prog
out=a.out or Path('/tmp/26892_sdr_preview_static_only')
if a.out:out.mkdir(parents=True,exist_ok=True)
reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine highp mediump lowp precision in out inout const struct if else do while switch case default for return discard break continue asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource namespace using'.split())
for n in ('render.glsl','gainmap.glsl'):
 s=(app/'src/main/assets/shaders/motionv2'/n).read_text()
 assert '#version' not in s and '#include' not in s and s.count('{')==s.count('}')
 assert s.count('/* IRIS_26892_SCENE_ADAPTIVE_SDR_FINISH')==1
 assert 'iris26892SdrAdaptiveGuide' in s
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 pat=r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D)\s+([A-Za-z_][A-Za-z0-9_]*)'
 names=re.findall(pat,code)
 assert not(set(names)&reserved),('GLSL reserved',n,set(names)&reserved)
 assert not any(k.startswith('gl_') or '__' in k for k in names),('bad GLSL identifiers',n)
 full='#version 310 es\n#line 1\n'+s
 if a.compiler:
  dest=out/(Path(n).stem+'.frag');dest.write_text(full)
  cp=subprocess.run([str(a.compiler),'-S','frag',str(dest)],capture_output=True,text=True)
  assert cp.returncode==0,('pinned REAL GLSL compile failed',n,cp.stdout,cp.stderr)
 print('PASS 26892 runtime-expanded ESSL source',n,'sha256='+hashlib.sha256(full.encode()).hexdigest(),'PINNED_COMPILE='+('PASS' if a.compiler else 'NOT RUN'))
print('PASS 26892 TWO exact changed render+gainmap ESSL310 programs; REAL PINNED COMPILE '+('PASS' if a.compiler else 'NOT RUN'))
