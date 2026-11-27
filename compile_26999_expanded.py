#!/usr/bin/env python3
import pathlib,subprocess,hashlib,tempfile,sys,os
from verify_26999_v6_current_glsl import lexical_check
R=pathlib.Path(__file__).resolve().parent; OUT=R/'photon_26999_outputs';OUT.mkdir(exist_ok=True)
compiler=next(p for p in (R/'.photon_26904_incremental_work/real_shader_tools/glslang').rglob('*') if p.is_file() and p.name in ('glslang','glslangValidator'))
assert '16.5.0' in subprocess.check_output([str(compiler),'--version'],text=True)
log=OUT/'26999_EXPANDED_REAL_GLSL_SPIRV.txt'
with tempfile.TemporaryDirectory(prefix='26999-expanded-') as td,log.open('w') as out:
 t=pathlib.Path(td);srcdir=t/'expanded'
 def run(*cmd):
  cmd=list(map(str,cmd));out.write('RUN '+' '.join(cmd)+'\n');out.flush();subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 run('kotlinc',R/'Emit26999.kt',*[R/p for p in (R/'26999_SHADER_KOTLIN_FILES.txt').read_text().splitlines()],'-include-runtime','-d',t/'emit.jar')
 run('java','-jar',t/'emit.jar',srcdir,*(R/'26999_SHADER_OBJECTS.txt').read_text().splitlines())
 want=dict((p,h) for h,p in (l.split('  ',1) for l in (R/'26999_EXPANDED_SHADER.sha256').read_text().splitlines()));got={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in srcdir.iterdir()};assert got==want
 for tool in (compiler,'spirv-opt','spirv-val'):run(tool,'--version')
 for p in sorted(srcdir.iterdir()):
  stage=p.suffix[1:];assert stage in ('vert','frag','comp');s=p.read_text();lexical_check(s,p.name);run(compiler,'-S',stage,p)
  converted=t/('converted.'+p.name);converted.write_text(s.replace('#version 300 es','#version 310 es',1));run(compiler,'-S',stage,converted)
  spv=t/(p.name+'.spv');opt=t/(p.name+'.opt.spv');run(compiler,'-G','--auto-map-locations','--auto-map-bindings','-S',stage,'-o',spv,converted);run('spirv-val','--target-env','opengl4.5',spv);run('spirv-opt','--target-env=opengl4.5','-O',spv,'-o',opt);run('spirv-val','--target-env','opengl4.5',opt)
  if stage=='frag':run(compiler,'-l',p.with_suffix('.vert'),p)
 out.write('PASS 26999 exact expanded donor shader GLSL/SPIR-V compile/opt/val and pair link\n')
print(log.read_text().splitlines()[-1])
