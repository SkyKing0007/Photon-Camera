#!/usr/bin/env python3
from pathlib import Path
import re,sys
R=Path(__file__).resolve().parent
P=(R/'handoff_payload_26929') if '--payload' in sys.argv else R
shader=(P/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp').read_text()
inc=(P/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert '#version 450' in shader
assert 'layout(local_size_x=16,local_size_y=16,local_size_z=1) in;' in shader
assert 'layout(set=0,binding=0,rgba16f) readonly uniform image2D denoisedRgb;' in shader
assert 'layout(set=0,binding=1,rgba16f) coherent uniform image2D irisRgb;' in shader
assert 'uint width;uint height;' in shader
assert 'float singleShotA;float singleReadB;' in shader
assert 'float mergedFrames;float wbRed;float wbBlue;float reserved;' in shader
assert 'static_assert(sizeof(WaveletCopy26929Pc)==32u,' in inc
assert inc.count('bWaveletCopy->record(cmd,rb,&copyArgs,sizeof(copyArgs),outWidth,outHeight);')==1
assert 'program.workgroupX=16u;program.workgroupY=16u;program.workgroupZ=1u;' in inc
assert '32u,1u));' in inc
assert shader.count('imageLoad(irisRgb,')==1  # center only: no neighbor RAW hazards
assert 'imageStore(irisRgb,q,vec4(denoised,confidence));return;' in shader
assert 'imageStore(irisRgb,q,vec4(max(outColor,vec3(0)),confidence));' in shader
# 26929 V1 FAILURE REGRESSION: compile error at line 92 was caused by
# "float coherent=". A qualifier is legal before a uniform declaration, never
# as an identifier. This lint is additional; the real 16.5 compiler remains mandatory.
reserved=r'(?:coherent|volatile|restrict|readonly|writeonly|uniform|buffer|shared|layout|precision|sample|patch|attribute|varying|flat|smooth|noperspective|invariant)'
assert not re.search(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234])\s+'+reserved+r'\b',shader), 'GLSL reserved-identifier regression'
assert not re.search(r'\b'+reserved+r'\s*(?==)',shader), 'GLSL qualifier used as variable name'
# Negative test: the prior broken fragment must be rejected by the same guard.
def reserved_variable(text):
 return bool(re.search(r'\b(?:float|int|uint|bool|vec[234])\s+'+reserved+r'\b',text))
assert reserved_variable('float coherent=0.5;')
assert reserved_variable('float precision=0.5;')
assert reserved_variable('vec3 sample=vec3(0);')
assert not reserved_variable('float donorCoherence=0.5;')

print('PASS exact 32-byte push constants, immutable donor reads and in-place write ownership; real SPIR-V mandatory')
