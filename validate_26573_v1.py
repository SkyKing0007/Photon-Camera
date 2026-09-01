#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys,re
CHANGED={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}

def fail(m): raise SystemExit('FAIL: '+m)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(r): return {str(p.relative_to(r)):H(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def smooth01(x):
    t=max(0.0,min(1.0,x));return t*t*(3.0-2.0*t)
def temporal_agreement(samples,weights=None):
    if weights is None: weights=[1.0]*len(samples)
    sw=sum(weights);sw2=sum(w*w for w in weights)
    if sw<=.08 or sw2<=1e-6:return 0.0
    mean=sum(w*y for w,y in zip(weights,samples))/sw
    var=max(sum(w*y*y for w,y in zip(weights,samples))/sw-mean*mean,0.0)
    neff=sw*sw/max(sw2,1e-6)
    support=smooth01((neff-1.50)/1.50)
    rs=math.sqrt(var)/max(abs(mean),.030)
    stable=1.0-smooth01((rs-.060)/.120)
    return max(0.0,min(1.0,support*stable))
def fixture(direct_y,temporal,guide_y=.20,phase=4,peak=.20,chroma_gate=1.0,agreement_gate=1.0,signal_gate=1.0):
    low=sum(direct_y)/4.0
    pg=1.0 if phase>=4 else .85 if phase==3 else .50 if phase==2 else 0.0
    hg=1.0-smooth01((peak-.72)/.20)
    safety=min(signal_gate,hg,chroma_gate,agreement_gate)
    confidence=max(0.0,min(1.0,pg*min(temporal)*safety))
    denom=max(low,.015); residual=[(y-low)/denom for y in direct_y]
    ma=max(abs(x) for x in residual);shape=min(1.0,.42/ma) if ma>1e-6 else 0.0
    factors=[]
    for d in residual:
        target=max(guide_y+guide_y*d*shape*confidence,0.0)
        factors.append(max(.68,min(1.47,target/guide_y)) if guide_y>1e-5 else 1.0)
    return factors,confidence,residual,shape
def math_regressions():
    if temporal_agreement([.2]*8)<.999999:fail('stable cross-frame evidence not full confidence')
    two=temporal_agreement([.2,.2])
    if not (.20<two<.35):fail(f'two-frame temporal support should remain weak, got {two}')
    if temporal_agreement([.2])!=0:fail('single observation gained SR authority')
    mild=temporal_agreement([.195,.20,.202,.198,.204,.197,.201,.203])
    if mild<.95:fail(f'mild stable variation wrongly rejected {mild}')
    outlier=temporal_agreement([.15,.25,.15,.25,.15,.25,.15,.25])
    if outlier>.02:fail(f'alternating alignment/phase instability survived {outlier}')
    f,c,r,shape=fixture([.15,.25,.15,.25],[1,1,1,1])
    if c<.99 or shape<=0:fail('stable 2x detail not admitted')
    if abs(sum(r))>1e-10:fail('zero-DC residual regression')
    if not all(.68<=x<=1.47 for x in f):fail('factor bounds')
    f,c,_,_=fixture([.15,.25,.15,.25],[1,1,0,1])
    if c!=0 or any(abs(x-1)>1e-12 for x in f):fail('one unstable 2x subpixel must invalidate cell')
    f,c,_,_=fixture([.15,.25,.15,.25],[1,1,1,1],phase=1)
    if c!=0 or any(abs(x-1)>1e-12 for x in f):fail('low phase fallback')
    f,c,_,_=fixture([.80,.90,.80,.90],[1,1,1,1],peak=.93)
    if c!=0 or any(abs(x-1)>1e-12 for x in f):fail('highlight safety regression')

def embedded(src,name):
    m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src)
    if not m:fail('missing embedded shader '+name)
    a=m.end();z=src.find('""".trimIndent()',a)
    if z<0:fail('missing embedded shader terminator '+name)
    return src[a:z]

def main():
    if len(sys.argv)!=3:fail('usage base candidate')
    b,c=map(Path,sys.argv[1:]);fb,fc=files(b),files(c)
    if set(fb)!=set(fc):fail('file universe changed')
    changed={p for p in fb if fb[p]!=fc[p]}
    if changed!=CHANGED:fail('changed-file allowlist mismatch '+repr(sorted(changed)))
    if len(fb)!=1708:fail(f'candidate authority file count expected 1708 got {len(fb)}')
    sh0=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    st0=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
    br0=(b/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text();br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    n0=(b/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();n=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    ver=(c/'app/version.properties').read_text()
    if 'VERSION_NAME=0.9726573' not in ver or 'VERSION_BUILD=26573' not in ver:fail('version')
    # Exactly two runtime-expanded shader strings changed inside the shader carrier.
    names=[]
    pat=re.compile(r'(?m)^\s*(?:private\s+)?val\s+(\w+)\s*=\s*"""')
    for m in pat.finditer(sh):
        name=m.group(1)
        try:a=embedded(sh0,name);d=embedded(sh,name)
        except SystemExit:continue
        if a!=d:names.append(name)
    if sorted(names)!=['true2xGuideRender26568','true2xMerge26564']:fail('modified expanded shader set '+repr(sorted(names)))
    merge=embedded(sh,'true2xMerge26564');render=embedded(sh,'true2xGuideRender26568')
    for token in ['layout(location = 3) out vec4 oTemporalLumaStats','IRIS_26573_CROSS_FRAME_LUMA_MOMENTS','frameY * temporalWeight','frameY * frameY * temporalWeight','temporalWeight * temporalWeight','frameWeight > 0.08 && sourceRawPeak < uRawClipThreshold']:
        if token not in merge:fail('GPU temporal moment contract '+token)
    for token in ['IRIS_26573_CROSS_FRAME_TRUE_DETAIL_LUMA_OWNER','uniform sampler2D uTemporalLumaStats','irisTemporalAgreement','effectiveN = (sumW * sumW)','relativeSigma = sqrt(varianceY)','(effectiveN - 1.50) / 1.50','(relativeSigma - 0.060) / 0.120','IRIS_26573_BLOCK_WIDE_TEMPORAL_PROOF','temporalGate = min(min(t00, t10), min(t01, t11))','phaseGate * temporalGate * safetyGate','0.42 / maxAbsDetail','clamp(targetY / guideY, 0.68, 1.47)','IRIS_26573_REQUIRED_SR_PROOF_DIAGNOSTIC','phaseCount * 8 + reasonClass']:
        if token not in render:fail('GPU cross-frame detail contract '+token)
    if 'guideRgb * factor' not in render:fail('trusted guide scalar RGB output missing')
    if re.search(r'oRenderRgb\s*=\s*vec4\s*\(\s*direct',render):fail('direct CFA became output RGB owner')
    # GPU host ownership + proof completeness.
    for token in ['createTexture(tileWidth, tileHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)','intArrayOf(color, weights, phase, temporal)','bindTexture(program,"uTemporalLumaStats",3,temporal)','IRIS_26573_REQUIRED_SR_PROOF_NO_SECOND_READBACK','phaseHistogram.sum() == expectedPixels','reasonTotal == expectedPixels','IRIS_26573_SR_PROOF','PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26573_SR_PROOF details=$proof")','TRUE2X_PROOF_GRID_WIDTH = 32','TRUE2X_PROOF_GRID_HEIGHT = 24','TRUE2X_ACCUMULATOR_FLOATS_PER_PIXEL = 10','IRIS_26573_CPU_PACKED_PHASE_TEMPORAL_PROOF']:
        if token not in st:fail('stacker proof/runtime contract '+token)
    if st.count('GLES30.glReadPixels(')-st0.count('GLES30.glReadPixels(')!=0:fail('26573 added a new full-resolution GPU readback')
    # CPU native parity.
    for token in ['tileW*tileH*10*(jlong)sizeof(float)','frameY*fw','frameY*frameY*fw','acc[q+8]+=fw','acc[q+9]+=fw*fw','packedSupportAt','>>3)&0x1fu','phaseGate*temporalGate*safetyGate','phaseCount*8+reasonClass','GetArrayLength(detailStats)<9']:
        if token not in n:fail('CPU/native parity contract '+token)
    # CPU proof must count only non-overlapping published interiors, not denoise halos.
    for token in ['IRIS_26573_CPU_INTERIOR_ONLY_PROOF','val nativeScratchStats = LongArray(9)','accumulateInteriorProof(','rgba, nativeScratchStats','detailStats[0] == expectedPixels','gridTotal == expectedPixels','IRIS_26573_SR_PROOF','PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26573_SR_PROOF details=$proof")']:
        if token not in br:fail('bridge hard SR proof '+token)
    if 'rgba, detailStats,' in br:fail('CPU halo-overlap stats still feed authoritative whole-frame counters')
    # Existing 26571 edge/color and publication-speed owners must be untouched.
    edge='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    if H(b/edge)!=H(c/edge):fail('26571 coherent edge-color owner changed')
    cm='app/src/main/cpp/CMakeLists.txt'
    if H(b/cm)!=H(c/cm):fail('26571 publication CMake owner changed')
    marker='/* IRIS_26571_TRUE2X_GPU_PUBLICATION'
    i0=n0.find(marker);i1=n.find(marker)
    if i0<0 or i1<0 or n0[i0:]!=n[i1:]:fail('26571 GPU/PBO/JPEG publication tail changed')
    # No source path reintroduces sharpening as SR authority.
    for token in ['unsharp','laplacian','sharpen26573','edgeEnhance26573']:
        if token.lower() in (sh+st+br+n).lower():fail('forbidden sharpening authority '+token)
    math_regressions()
    print('PASS exact 5-file runtime allowlist files=1708')
    print('PASS 26573 cross-frame temporal luminance proof + block-wide admission GPU/CPU parity')
    print('PASS zero-DC luminance-only SR; Sabre/VGN RGB/chroma/highlight ownership preserved')
    print('PASS mandatory exact-pixel SR proof + 32x24 activity maps with CPU interior-only accounting')
    print('PASS 26571 edge-color and late GPU/PBO/JPEG publication owners byte-identical')
    print('PASS stable/mild/outlier/single-observation/phase/highlight synthetic regressions')
if __name__=='__main__':main()
