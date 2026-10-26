#!/usr/bin/env python3
"""Source preflight plus optional PINNED real glslang+SPIRV-tools for FIVE 26880 compute owners.
Real mode runs the exact CMake adapter, not a simulator; source-only never claims compile.
"""
from pathlib import Path
import argparse,re,subprocess,hashlib,sys
ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--compiler');ap.add_argument('--spirv-val');ap.add_argument('--spirv-opt');ap.add_argument('--out',type=Path)
a=ap.parse_args();src=a.candidate/'app/src/main/cpp/iris26864'
shaders={
'precondition':src/'vendor/rawr/native/raw_denoise/shaders/denoise_img_precondition.comp',
'atrous':src/'vendor/rawr/native/raw_denoise/shaders/denoise_img_atrous.comp',
'threshold':src/'vendor/rawr/native/raw_denoise/shaders/denoise_img_threshold.comp',
'backtransform':src/'vendor/rawr/native/raw_denoise/shaders/denoise_img_backtransform.comp',
'copy':src/'Iris26880WaveletCopy.comp'}
# Disallow reserved identifiers as shader-declared variables, functions and
# interface-block names. The pinned real GLSL language compiler is definitive.
reserved={'attribute','varying','namespace','using','typedef','asm','class','union','enum','template','this','public','static','extern','external','interface','sampler1D','sampler1DShadow','sampler2DRect','sampler2DRectShadow','samplerBuffer','samplerCubeArray','samplerCubeArrayShadow','image1D','image1DArray','image2DRect','imageBuffer','long','short','double','half','fixed','unsigned','input','output','goto','common','partition','active','filter','sizeof','cast','resource','subroutine','precise','precision'}
for name,p in shaders.items():
 assert p.is_file(),('missing modified 26880 shader',name)
 s=p.read_text();assert s.lstrip().startswith('#version 450'),(name,'missing Vulkan GLSL version')
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for m in re.finditer(r'\b(?:uniform|readonly|writeonly|const|float|int|uint|vec[234]|uvec[234]|ivec[234]|mat[234]|image2D|buffer|void|bool)\s+([A-Za-z_]\w*)',code):
  assert m.group(1) not in reserved,(name,'reserved declaration',m.group(1))
 assert 'void main(' in code,(name,'missing compute entry')
print('PASS 26880 all five original GPU wavelet/copy sources and reserved declaration preflight (NOT COMPILED)' if not a.compiler else 'PASS 26880 GLSL reserved scan before compiler')
if a.compiler:
 assert a.spirv_val and a.spirv_opt and a.out
 adapter=src/'compile_locked_rawr_glslc.py';a.out.mkdir(parents=True,exist_ok=True)
 for name,p in shaders.items():
  dest=a.out/(name+'.spv')
  subprocess.run([sys.executable,'-S',str(adapter),f'--validator={a.compiler}',f'--spirv-val={a.spirv_val}',f'--spirv-opt={a.spirv_opt}',
      '--target-env=vulkan1.1','-O',str(p),'-o',str(dest)],check=True)
  data=dest.read_bytes()
  assert len(data)>=84 and data[:4]==b'\x03\x02\x23\x07',('invalid real SPIRV',name)
  print('PASS pinned glslang 16.5.0 + spirv-val pre/post optimized',name,hashlib.sha256(data).hexdigest())
 print('PASS REAL 26880 FIVE ORIGINAL RAWR WAVELET SPIR-V COMPILERS')
