#!/usr/bin/env python3
import pathlib,subprocess,re,textwrap,hashlib,tempfile
R=pathlib.Path(__file__).resolve().parent;K=R/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129';OUT=R/'photon_26994_outputs';OUT.mkdir(exist_ok=True)
def literal(f,n):
 m=re.search(r'\bval '+n+r' = """\n(.*?)\n\s*"""\.trimIndent\(\)',f.read_text(),re.S);assert m,(f,n);return textwrap.dedent(m.group(1))
vert=literal(K/'raw/RawFullscreenQuad.kt','VERTEX_SHADER');frag=literal(K/'raw/RawAdjustmentPass.kt','FRAGMENT_SHADER').replace('${ShadowsHighlightsShader.GLSL}',literal(K/'lut/ShadowsHighlightsShader.kt','GLSL'));assert '${' not in frag
compiler=next(p for p in (R/'.photon_26904_incremental_work/real_shader_tools/glslang').rglob('*') if p.is_file() and p.name in ('glslang','glslangValidator'))
assert '16.5.0' in subprocess.check_output([str(compiler),'--version'],text=True)
log=OUT/'26994_SHADOW_REAL_GLSL_SPIRV.txt'
with tempfile.TemporaryDirectory(prefix='26994-shadow-real-') as td,log.open('w') as out:
 t=pathlib.Path(td);files=[]
 def run(*cmd):
  cmd=list(map(str,cmd));out.write('RUN '+' '.join(cmd)+'\n');out.flush();subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,check=True)
 for tool in (compiler,'spirv-opt','spirv-val'):run(tool,'--version')
 for stage,source in [('vert',vert),('frag',frag)]:
  src=t/f'shadow.{stage}';src.write_text(source+'\n');files.append(src);out.write(hashlib.sha256(src.read_bytes()).hexdigest()+' '+src.name+'\n');run(compiler,'-S',stage,src)
  converted=t/f'shadow310.{stage}';converted.write_text(src.read_text().replace('#version 300 es','#version 310 es',1));run(compiler,'-S',stage,converted)
  spv=t/f'shadow.{stage}.spv';opt=t/f'shadow.{stage}.opt.spv';run(compiler,'-G','--auto-map-locations','--auto-map-bindings','-S',stage,'-o',spv,converted);run('spirv-val','--target-env','opengl4.5',spv);run('spirv-opt','--target-env=opengl4.5','-O',spv,'-o',opt);run('spirv-val','--target-env','opengl4.5',opt)
  out.write(hashlib.sha256(spv.read_bytes()).hexdigest()+' '+hashlib.sha256(opt.read_bytes()).hexdigest()+'\n')
 run(compiler,'-l',*files);out.write('PASS 26994 expanded RAW adjustment pair original/310 GLSL and SPIR-V opt/val\n')
print(log.read_text().splitlines()[-1])
