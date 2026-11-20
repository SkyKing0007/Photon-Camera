#!/usr/bin/env python3
"""Fail before expensive toolchain setup on illegal identifiers and native shader wiring.

This is a lexical/ownership regression, NOT a replacement for real glslang/SPIR-V,
CMake/NDK link, Kotlin/Java or assembleDebug, all retained as mandatory gates.
"""
import re
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R if '--live' in sys.argv else R / 'handoff_payload_26970'
SHADER_DIR = Path('app/src/main/cpp/iris26864/bridge')
SHADERS = ('Iris26887BOffHdrqMerge.comp',
           'Iris26887BOffHdrqDeconvolute.comp',
           'Iris26970BOffGrainEven.comp')
# GLSL reserved qualifiers and names (including 26970 V1's actual 'vec3 out').
FORBIDDEN = set('''attribute varying buffer shared coherent volatile restrict readonly
 writeonly atomic_uint layout centroid flat smooth noperspective patch sample
 in out inout uniform precision highp mediump lowp invariant precise
 break continue do for while switch case default if else return discard
 class typedef template this union enum namespace using public static external
 inline long short half fixed unsigned input output common partition active
 sizeof cast goto noinline packed row_major column_major subroutine'''.split())
TYPE = r'(?:float|double|int|uint|bool|[biud]?vec[234]|d?mat[234](?:x[234])?|image\w+|[iu]?sampler\w+|atomic_uint)'
DECL = re.compile(r'\b'+TYPE+r'\s+([A-Za-z_]\w*)\s*(?=[=;,\[\)])')

def code_without_comments(s):
    return re.sub(r'/\*.*?\*/|//[^\n]*', ' ', s, flags=re.S)

def illegal_names(s):
    code=code_without_comments(s)
    return [(m.group(1),m.start()) for m in DECL.finditer(code) if m.group(1) in FORBIDDEN]

for file in SHADERS:
    path = ROOT / SHADER_DIR / file
    s=path.read_text()
    assert s.startswith('#version 450\n'),file
    assert code_without_comments(s).count('void main()')==1,file
    bad=illegal_names(s)
    assert not bad, f'{file}: illegal GLSL identifier {bad}'
    assert not re.search(r'\bisfinite\s*\(',code_without_comments(s)),file

# The actual 26970 V1 failure and other reserved-word negative mutations.
source=(ROOT/SHADER_DIR/SHADERS[-1]).read_text()
assert source.count('vec3 correctedRgb=fromLC(corrected);')==1
assert source.count('correctedRgb=clamp(')==1
assert source.count('if(!finite3(correctedRgb))correctedRgb=orig.rgb;')==1
assert source.count('vec4(correctedRgb,orig.a)')==1
for bad in ('out','in','flat','coherent','layout','uniform','shared','buffer','varying','attribute','precision','sample'):
    injected=source.replace('vec3 correctedRgb=fromLC(corrected);',
                            f'vec3 {bad}=fromLC(corrected);',1)
    assert illegal_names(injected),f'failed to detect invalid GLSL variable: {bad}'
# Do not flag a qualifier occurring in a comment.
assert not illegal_names('// vec3 out = something;\nvec3 validOutput=vec3(0.0);')

# Exact generated-header link from the 26970 shader to the AMaZE JNI compilation.
cm=(ROOT/Path('app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake')).read_text()
jni=(ROOT/Path('app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc')).read_text()
assert cm.count('elseif(BRIDGE_NAME STREQUAL "grain_even26970")')==1
assert cm.count('Iris26970BOffGrainEven.comp')==1
assert 'set(BRIDGE_HDR "${IRIS26864_BRIDGE_SPV_DIR}/iris26864_${BRIDGE_NAME}.h")' in cm
assert '"-DSYMBOL=iris26864_${BRIDGE_NAME}_spv"' in cm
assert 'add_dependencies(iris26856amaze iris26864_real_bridge_spirv)' in cm
assert 'target_include_directories(iris26856amaze PRIVATE "${IRIS26864_BRIDGE_SPV_DIR}")' in cm
assert jni.count('#include "iris26864_grain_even26970.h"')==1
assert jni.count('iris26864_grain_even26970_spv_size')==1
assert jni.count('iris26864_grain_even26970_spv;')==1
assert jni.count('bOffGrain26970->preflight(')==1
assert jni.count('bOffGrain26970->record(')==1
assert jni.count('bWaveletCopy->preflight(')>=1
for binding in ('binding=0,rgba16f','binding=1,rgba16f','binding=2)'):
    assert binding in source,binding
assert re.search(r'\{0u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE\}',jni)
assert re.search(r'\{1u,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE\}',jni)
assert 'nb.binding=2u;' in jni and 'nb.type=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER' in jni
assert 'struct alignas(16) GrainArgs' in jni and 'sizeof(GrainArgs)==48u' in jni
assert 'sr==JNI_FALSE && photoBOffOnly==JNI_TRUE' in jni
assert 'hdrqEffectiveChroma==JNI_FALSE' in jni
assert 'result.noiseEstimated' in jni
print('PASS 26970 V2 physically scanned changed GLSL reserved declarations, 12 negative mutations, CMake embedded SPIR-V header/ABI/bindings, protected B OFF gate')
