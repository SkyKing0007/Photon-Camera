#!/usr/bin/env python3
from pathlib import Path
import difflib,re,sys

if len(sys.argv) != 3: raise SystemExit('usage: validate_26564_true2x_memory.py CANDIDATE_ROOT BASE_ROOT')
C=Path(sys.argv[1]); B=Path(sys.argv[2])
files=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
added=[]
for rel in files:
    a=(B/rel).read_text().splitlines(); b=(C/rel).read_text().splitlines()
    for line in difflib.unified_diff(a,b,lineterm=''):
        if line.startswith('+') and not line.startswith('+++'): added.append((rel,line[1:]))
def ck(name,cond,detail=''):
    if not cond: raise SystemExit(f'FAIL {name}: {detail}')
    print('PASS',name + (f' — {detail}' if detail else ''))
stack=(C/files[1]).read_text(); native=(C/files[0]).read_text(); bridge=(C/files[2]).read_text()
# The only full 2x-sized storage may be disk-backed files. No newly introduced heap/direct buffer or GL
# texture is allowed to multiply both full true2x dimensions.
forbidden=[]
# Match the dimensions inside the allocation expression itself; surrounding code may legitimately
# mention full output geometry while allocating only a bounded tile.
full_pairs = (
    r'fullOutputWidth[^;\n,)]*fullOutputHeight', r'fullOutputHeight[^;\n,)]*fullOutputWidth',
    r'trueW[^;\n,)]*trueH', r'trueH[^;\n,)]*trueW',
    r'outW[^;\n,)]*outH', r'outH[^;\n,)]*outW',
)
alloc_re = re.compile(r'(LargeDirectBuffer\.allocate\([^\n;]*|ByteBuffer\.allocate(?:Direct)?\([^\n;]*|ByteArray\([^\n;]*|FloatArray\([^\n;]*|ShortArray\([^\n;]*|IntArray\([^\n;]*|std::vector<[^>]+>[^;\n]*)')
for rel,line in added:
    sline=re.sub(r'\s+',' ',line)
    for m in alloc_re.finditer(sline):
        expr=m.group(0)
        if any(re.search(pair,expr) for pair in full_pairs): forbidden.append(f'{rel}: {expr}')
    if 'createTexture(' in sline:
        expr=sline[sline.index('createTexture('):]
        if any(re.search(pair,expr) for pair in full_pairs): forbidden.append(f'{rel}: {expr}')
ck('no newly introduced monolithic true2x heap/direct/GL allocation',not forbidden,'\n'.join(forbidden[:20]))
ck('true2x GPU tiles bounded', 'TRUE2X_GPU_TILE_WIDTH = 1024' in stack and 'TRUE2X_GPU_TILE_HEIGHT = 128' in stack)
ck('true2x CPU tiles bounded', 'TRUE2X_CPU_TILE_WIDTH = 512' in stack and 'TRUE2X_CPU_TILE_HEIGHT = 128' in stack)
ck('true2x render derivative tiled', 'val core = 512' in bridge and 'val halo = if (runDenoise) 128 else 0' in bridge)
ck('true2x final color render tiled', 'constexpr int core=256' in native and 'std::min(4,(int)(hc?hc:2))' in native)
ck('full true2x RGB16F carrier is disk-backed', 'out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)' in stack)
ck('final RGB8 output staging is disk-backed', 'ftruncate(outFd,(off_t)outBytes)' in native)
ck('Motion gain map staging is disk-backed', 'ftruncate(gainFd,(off_t)gainBytes)' in native)
ck('legacy full 2x detail GL owner retired', 'val superResDetailAccumulator = 0' in stack)
# Persisted evidence may use one native-scale covariance readback at a time, but never retain one per frame in RAM.
ck('covariance evidence persisted to file', 'covarianceFile = covarianceFile' in stack and 'cleanupTrue2xEvidence' in stack)
ck('flow is compact retained evidence', 'val flowData: ByteBuffer' in stack and 'flowWidth' in stack and 'flowHeight' in stack)
ck('RAW remains region-read from SafeImage', 'readTrue2xRawRegion(' in stack and 'readFileRegion(' in stack)
print('PASS TOTAL 12 / 12')
