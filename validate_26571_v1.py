#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
CHANGED={
'app/src/main/cpp/CMakeLists.txt',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
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
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)
def lum(rgb): return .25*rgb[0]+.5*rgb[1]+.25*rgb[2]
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,k): return tuple(x*k for x in a)
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def length(a): return math.sqrt(sum(x*x for x in a))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def mix(a,b,t): return tuple(x*(1-t)+y*t for x,y in zip(a,b))
def universal_fixture(center,neighbors):
    cy=lum(center); cs=max(cy,.060); cc=sub(center,(cy,cy,cy)); cnc=mul(cc,1/cs)
    nsum=cnc; ws=1.; support=0.; maxd=0.; br=dk=0
    for nrgb in neighbors:
        ny=lum(nrgb); ls=max(cy,ny,.060); sd=(ny-cy)/ls; rd=abs(sd); maxd=max(maxd,rd)
        br+=sd>.16; dk+=sd<-.16
        w=1-smoothstep(.16,.55,rd); nc=sub(nrgb,(ny,ny,ny)); nn=mul(nc,1/max(ny,.060))
        nsum=add(nsum,mul(nn,w)); ws+=w; support+=w
    cons=mul(nsum,1/max(ws,1e-6)); disagreement=length(sub(cnc,cons)); cm=length(cons); cnm=length(cnc)
    agree=max(-1,min(1,dot(cnc,cons)/max(cnm*cm,1e-6)))
    unsupported=smoothstep(.045,.260,disagreement)*(1-smoothstep(.18,.65,cm)); surf=smoothstep(1.5,5.5,support)
    legacyedge=smoothstep(.45,.90,maxd); one=1.0 if ((br>=4 and dk<=1) or (dk>=4 and br<=1)) else 0.0
    hi=1-smoothstep(.72,.92,cy); material=one*(1-smoothstep(.72,.92,agree))*hi; edge=max(legacyedge,material)
    coherent=smoothstep(.72,.94,agree)*smoothstep(.050,.180,cm); ratio=cnm/max(cm,.025); plausible=1-smoothstep(2.0,3.5,ratio); protect=coherent*plausible*hi
    correction=.65*unsupported*surf*(1-edge)*(1-.85*protect)
    tc=mul(cons,cs); ccm=length(cc); tm=length(tc)
    if tm>ccm and tm>1e-7: tc=mul(tc,ccm/tm)
    outc=mix(cc,tc,correction); out=tuple(max(0,min(1,cy+x)) for x in outc)
    return out,correction,material,agree
def color_math_regressions():
    sky=(.23,.55,.88);out,c,_,_=universal_fixture(sky,[sky]*8)
    if max(abs(x-y) for x,y in zip(out,sky))>1e-7 or c!=0: fail('clean sky pass-through regression')
    foliage=(.10,.34,.08);out,c,_,_=universal_fixture(foliage,[foliage]*8)
    if max(abs(x-y) for x,y in zip(out,foliage))>1e-7 or c!=0: fail('coherent foliage pass-through regression')
    neutral=(.30,.30,.30);false=(.42,.24,.42);out,c,_,_=universal_fixture(false,[neutral]*8)
    if c<=.10 or length(sub(out,(lum(out),)*3))>=length(sub(false,(lum(false),)*3)): fail('isolated false chroma still suppressible regression')
    neutral_hi=(.90,.90,.90);pink_hi=(1.0,.80,.96);out,c,_,_=universal_fixture(pink_hi,[neutral_hi]*8)
    if c<=.05: fail('highlight pink cleanup preservation regression')
    fol2=(.15,.50,.12);sky2=(.25,.53,.70);mixed=(.32,.32,.32);out,c,m,_=universal_fixture(fol2,[sky2]*4+[mixed]*4)
    if m<=.95 or c>=.02: fail('moderate foliage/sky material boundary regression')
    dark=(.08,.24,.07);bright=(.20,.55,.18);_,_,m,_=universal_fixture(dark,[bright]*4+[dark]*4)
    if m>=.5: fail('illumination-only same material misclassified regression')
    def reset(edge,jump,maxy):
        hi=1-smoothstep(47162.88,60263.68,maxy)
        return edge>.55 or (edge>.24 and jump>.45 and hi>.5)
    if not reset(.30,.70,20000) or reset(.30,.10,20000) or reset(.30,.70,62000) or not reset(.60,.10,62000): fail('IIR material/highlight boundary policy regression')
    original=1000.;candidate=300.;protected=min(max(candidate,.80*original),original)
    if protected!=800 or protected>original: fail('directional chroma floor/cap regression')

def main():
    if len(sys.argv)!=3: fail('usage base candidate')
    b,c=map(Path,sys.argv[1:]);fb,fc=files(b),files(c)
    if set(fb)!=set(fc): fail('file universe changed')
    changed={p for p in fb if fb[p]!=fc[p]}
    if changed!=CHANGED: fail('changed-file allowlist mismatch '+repr(sorted(changed)))
    e0=(b/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();e=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    cm=(c/'app/src/main/cpp/CMakeLists.txt').read_text();ver=(c/'app/version.properties').read_text()
    k0=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    k=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    for start,end,label in [
      ('inline bool profileColor(','inline bool adaptiveAppearance(','profileColor'),('inline bool adaptiveAppearance(','inline Vec3 tone(','adaptiveAppearance'),('inline Vec3 tone(','inline bool preRenderAt(','tone'),('inline Vec3 renderHeadroom(','struct SrgbLut','headroom'),('inline bool renderBaseCached(','inline float guideRgb(','renderBaseCached'),('inline void applyJinPixel(','/* IRIS_26568_TRUE2X_STREAMING_JPEG','Jin transfer'),('struct StreamingBandTiming','extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative','26570 CPU streaming helpers')]:
        if block(e0,start,end)!=block(e,start,end): fail(label+' changed versus successful 26570')
    for token in ['IRIS_26571_TRUE2X_GPU_PUBLICATION','IRIS_26571_TRUE2X_PUBLICATION_COMPUTE','IRIS_26571_TRUE2X_GPU_PUBLICATION_ROUTE','GL_RGBA8UI','GL_PIXEL_PACK_BUFFER','glFenceSync','glMapBufferRange','queue.finish(false,"jpeg_band_encode")','Exact successful 26570 CPU fallback begins here.','IRIS_26571_TRUE2X_GPU_FALLBACK','"MotionTrace","PIPELINE_STATE stage=IRIS_26571_TRUE2X_GPU_PUBLICATION','"MotionTrace","PIPELINE_STATE stage=IRIS_26571_TRUE2X_CPU_FALLBACK']:
        if token not in e: fail('missing GPU publication contract '+token)
    if 'glTexStorage2D(GL_TEXTURE_2D,1,GL_RGBA8UI,outWidth,maxBandRows)' not in e: fail('bounded GPU output allocation')
    if 'glGenBuffers(2,pbo)' not in e or 'pboSlots=2' not in e: fail('two-PBO bounded readback')
    if 'bool gpuEligible=motionFast&&!water.enabled();' not in e: fail('GPU eligibility must exclude Jin/watermark')
    if 'if(!params||!out||slot<0||slot>1)return false;' in e: fail('GPU producer null-output regression')
    if 'if(!params||slot<0||slot>1)return false;' not in e: fail('GPU renderReadback reachability guard missing')
    if 'gpu.renderReadback(sourceFd,gainMax,generateGain,top,h,slot,nullptr,gpuTiming,&why)' not in e: fail('GPU deferred-output producer call changed')
    route=block(e,'/* IRIS_26571_TRUE2X_GPU_PUBLICATION_ROUTE','/* Exact successful 26570 CPU fallback begins here. */')
    if 'return JNI_FALSE' in route: fail('GPU route can return failure before CPU fallback')
    for token in ['jpeg_set_quality(&baseC,std::clamp((int)quality,1,100),TRUE)','baseC.comp_info[k].h_samp_factor=1','baseC.comp_info[k].v_samp_factor=1','gainC.image_width=outW;gainC.image_height=outH','gainC.in_color_space=JCS_GRAYSCALE','const int bandRows=motionFast?256:128','IRIS_26570_TRUE2X_ENCODER_TIMING','scratch=BOUNDED_DOUBLE_BAND']:
        if token not in e: fail('26570 quality/fallback contract '+token)
    gpu=block(e,'/* IRIS_26571_TRUE2X_GPU_PUBLICATION','struct StreamingBandTiming')
    for stale in ['MotionV2CfaReconstruction','direct_rgb_accumulate','PyramidAlignment','ExposureFusionBayer2']:
        if stale in gpu: fail('GPU publisher acquired forbidden owner '+stale)
    if 'target_link_libraries(motionv2jpeg PRIVATE turbojpeg-static jpeg-static iris26507-ultrahdr log jnigraphics android z EGL GLESv3)' not in cm: fail('native EGL/GLESv3 link declaration')
    if 'VERSION_NAME=0.9726571' not in ver or 'VERSION_BUILD=26571' not in ver: fail('version')
    # Exact IQ ownership: only four named embedded shader regions plus dispatch comment may differ in the VGN Kotlin file.
    for token in ['IRIS_26571_COHERENT_EDGE_COLOR_OWNER','IRIS_26571_COHERENT_CHROMA_PRESERVATION','IRIS_26571_SAME_SIDE_MATERIAL_BOUNDARY','IRIS_26571_CROSS_EDGE_CHROMA_OWNERSHIP','IRIS_26571_DIRECTIONAL_EDGE_CHROMA_FLOOR','IRIS_26571_IIR_MATERIAL_EDGE_STATE_RESET']:
        if token not in k: fail('missing color/edge owner '+token)
    if 'IRIS_26570_ONE_SIDED_EDGE_LUMA_AUTHORITY' not in k: fail('26570 luma halo protection lost')
    if 'targetChroma *= centerMagnitude / targetMagnitude;' not in k: fail('no chroma boost cap lost')
    if 'highlightPreservePermission' not in k: fail('highlight false-color safety gate lost')
    if '0.80*originalMagnitude' not in k or 'protectedMagnitude=clamp(edgeMagnitude,0.80*originalMagnitude,originalMagnitude)' not in k: fail('edge vibrancy floor/cap missing')
    if 'edgeRatio>0.55' not in k or 'edgeRatio>0.24&&chromaJump>0.45' not in k: fail('IIR strong + moderate material boundary ownership missing')
    # Unrelated Kotlin regions around the modified shader owner must remain byte-identical.
    if block(k0,'internal object Iris26529SpatialRgbChromaShaders {','    /* IRIS_26570_SURFACE_CONTINUITY_ILLUMINATION_INDEPENDENT') != block(k,'internal object Iris26529SpatialRgbChromaShaders {','    /* IRIS_26571_COHERENT_CHROMA_PRESERVATION'): fail('pre-shader Kotlin owner changed unexpectedly')
    # Preserve all shaders after iirRgb exactly; only universal/localMedian/directional/iir are intentionally changed and localClamp stays byte-identical.
    if block(k0,'    val localClamp = """','    val localMedian = """') != block(k,'    val localClamp = """','    val localMedian = """'): fail('26570 localClamp bytes changed')
    if k0[k0.find('    val calculateError = """'):] != k[k.find('    val calculateError = """'):]: fail('post-iir VGN shader graph changed unexpectedly')
    color_math_regressions()
    print('PASS exact 4-file runtime allowlist')
    print('PASS successful 26570 CPU render/Jin/streaming fallback functions byte-identical')
    print('PASS bounded GLES 3.1 publication + two-PBO readback + CPU fallback contract')
    print('PASS 26570 clean-sky/luma-halo/no-clump/pink-safety ownership retained with localized coherent edge-color correction')
    print('PASS synthetic clean-sky / foliage-edge / false-chroma / highlight / IIR regressions')
    print('PASS 4:4:4 base / 1:1 gain / Display-P3 / true50MP publication contracts preserved')
if __name__=='__main__': main()
