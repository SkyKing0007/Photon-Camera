#!/usr/bin/env python3
"""26930 native GLSL reserved tokens, descriptor/ABI, lifetime/in-place hazards."""
from pathlib import Path
import re,sys
R=Path(__file__).resolve().parent
P=(R/'handoff_payload_26930') if '--payload' in sys.argv else R
s=(P/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp').read_text()
a=(P/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert s.startswith('#version 450')
assert 'layout(local_size_x=16,local_size_y=16,local_size_z=1) in;' in s
assert 'layout(set=0,binding=0,rgba16f) readonly uniform image2D denoisedRgb;' in s
assert 'layout(set=0,binding=1,rgba16f) coherent uniform image2D irisRgb;' in s
assert 'layout(std430,set=0,binding=2) readonly buffer PhysicalLsc {vec4 lscMap[];};' in s
for x in ('uvec4 extent;','uvec4 sensor;','vec4 shot;','vec4 readNoise;','vec4 wb;'):
 assert x in s,x
assert 'struct alignas(16) WaveletCopy26930Pc' in a
assert 'static_assert(sizeof(WaveletCopy26930Pc)==80u' in a
assert 'program.workgroupX=16u;program.workgroupY=16u;program.workgroupZ=1u;' in a
assert '80u,1u));' in a
assert a.count('bWaveletCopy->record(cmd,rb,&copyArgs,sizeof(copyArgs),outWidth,outHeight);')==1
assert 'VkMemoryBarrier copyRead' in a and 'VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT' in a
assert s.count('imageLoad(irisRgb,')==1 # immutable donor source; center is only destination read
assert s.count('imageLoad(denoisedRgb,')==3 # center, donor, midpoint
assert s.count('imageStore(irisRgb,q,')>=3
assert 'ivec2 mid=q+off/2;' in s and 'any(greaterThan(at,limit))' in s
assert 'uvec2 coord=gl_GlobalInvocationID.xy;' in s
reserved=r'(?:coherent|precision|sample|patch|volatile|restrict|readonly|writeonly|uniform|buffer|shared|layout|attribute|varying|flat|smooth|noperspective|invariant)'
def forbidden(t):
 return bool(re.search(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234])\s+'+reserved+r'\b',t) or
             re.search(r'\b'+reserved+r'\s*(?==)',t))
assert not forbidden(s), 'INVALID GLSL RESERVED IDENTIFIER: previously failed 26925 and 26929'
for t in ('float coherent=0.1;','float precision=0.1;','vec3 sample=vec3(0);',
          'int patch=1;','float shared = 1.0;'):assert forbidden(t),t
assert not forbidden('float donorCoherence=0.5;')
# Both physical signal variance and LSC propagate the correct squares.
assert 'vec3 srcSensor=max(original.rgb/lsc,vec3(0.0));' in s
assert '*lsc*lsc*p.wb.rgb*p.wb.rgb' in s
assert 'float restoreY=' in s and 'vec3 adjustment=target-chroma;' in s
assert 'adjustment-=vec3(lightness(adjustment));' in s
assert 'imageStore(irisRgb,q,vec4(max(revised,vec3(0.0)),confidence));' in s
print('PASS 26930 reserved GLSL coherent/precision/sample/pattern negative checks, exact 80-byte/three-descriptor Vulkan ABI, immutable donors')
