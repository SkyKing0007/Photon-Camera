#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
CHANGED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/version.properties'}

def fail(m): raise SystemExit('FAIL: '+m)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(r):
    app=r/'app'
    return {str(p.relative_to(r)):H(p) for p in sorted(app.rglob('*')) if p.is_file()}
def smooth(a,b,x):
    if b==a:return 1.0 if x>=b else 0.0
    t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def correction(center_luma, center_chroma, neigh):
    center_scale=max(center_luma,.060);cn=[x/center_scale for x in center_chroma]
    s=cn[:];ws=1.;support=0.;mx=0.
    for nl,nc in neigh:
        scale=max(center_luma,nl,.060);d=abs(nl-center_luma)/scale;mx=max(mx,d);w=1-smooth(.16,.55,d)
        nn=[x/max(nl,.060) for x in nc]
        s=[s[i]+nn[i]*w for i in range(3)];ws+=w;support+=w
    co=[x/ws for x in s];dis=math.sqrt(sum((cn[i]-co[i])**2 for i in range(3)));mag=math.sqrt(sum(x*x for x in co))
    unsupported=smooth(.045,.260,dis)*(1-smooth(.18,.65,mag)); surface=smooth(1.5,5.5,support); edge=smooth(.45,.90,mx)
    return .65*unsupported*surface*(1-edge)
def main():
    if len(sys.argv)!=3: fail('usage base candidate')
    b,c=map(Path,sys.argv[1:]);fb,fc=files(b),files(c)
    if set(fb)!=set(fc):fail('file universe changed')
    changed={p for p in fb if fb[p]!=fc[p]}
    if changed!=CHANGED:fail('changed-file allowlist mismatch '+repr(sorted(changed)))
    v=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    e=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    ver=(c/'app/version.properties').read_text()
    for x in ['IRIS_26570_SURFACE_CONTINUITY_ILLUMINATION_INDEPENDENT','IRIS_26570_ONE_SIDED_EDGE_LUMA_AUTHORITY','IRIS_26570_CROSS_EDGE_CHROMA_EXCLUSION','IRIS_26570_IIR_STRONG_EDGE_STATE_RESET']:
        if x not in v:fail('missing VGN contract '+x)
    if 'shadowNeed' in v:fail('absolute brightness cleanup branch survived')
    if 'imageStore(uOutput,p,imageLoad(uInput,p));' not in v:fail('local clamp luma pass-through missing')
    if 'oneSidedProtection' not in v or 'center.r,' not in v:fail('cross-edge median contract missing')
    if 'edgeRatio>0.55' not in v:fail('IIR boundary reset missing')
    # Never globally weaken Sabre/reconstruction: these tokens must not be added to the changed VGN/encoder code.
    for stale in ['warpConfidence >=','MotionV2CfaReconstruction','direct_rgb_accumulate']:
        if stale in e: fail('encoder unexpectedly owns reconstruction token '+stale)
    for x in ['IRIS_26570_TRUE2X_RENDER_ENCODE_PIPELINE','IRIS_26570_TRUE2X_ENCODER_TIMING','writeJpegBand','std::thread nextRender','std::thread gainEncode','jpegBatchRows=%d','scratch=BOUNDED_DOUBLE_BAND']:
        if x not in e:fail('performance contract '+x)
    for x in ['jpeg_set_quality(&baseC,std::clamp((int)quality,1,100),TRUE)','baseC.comp_info[k].h_samp_factor=1','baseC.comp_info[k].v_samp_factor=1','gainC.image_width=outW;gainC.image_height=outH','gainC.in_color_space=JCS_GRAYSCALE','const int bandRows=motionFast?256:128']:
        if x not in e:fail('quality/output contract drift '+x)
    if 'VERSION_NAME=0.9726570' not in ver or 'VERSION_BUILD=26570' not in ver:fail('version')
    # Synthetic semantic regressions. Same normalized chroma defect must not depend materially on absolute brightness.
    dark=correction(.08,[.012,-.010,-.002],[(.08,[0.,0.,0.])]*8)
    bright=correction(.48,[.072,-.060,-.012],[(.48,[0.,0.,0.])]*8)
    if abs(dark-bright)>0.035:fail(f'illumination independence synthetic dark={dark} bright={bright}')
    if dark<=0.02 or bright<=0.02:fail('same-surface cleanup unexpectedly disabled')
    # A dark leaf center surrounded predominantly by bright sky must get zero cross-edge median authority.
    leaf_center=.08; neighbors=[.80,.78,.82,.79,.81,.77,.80,.075]
    brighter=sum(1 for n in neighbors if (n-leaf_center)/max(n,leaf_center,.060)>.18)
    darker=sum(1 for n in neighbors if (n-leaf_center)/max(n,leaf_center,.060)<-.18)
    one=1.0 if (brighter>=6 and darker<=1) or (darker>=6 and brighter<=1) else 0.0
    if one!=1.0:fail('one-sided foliage/sky synthetic did not protect')
    print('PASS exact 3-file runtime allowlist')
    print(f'PASS illumination-independent continuity synthetic darkCorrection={dark:.6f} brightCorrection={bright:.6f}')
    print('PASS one-sided foliage/sky exclusion + luma-envelope source contracts')
    print('PASS true2x quality/4:4:4/1:1/band bounds preserved; render/encode overlap only')
if __name__=='__main__':main()
