#!/usr/bin/env python3
"""26889 exact changed-runtime GLSL source safety and ACTIONS pinned real compilers."""
import argparse,subprocess,sys,hashlib,re,textwrap,pathlib
p=argparse.ArgumentParser(allow_abbrev=False)
p.add_argument('candidate',type=pathlib.Path)
p.add_argument('--compiler');p.add_argument('--spirv-val');p.add_argument('--spirv-opt');p.add_argument('--out',type=pathlib.Path)
a=p.parse_args()
if any((a.compiler,a.spirv_val,a.spirv_opt,a.out)):
 assert all((a.compiler,a.spirv_val,a.spirv_opt,a.out))
root=a.candidate/'app/src/main/cpp/iris26864';bridge=root/'bridge'
shaders=[bridge/'Iris26888BOffHdrqMismatch.comp',bridge/'Iris26887BOffHdrqMerge.comp']
cm=(root/'Iris26864VendorRawr.cmake').read_text()
for name in shaders:
 s=name.read_text()
 assert s.startswith('#version 450\n') and 'void main()' in s and s.count('{')==s.count('}')
 assert name.name in cm,('modified shader not linked to active CMake',name)
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for m in re.finditer(r'\b(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|image2D|void)\s+([A-Za-z_]\w*)',code):
  assert m.group(1) not in ('sample','namespace','output','input','filter','long','short','half','double') and '__' not in m.group(1)
 print('PASS modified B-OFF actual Vulkan GLSL #version 450, declarations and CMake ownership',name.name)
long=(a.candidate/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26868DirectLong.kt').read_text()
m=re.search(r'\bval\s+trustedShadowGainBOffMotionSafe\s*=\s*"""(.*?)"""\.trimIndent\(\)',long,re.S)
assert m and long.count('val trustedShadowGainBOffMotionSafe')==1
fragment=textwrap.dedent(m.group(1)).strip('\n')+'\n'
assert fragment.startswith('#version 300 es\n') and fragment.count('#version')==1
assert 'void main()' in fragment and fragment.count('{')==fragment.count('}')
assert not re.search(r'\b(?:sample|namespace|output|input)\s*(?:=|;|\()',fragment)
assert not re.search(r'\$\{|\$[A-Za-z]|^\s*#(?:include|import|line)\b',fragment,re.M)
print('PASS modified B-OFF LONG actual ESSL300 expansion and reserved-identifier checks')
if a.compiler:
 for tool in (a.compiler,a.spirv_val,a.spirv_opt):
  assert pathlib.Path(tool).is_file(),('missing pinned actual compiler tool',tool)
 a.out.mkdir(parents=True,exist_ok=True)
 f=a.out/'trustedShadowGainBOffMotionSafe.frag';f.write_text(fragment)
 x=subprocess.run([a.compiler,'-S','frag',str(f)],capture_output=True,text=True)
 assert x.returncode==0,(x.stdout,x.stderr)
 adapter=root/'compile_locked_rawr_glslc.py';assert adapter.is_file()
 receipts=[]
 for shader in shaders:
  variants=('prod','trace') if shader.name=='Iris26887BOffHdrqMerge.comp' else ('prod',)
  for variant in variants:
   dest=a.out/(shader.stem+'_'+variant+'.spv')
   flags=['--target-env=vulkan1.1','-O']
   if variant=='trace':flags.append('-DRAWR_PARITY_TRACE=1')
   cmd=[sys.executable,'-S',str(adapter),'--validator='+a.compiler,'--spirv-val='+a.spirv_val,'--spirv-opt='+a.spirv_opt,*flags,str(shader),'-o',str(dest)]
   subprocess.run(cmd,check=True)
   raw=dest.read_bytes();assert len(raw)>80 and raw[:4]==bytes.fromhex('03022307')
   receipts.append(hashlib.sha256(raw).hexdigest()+'  '+dest.name)
 assert len(receipts)==3
 (a.out/'26889_REAL_COMPILED_SHADER_SHA256.txt').write_text('\n'.join(receipts)+'\n')
 print('PASS 26889 pinned REAL glslang/SPIR-V 3 modified native variants + original ESSL300 LONG')
else:
 print('REAL GLSLANG 16.5.0 AND SPIR-V COMPILERS NOT RUN LOCALLY; deferred to Actions')
