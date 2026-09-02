#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=['app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/version.properties']

def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(root): return {str(p.relative_to(root)):sha(p) for p in sorted((Path(root)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
    if t not in s: fail(label+' missing: '+t)
def extract_raw_string(s,name):
    m=re.search(r'static const char\*'+re.escape(name)+r'=R"GLSL\((.*?)\)GLSL";',s,re.S)
    if not m: fail('native embedded shader missing '+name)
    return m.group(1)

def main():
    if len(sys.argv)!=3: fail('usage base candidate')
    base,cand=map(Path,sys.argv[1:])
    a,b=amap(base),amap(cand)
    if len(a)!=1708 or len(b)!=1708: fail(f'candidate universe {len(a)}/{len(b)}')
    diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
    if diff!=CHANGED: fail('changed allowlist '+repr(diff))
    v=(cand/'app/version.properties').read_text()
    need(v,'VERSION_NAME=0.9726577','version name'); need(v,'VERSION_BUILD=26577','version build')
    native=(cand/CHANGED[0]).read_text(); native_base=(base/CHANGED[0]).read_text()

    # The publication compute/pixel math is frozen exactly from successful 26576.
    if extract_raw_string(native_base,'kIris26571PublicationCompute') != extract_raw_string(native,'kIris26571PublicationCompute'):
        fail('26571 publication compute math changed')
    for t in ['const int bandRows=motionFast?256:128','glGenBuffers(2,pbo)','pboSlots=2','jpeg_set_quality(&baseC,std::clamp((int)quality,1,100),TRUE)','/* Exact successful 26570 CPU fallback begins here. */']:
        need(native,t,'publication invariant')

    # Exact 26576 runtime failure becomes a permanent transport regression.
    for t in [
        'IRIS_26577_TRUE2X_GPU_READBACK_COMPAT_TIER',
        'useExplicitFenceSync',
        'gpuMode=%s',
        'MAP_SYNC_COMPAT',
        'ASYNC_FENCE',
        'glUnmapBuffer_invalidated',
        'resolve_invalid_state',
        'resolve_missing_fence',
        'resolve_bind_pbo',
        'resolve_unbind_pbo',
        'asyncFailureReason=%s',
        'compatFailureReason=%s',
        'IRIS_26577_TRUE2X_GPU_TO_CPU_FALLBACK',
    ]: need(native,t,'26577 GPU publication correction')
    if '"gpu_failed"' in native: fail('generic gpu_failed reason survives')
    if 'return glGetError()==GL_NO_ERROR' in native: fail('reasonless resolve error exit survives')
    if 'GLboolean unmapOk=glUnmapBuffer' not in native: fail('glUnmapBuffer result not validated')

    # Ordering: proven async GPU first, map-synchronized GPU compatibility second, CPU last.
    async_call='(int)quality,true,&gpuTiming'
    compat_call='(int)quality,false,&gpuCompatTiming'
    cpu='/* Exact successful 26570 CPU fallback begins here. */'
    for t in [async_call,compat_call,cpu]: need(native,t,'GPU tier ordering')
    if not (native.index(async_call) < native.index(compat_call) < native.index(cpu)):
        fail('GPU async -> GPU compat -> CPU fallback order changed')

    # Map-sync compatibility remains GPU rendering: same compute/readPixels/PBO route, only explicit fence wait is bypassed.
    if native.count('glDispatchCompute((GLuint)((outWidth+15)/16),(GLuint)((h+7)/8),1)') != native_base.count('glDispatchCompute((GLuint)((outWidth+15)/16),(GLuint)((h+7)/8),1)'):
        fail('publication dispatch count changed')
    if native.count('glReadPixels(0,0,outWidth,h,GL_RGBA_INTEGER,GL_UNSIGNED_BYTE,(void*)0)') != native_base.count('glReadPixels(0,0,outWidth,h,GL_RGBA_INTEGER,GL_UNSIGNED_BYTE,(void*)0)'):
        fail('publication readPixels count changed')

    # No shader/DNG/Night/Java ownership surface is allowed into this correction.
    forbidden=[p for p in diff if '/shaders/' in p or p.endswith('.kt') or p.endswith('.java') or 'Night' in p or 'dng' in p.lower()]
    if forbidden: fail('forbidden ownership change '+repr(forbidden))

    print('PASS exact 1708-file successful-26576 authority -> two-file 26577 allowlist')
    print('PASS embedded 26571 publication compute/pixel math byte-identical')
    print('PASS proven ASYNC_FENCE GPU path remains first choice')
    print('PASS MAP_SYNC_COMPAT GPU tier precedes exact 26570 CPU fallback')
    print('PASS reasonless gpu_failed exit eliminated; resolve/map/unmap stages named')
    print('PASS glUnmapBuffer validity and GL errors explicitly checked')
    print('PASS no Java/Kotlin/GLSL/DNG/Night/reconstruction ownership changes')
if __name__=='__main__': main()
