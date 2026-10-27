#!/usr/bin/env python3
"""26885 Vulkan compute shader reserved identifiers + pinned expanded real compiler."""
from pathlib import Path
import argparse,re,sys,subprocess,hashlib
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--spirv-val');p.add_argument('--spirv-opt');p.add_argument('--out',type=Path);a=p.parse_args()
shader=a.candidate/'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
s=shader.read_text();assert s.lstrip().startswith('#version 450')
code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
reserved={'attribute','varying','namespace','using','typedef','asm','class','union','enum','template','this','public','static','extern','external','interface','sampler1D','sampler1DShadow','sampler2DRect','sampler2DRectShadow','samplerBuffer','samplerCubeArray','samplerCubeArrayShadow','image1D','image1DArray','image2DRect','imageBuffer','long','short','double','half','fixed','unsigned','input','output','goto','common','partition','active','filter','sizeof','cast','resource','subroutine','precise','precision'}
for m in re.finditer(r'\b(?:uniform|readonly|writeonly|const|float|int|uint|vec[234]|uvec[234]|ivec[234]|mat[234]|image2D|uimage2D|buffer|void|bool)\s+([A-Za-z_]\w*)',code):
 assert m.group(1) not in reserved,('reserved name',m.group(1))
assert 'void main(' in code and 'imageStore(amazeRgbInPlace' in code
assert 'imageLoad(wronskiRgb' in code and 'originalSensorClip' in code
assert '#include' not in code and 'set=0,binding=3' in code
if a.compiler:
 assert a.spirv_val and a.spirv_opt and a.out
 assert Path(a.compiler).is_file() and Path(a.spirv_val).is_file() and Path(a.spirv_opt).is_file()
 a.out.mkdir(parents=True,exist_ok=True)
 adapter=shader.parent/'compile_locked_rawr_glslc.py'
 dest=a.out/'wronski_chroma_guide.spv'
 subprocess.run([sys.executable,'-S',str(adapter),f'--validator={a.compiler}',f'--spirv-val={a.spirv_val}',f'--spirv-opt={a.spirv_opt}','--target-env=vulkan1.1','-O',str(shader),'-o',str(dest)],check=True)
 data=dest.read_bytes();assert len(data)>=84 and data[:4]==b'\x03\x02\x23\x07'
 print('PASS 26885 PINNED REAL GLSLANG 16.5.0 and SPIRV-VAL pre/post optimized',hashlib.sha256(data).hexdigest())
else:print('PASS 26885 full new shader declaration/reserved scan and source; REAL GLSL NOT RUN HERE',hashlib.sha256(shader.read_bytes()).hexdigest())
