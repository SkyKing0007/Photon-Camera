#!/usr/bin/env python3
"""26886 complete modified Vulkan compute shader token scan and PINNED real compilation."""
from pathlib import Path
import argparse,re,hashlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--compiler');p.add_argument('--spirv-val');p.add_argument('--spirv-opt');p.add_argument('--out',type=Path);a=p.parse_args()
src=a.candidate/'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
s=src.read_text();assert s.startswith('#version 450') and '#include' not in s
code=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
reserved=set('attribute varying namespace using typedef asm class union enum template this public static extern external interface sampler1D sampler1DShadow sampler2DRect sampler2DRectShadow samplerBuffer samplerCubeArray samplerCubeArrayShadow image1D image1DArray image2DRect imageBuffer long short double half fixed unsigned input output goto common partition active filter sizeof cast resource subroutine precise precision'.split())
for m in re.finditer(r'\b(?:uniform|readonly|writeonly|const|float|int|uint|vec[234]|uvec[234]|ivec[234]|mat[234]|image2D|uimage2D|buffer|void|bool)\s+([A-Za-z_]\w*)',code):
 assert m.group(1) not in reserved,('reserved GLSL name',m.group(1))
assert 'layout(local_size_x=16,local_size_y=16)' in s and 'void main()' in s
assert s.count('imageStore(amazeRgbInPlace,')==1
if a.compiler:
 assert a.spirv_val and a.spirv_opt and a.out
 assert Path(a.compiler).is_file() and Path(a.spirv_val).is_file() and Path(a.spirv_opt).is_file()
 a.out.mkdir(parents=True,exist_ok=True)
 adapter=src.parent/'compile_locked_rawr_glslc.py';assert adapter.is_file()
 dest=a.out/'26886_wronski_chroma_guide.spv'
 subprocess.run([sys.executable,'-S',str(adapter),f'--validator={a.compiler}',f'--spirv-val={a.spirv_val}',f'--spirv-opt={a.spirv_opt}','--target-env=vulkan1.1','-O',str(src),'-o',str(dest)],check=True)
 b=dest.read_bytes();assert len(b)>=84 and b[:4]==b'\x03\x02\x23\x07'
 print('PASS 26886 PINNED REAL GLSLANG 16.5.0 and SPIRV-VAL pre/post optimized',hashlib.sha256(b).hexdigest())
else:print('PASS 26886 complete shader reserved/declaration/ownership scan; REAL GLSL NOT RUN HERE',hashlib.sha256(src.read_bytes()).hexdigest())
