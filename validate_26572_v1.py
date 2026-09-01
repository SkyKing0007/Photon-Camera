#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
CHANGED={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}

def fail(m): raise SystemExit('FAIL: '+m)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(r): return {str(p.relative_to(r)):H(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def block(s,a,b):
    x=s.find(a)
    if x<0: fail('missing block start '+a)
    y=s.find(b,x)
    if y<0: fail('missing block end '+b)
    return s[x:y]
def smooth01(x):
    t=max(0.0,min(1.0,x)); return t*t*(3.0-2.0*t)
def chroma(rgb):
    sm=max(sum(rgb),1e-5); return tuple(v/sm for v in rgb)
def dist(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def old_factor(direct_y, low_y, guide_y, phase=4, peak=.20, chroma_distance=0.0):
    pg=1.0 if phase>=4 else .68 if phase==3 else .32 if phase==2 else 0.0
    sg=smooth01((guide_y-.020)/.080)
    hg=1.0-smooth01((peak-.72)/.20)
    cg=1.0-smooth01((chroma_distance-.015)/.055)
    ag=1.0-smooth01((abs(math.log2((low_y+.01)/(guide_y+.01)))-.08)/.27)
    conf=max(0,min(1,pg*sg*hg*cg*ag))
    raw=max(-.25,min(.25,math.log2((direct_y+.004)/(low_y+.004))))
    return 2**(raw*conf),conf
def new_fixture(direct_y, guide_rgb, phases=(4,4,4,4), direct_block_rgb=None):
    # Mirrors 26572 block math for a grayscale direct-CFA luma fixture and one trusted guide chroma.
    if len(direct_y)!=4 or len(guide_rgb)!=4: fail('fixture geometry')
    low=max(sum(direct_y)/4,0.0)
    gy=[.25*r+.50*g+.25*b for r,g,b in guide_rgb]
    gb=max(sum(gy)/4,0.0)
    block_phase=min(phases)
    pg=1.0 if block_phase>=4 else .85 if block_phase==3 else .50 if block_phase==2 else 0.0
    sg=smooth01((gb-.015)/.055)
    peak=max(max(max(rgb) for rgb in guide_rgb),max(direct_y))
    hg=1.0-smooth01((peak-.72)/.20)
    if direct_block_rgb is None:
        direct_block=(low,low,low)
    else:
        direct_block=direct_block_rgb
    guide_block=tuple(sum(rgb[k] for rgb in guide_rgb)/4 for k in range(3))
    cd=dist(chroma(direct_block),chroma(guide_block))
    cg=1.0-smooth01((cd-.015)/.055)
    ag=1.0-smooth01((abs(math.log2((low+.01)/(gb+.01)))-.08)/.27)
    safety=min(sg,hg,cg,ag)
    conf=max(0,min(1,pg*safety))
    denom=max(low,.015)
    ds=[(y-low)/denom for y in direct_y]
    ma=max(abs(x) for x in ds)
    shape=min(1,.42/ma) if ma>1e-6 else 0.0
    out=[]; factors=[]
    for i,d in enumerate(ds):
        target=max(gy[i]+gb*d*shape*conf,0.0)
        factor=max(.68,min(1.47,target/gy[i])) if gy[i]>1e-5 else 1.0
        factors.append(factor);out.append(tuple(max(v*factor,0.0) for v in guide_rgb[i]))
    return out,factors,conf,ds,shape,(sg,hg,cg,ag)
def math_regressions():
    guide=[(.20,.20,.20)]*4
    # Flat evidence must be exact pass-through.
    out,f,c,ds,shape,_=new_fixture([.20]*4,guide)
    if any(abs(x-1)>1e-9 for x in f) or shape!=0: fail('flat true2x evidence not exact guide')
    # Strong real 2x pattern must carry more structure than 26571 under full confidence.
    ys=[.15,.25,.15,.25]
    _,nf,nc,ds,shape,_=new_fixture(ys,guide)
    of=[old_factor(y,.20,.20)[0] for y in ys]
    new_contrast=max(nf)-min(nf); old_contrast=max(of)-min(of)
    if nc<.99 or not new_contrast>old_contrast*1.35: fail(f'true-detail gain too weak new={new_contrast} old={old_contrast}')
    # Direct residual is zero DC inside the 2x2 block before safety scaling.
    if abs(sum(ds))>1e-10: fail('direct 2x2 residual has nonzero DC')
    # At full confidence and this unclipped fixture the guide block mean remains exact.
    # Recompute output for the block-mean proof.
    out,_,_,_,_,_=new_fixture(ys,guide)
    if abs(sum(.25*r+.50*g+.25*b for r,g,b in out)/4-.20)>1e-7: fail('accepted 2x2 fixture shifts guide DC')
    # 1 phase => exact guide; 2 phases can contribute but remains bounded.
    _,f1,c1,_,_,_=new_fixture(ys,guide,phases=(1,4,4,4))
    if c1!=0 or any(abs(x-1)>1e-9 for x in f1): fail('unsafe phase support not exact guide fallback')
    _,f2,c2,_,_,_=new_fixture(ys,guide,phases=(2,2,2,2))
    if not (0<c2<=.50 and all(.68<=x<=1.47 for x in f2)): fail('2-phase bounded support regression')
    # Highlight block => exact guide, protecting prior pink/highlight cleanup ownership.
    hi=[(.93,.93,.93)]*4
    _,fh,ch,_,_,gates=new_fixture([.90, .96, .90, .96],hi)
    if ch!=0 or any(abs(x-1)>1e-9 for x in fh) or gates[1]!=0: fail('highlight false-color safety can be bypassed')
    # Strong low-frequency chroma disagreement => exact guide, no direct chroma ownership.
    green=[(.10,.30,.08)]*4
    _,fc,cc,_,_,gates=new_fixture([.20,.30,.20,.30],green,direct_block_rgb=(.30,.05,.30))
    if cc!=0 or any(abs(x-1)>1e-9 for x in fc) or gates[2]!=0: fail('cross-material chroma disagreement not rejected')
    # Output chromaticity must equal the trusted guide chromaticity for accepted detail.
    colored=[(.14,.24,.08),(.14,.24,.08),(.14,.24,.08),(.14,.24,.08)]
    out,fac,conf,_,_,_=new_fixture([.16,.24,.16,.24],colored,direct_block_rgb=tuple(sum(x[k] for x in colored)/4 for k in range(3)))
    if conf<=.5: fail('colored accepted fixture unexpectedly rejected')
    for a,b in zip(out,colored):
        if dist(chroma(a),chroma(b))>1e-7: fail('direct true2x changed guide chromaticity')
    # Scalar output factor is hard bounded; no runaway edge/halo gain.
    if not all(.68-1e-9<=x<=1.47+1e-9 for x in fac): fail('true-detail factor bound regression')

def main():
    if len(sys.argv)!=3: fail('usage base candidate')
    b,c=map(Path,sys.argv[1:]); fb,fc=files(b),files(c)
    if set(fb)!=set(fc): fail('file universe changed')
    changed={p for p in fb if fb[p]!=fc[p]}
    if changed!=CHANGED: fail('changed-file allowlist mismatch '+repr(sorted(changed)))
    if len(fb)!=1708: fail(f'candidate authority file count expected 1708 got {len(fb)}')
    sh0=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    st0=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
    br0=(b/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    n0=(b/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); n=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    ver=(c/'app/version.properties').read_text()
    # Exact intended math markers.
    for token in ['IRIS_26572_TRUE_DETAIL_LUMA_OWNER','blockPhaseCount','guideBlockY','safetyGate = min(','0.42 / maxAbsDetail','targetY = max(guideY + guideBlockY * directDetail * confidence','clamp(targetY / guideY, 0.68, 1.47)','float(phaseCount) + detailCode']:
        if token not in sh: fail('GPU true-detail contract '+token)
    if 'rawLog = clamp(log2((directY + 0.004) / (lowY + 0.004)), -0.25, 0.25)' in sh: fail('26571 tiny exponent residual survived GPU')
    if 'phaseGate * signalGate * highlightGate * chromaGate * agreementGate' in sh: fail('26571 confidence-collapse product survived GPU')
    # 26572 must preserve 26571 speed intent: share 2x2 direct/phase fetches and use one native guide block anchor.
    for token in ['ivec2 nativeBlock = clamp(globalBlock / 2','vec3 guideBlockRgb = texelFetch(uNativeVgnGuide, nativeBlock','int p00 = irisPhaseCount(q00)','vec3 directRgb = cell.y == 0']:
        if token not in sh: fail('GPU true-detail fetch-sharing/performance contract '+token)
    if 'vec3 g00 = irisGuide(globalBlock)' in sh or 'vec3 directRgb = texelFetch(uDirectRgb, localP, 0).rgb' in sh:
        fail('redundant GPU per-pixel true-detail fetches survived')
    if 'auto guideBlock=gAt(bx/2,by/2)' not in n or 'int p00=supportAt(bx,by)' not in n:
        fail('CPU true-detail fetch-sharing/performance contract missing')
    if 'auto g00=bilGuide(bx,by)' in n:
        fail('redundant CPU four-bilinear guide block survived')
    for token in ['IRIS_26572_TRUE_DETAIL_LUMA_OWNER','blockPhaseCount','guideBlockY','0.42f/maxAbsDetail','clampf(targetY/guideY,0.68f,1.47f)','jlong stats[6]']:
        if token not in n: fail('CPU true-detail parity '+token)
    # Sole changed native block must remain before 26571 publication. The entire successful 26571 publisher is byte-identical.
    pub_start='/* IRIS_26571_TRUE2X_GPU_PUBLICATION'
    if n0[n0.index(pub_start):] != n[n.index(pub_start):]: fail('26571 GPU publication/PBO/JPEG mechanics changed')
    # All native code before the old/new true2x tile block and between it and publication remains byte-identical.
    write_marker='extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior'
    if n0[:n0.index('/* IRIS_26567_SABRE_GUIDED_CHROMA_NEUTRAL_TRUE2X')] != n[:n.index('/* IRIS_26572_TRUE_DETAIL_LUMA_OWNER')]: fail('native prefix outside true-detail owner changed')
    if n0[n0.index(write_marker):n0.index(pub_start)] != n[n.index(write_marker):n.index(pub_start)]: fail('native middle outside true-detail owner changed')
    # 26571 edge-color and publication link infrastructure are strictly protected.
    for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/cpp/CMakeLists.txt']:
        if H(b/rel)!=H(c/rel): fail('26571 protected file changed '+rel)
    # Only the one embedded true2x guide-render shader may change in the shader carrier file.
    if sh0[:sh0.index('    val true2xGuideRender26568 = """')] != sh[:sh.index('    val true2xGuideRender26568 = """')]: fail('shader carrier prefix changed')
    sh_end='\n    private val outputTransformBody = """'
    if sh0[sh0.index(sh_end):] != sh[sh.index(sh_end):]: fail('shader carrier suffix changed')
    # Stacker changes are telemetry/true2x render readback only; core merge/evidence producer stays byte-identical.
    for token in ['IRIS_26572_PHASE_AND_DETAIL_STATS_NO_SECOND_READBACK','IRIS_26572_TRUE_DETAIL_ACTIVITY backend=GPU','secondReadback=false','trueDetail26572=true']:
        if token not in st: fail('stacker 26572 telemetry '+token)
    for token in ['IRIS_26572_TRUE_DETAIL_RENDER_FUSED','highResLumaOwner=DIRECT_CFA','directChromaOwner=false','LongArray(6)','IRIS_26572_TRUE_DETAIL_ACTIVITY backend=CPU']:
        if token not in br: fail('bridge 26572 ownership '+token)
    if 'VERSION_NAME=0.9726572' not in ver or 'VERSION_BUILD=26572' not in ver: fail('version')
    math_regressions()
    print('PASS exact 5-file 26572 runtime allowlist over successful 26571 compiled authority')
    print('PASS 26571 edge-color/no-halo/no-clump/pink-safety owner byte-identical')
    print('PASS 26571 EGL/GLES/PBO/JPEG true2x publication mechanics byte-identical')
    print('PASS direct-CFA owns only bounded high-resolution luminance structure; Sabre/VGN retains RGB/chroma/highlight identity')
    print('PASS synthetic true-detail gain >26571 with zero-DC block residual, exact unsafe fallback, highlight/chroma rejection, chromaticity invariance')
if __name__=='__main__': main()
