#!/usr/bin/env python3
"""Exact runtime OES ESSL300 preview stage compile and link; external OES is GLES only."""
from pathlib import Path
import argparse,hashlib,importlib.util,subprocess,tempfile
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--audit',action='store_true');p.add_argument('--compile',action='store_true');o=p.parse_args();assert o.audit!=o.compile
spec=importlib.util.spec_from_file_location('identifier',R/'verify_26989_v6_current_glsl.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
root=R/'app/src/main/assets/shaders/preview';manifest={name:h for h,name in (x.split('  ',1) for x in (R/'26989_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
shader={}
for src,stage in [('main_vs.glsl','vert'),('main_fs.glsl','frag')]:
 f=root/src;data=f.read_bytes();assert hashlib.sha256(data).hexdigest()==manifest[f.relative_to(R).as_posix()]
 text='#version 300 es\n #line 1\n'+data.decode();a.lexical_check(text,str(f));shader[stage]=text
r=(R/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
assert 'return "#version 300 es";' in r and r.count('SupportedVersion + "\\n #line 1\\n"')==2
print('PASS exact runtime preview shader SHA and reserved identifier audit; OES ESSL300, no synthetic SPIR-V claim')
if o.compile:
 tools=R/'.photon_26904_incremental_work/real_shader_tools/glslang';compiler=next(x for x in tools.rglob('*') if x.is_file() and x.name in ('glslang','glslangValidator'))
 assert '16.5.0' in subprocess.check_output([str(compiler),'--version'],text=True)
 out=R/'photon_26989_outputs';out.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as td,(out/'26989_PREVIEW_REAL_GLSL.txt').open('w') as log:
  files=[]
  for stage,text in shader.items():
   f=Path(td)/('preview.'+stage);f.write_text(text);files.append(str(f));log.write(hashlib.sha256(f.read_bytes()).hexdigest()+' '+f.name+'\n');subprocess.run([str(compiler),'-S',stage,str(f)],stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run([str(compiler),'-l',*files],stdout=log,stderr=subprocess.STDOUT,check=True)
  log.write('PASS exact 26989 runtime ESSL300 OES preview pair compile/link\n')
 print('PASS exact 26989 runtime ESSL300 OES preview pair compile/link')
