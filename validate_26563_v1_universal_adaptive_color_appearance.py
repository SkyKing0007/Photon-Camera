#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math, re

EXPECTED_CHANGED={
'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'version.properties',
}
LUMA=(0.2126,0.7152,0.0722)

def sha(b): return hashlib.sha256(b).hexdigest()
def files(root):
    # Exact successful 26562 V1.1 audited-runtime comparison semantics:
    # app/src/main excluding separately-pinned native/vendor payloads, plus version/build files.
    # Repository-only app tests/.gitignore/proguard/etc are deliberately outside runtime authority.
    a=root/'app'; out={}
    main=a/'src/main'
    for p in main.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(a).as_posix()
        if rel.startswith('src/main/cpp/third_party_26507/') or rel.startswith('src/main/cpp/deps/'):
            continue
        out[rel]=sha(p.read_bytes())
    deps_gitignore=a/'src/main/cpp/deps/.gitignore'
    if deps_gitignore.is_file(): out[deps_gitignore.relative_to(a).as_posix()]=sha(deps_gitignore.read_bytes())
    for rel in ('version.properties','build.gradle'):
        q=a/rel
        if q.is_file(): out[rel]=sha(q.read_bytes())
    return out
def need(c,msg):
    if not c: raise SystemExit('FAIL: '+msg)
def text(root,rel): return (root/'app'/rel).read_text()
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def norm(a): return math.sqrt(dot(a,a))
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def luma(rgb): return dot(rgb,LUMA)
def chroma_vec(rgb):
    y=luma(rgb); return tuple(x-y for x in rgb)
def chroma_mag(rgb): return norm(chroma_vec(rgb))
def hue_dir(rgb):
    c=chroma_vec(rgb); n=norm(c); return tuple(x/n for x in c) if n>1e-12 else (0.0,0.0,0.0)

def component_limit(y,c):
    if c>1e-7: return max(1.0,(1.0-y)/c)
    if c<-1e-7: return max(1.0,(0.0-y)/c)
    return 4.0

def appearance(center,neighbors=None,display_gain=1.0):
    center=tuple(float(x) for x in center)
    if neighbors is None: neighbors=[center]*4
    y=luma(center); cc=chroma_vec(center); cm=norm(cc); rel=cm/max(y,0.08)
    chroma_sum=cc; mag_sum=cm; max_luma_delta=0.0
    for n in neighbors:
        n=tuple(float(x) for x in n); ny=luma(n); nc=chroma_vec(n)
        chroma_sum=add(chroma_sum,nc); mag_sum+=norm(nc); max_luma_delta=max(max_luma_delta,abs(ny-y))
    local_mean=mul(chroma_sum,0.2); local_mean_mag=mag_sum*0.2
    coherence=norm(local_mean)/max(local_mean_mag,1e-6)
    disagreement=norm(sub(cc,local_mean))
    neutral=smoothstep(0.0035,0.018,cm)
    rolloff=1.0-smoothstep(0.08,0.45,rel)
    dg=max(display_gain,1e-6); projected_y=y*dg; projected_peak=max(center)*dg
    shadow=smoothstep(0.015,0.075,projected_y)
    highlight=1.0-smoothstep(0.72,0.98,projected_peak)
    coherence_gate=smoothstep(0.45,0.82,coherence)
    agreement=1.0-smoothstep(0.018,0.085,disagreement)
    edge=1.0-smoothstep(0.025,0.11,max_luma_delta*dg)
    reliability=coherence_gate*agreement*edge
    requested=1.0+0.22*neutral*rolloff*shadow*highlight*reliability
    input_peak=max(center); limit=4.0
    if input_peak>=1.0 or projected_peak>=1.0: limit=1.0
    else:
        for c in cc: limit=min(limit,component_limit(y,c))
    gain=max(1.0,min(1.22,min(requested,limit)))
    if gain<=1.000001: out=center
    else: out=tuple(y+c*gain for c in cc)
    return out,gain,{'relative':rel,'projectedPeak':projected_peak,'reliability':reliability,'edge':edge,'coherence':coherence}

def semantic_tests():
    # 1 neutral input remains neutral/exact.
    neutral=(0.31,0.31,0.31); out,g,_=appearance(neutral)
    need(out==neutral and g==1.0,'neutral input changed')

    # 2 low-chroma legitimate input MUST get a meaningful positive boost.
    low=(0.35,0.32,0.31); low_out,low_gain,_=appearance(low)
    need(chroma_mag(low_out)>chroma_mag(low)*1.15 and low_gain>1.15,
         'explicit positive saturation semantic gate failed: legitimate weak color did not boost')

    # 3 medium chroma gets smaller proportional gain.
    med=(0.45,0.32,0.28); med_out,med_gain,_=appearance(med)
    need(med_gain>1.0 and med_gain<low_gain-0.10 and chroma_mag(med_out)>chroma_mag(med),
         'medium-chroma adaptive rolloff invalid')

    # 4 high chroma gets little/no boost.
    high=(0.70,0.20,0.15); high_out,high_gain,_=appearance(high)
    need(high_gain<=1.005 and abs(chroma_mag(high_out)-chroma_mag(high))<1e-7,
         'high-chroma anti-oversaturation gate failed')

    # 5 hue/chroma direction is preserved for boosted color.
    h0,h1=hue_dir(low),hue_dir(low_out)
    need(dot(h0,h1)>0.9999999,'hue/chroma direction shifted')

    # 6 Rec.709 linear luminance remains approximately exact.
    need(abs(luma(low_out)-luma(low))<1e-7 and abs(luma(med_out)-luma(med))<1e-7,
         'linear luminance changed')

    # 7 highlight proximity progressively reduces gain.
    mid=(0.55,0.52,0.51)
    _,g1,_=appearance(mid,display_gain=1.0)
    _,g15,_=appearance(mid,display_gain=1.5)
    _,g2,_=appearance(mid,display_gain=2.0)
    need(g1>g15>g2 and g2==1.0,'highlight/display-exposure gain suppression invalid')

    # 8 already clipped / extended linear colors cannot gain or create colored borders.
    pink_edge=(1.0,0.88,0.88); cyan_edge=(0.88,1.0,1.0); hdr=(1.15,0.93,0.90)
    for value in (pink_edge,cyan_edge,hdr):
        o,gg,_=appearance(value)
        need(gg==1.0 and o==value,'clipped/extended-linear pixel gained colorfulness')

    # 9 incoherent/mottled local chroma is not amplified.
    noisy=[(0.33,0.34,0.31),(0.34,0.30,0.34),(0.31,0.35,0.34),(0.36,0.30,0.31)]
    _,ng,meta=appearance(low,noisy)
    need(ng==1.0 and meta['coherence']<0.45,'incoherent chroma-noise gate failed')

    # 10 strong luminance boundary is protected (subject-border regression).
    edge=[(0.60,0.57,0.56),(0.10,0.09,0.085),(0.60,0.57,0.56),(0.10,0.09,0.085)]
    _,eg,meta=appearance(low,edge)
    need(eg==1.0 and meta['edge']==0.0,'strong luminance edge color-boost protection failed')

    # 11 in-gamut inputs may not create negative/>1 channels.
    for r in (0.08,0.20,0.45,0.70,0.92):
        for g0 in (0.08,0.25,0.50,0.80,0.94):
            for b in (0.08,0.30,0.55,0.85,0.96):
                c=(r,g0,b)
                if max(c)>=1.0: continue
                o,gg,_=appearance(c)
                need(1.0<=gg<=1.2200001,'adaptive gain exceeded hard bound')
                need(min(o)>=-1e-7 and max(o)<=1.0000001,'new out-of-gamut channel created')

    # 12 weak colors across hue directions all can boost; this is not a warm-color special case.
    for weak in ((0.35,0.32,0.31),(0.31,0.35,0.32),(0.31,0.32,0.35)):
        _,gg,_=appearance(weak); need(gg>1.10,'universal weak-color boost failed across hue directions')

    print('PASS 26563 semantic color tests: positive boost + adaptive rolloff + hue/luma + highlight/edge/noise/gamut safety')

def validate(base,cand):
    B,C=files(base),files(cand); changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
    need(changed==EXPECTED_CHANGED,f'changed-file allowlist mismatch unexpected={sorted(changed-EXPECTED_CHANGED)} missing={sorted(EXPECTED_CHANGED-changed)}')
    print('PASS exact 4-file 26563 runtime allowlist')

    # Protect the old cleanup and all 26562 reconstruction/DNG/lifecycle owners by byte equality.
    protected=[
      'src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
      'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
      'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
      'src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
      'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'src/main/assets/shaders/motionv2/color_transform.glsl',
      'src/main/assets/shaders/motionv2/display_exposure.glsl',
      'src/main/assets/shaders/motionv2/render.glsl',
      'src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java',
      'src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
      'src/main/java/com/particlesdevs/photoncamera/util/log/ActivityLifecycleMonitor.java',
    ]
    for rel in protected: need(B.get(rel)==C.get(rel),f'protected 26562 owner changed: {rel}')
    cleanup=text(cand,protected[0])
    need('IRIS_26561_UNIVERSAL_ADAPTIVE_COLOR' in cleanup and 'never boosts saturation' in cleanup,
         '26561 cleanup identity/semantic guard missing')
    print(f'PASS protected 26561 cleanup + 26562 SR/DNG/lifecycle/exposure/render invariance ({len(protected)} files)')

    post=text(cand,'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    need(post.count('add(new MotionV2AdaptiveColorAppearance());')==2,'appearance stage must exist exactly once in Night and once in Motion graph')
    # Exact order in Night branch.
    night_start=post.index('if(mParameters.irisNightActive)')
    night_end=post.index('return;',night_start)
    night=post[night_start:night_end]
    for a,b in [
      ('add(new MotionV2ColorTransform());','add(new MotionV2ViewfinderExposureMatcher());'),
      ('add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());'),
      ('add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());'),
      ('add(new MotionV2DisplayExposure());','add(new MotionV2Render());')]:
        need(night.index(a)<night.index(b),f'Night node order invalid {a} -> {b}')
    # Exact order in Motion branch.
    build_start=post.index('private void BuildDefaultPipeline()')
    motion_start=post.index('if (mParameters.motionV2Active)',build_start)
    motion_end=post.index('return;',motion_start)
    motion=post[motion_start:motion_end]
    for a,b in [
      ('add(new MotionV2ColorTransform());','add(new MotionV2ViewfinderExposureMatcher());'),
      ('add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());'),
      ('add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());'),
      ('add(new MotionV2DisplayExposure());','add(new MotionV2Render());')]:
        need(motion.index(a)<motion.index(b),f'Motion node order invalid {a} -> {b}')
    # SR does not select/bypass the appearance stage; both SR states use the same post branch.
    need('MotionV2AdaptiveColorAppearance' in night and 'MotionV2AdaptiveColorAppearance' in motion,
         'shared Motion/Night appearance coverage missing')
    print('PASS Motion/Night x SR OFF/ON converge through one shared 26563 stage exactly once')

    node=text(cand,'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java')
    shader=text(cand,'src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl')
    need('afterDeviceProfileColor=true' in node and 'beforeDisplayExposure=true' in node and 'dngAffected=false' in node,
         'new stage domain/ownership logging incomplete')
    need('motionV2SuperResOutputEnabled' not in re.sub(r'Log\.i\(.*?\);','',node,flags=re.S),
         'Super Res state conditionally controls appearance stage')
    for fragment in [
      'vec3 centerChroma = centerRgb - vec3(centerLuma);',
      'float requestedGain = 1.0 + 0.22',
      'float highlightGate = 1.0 - smoothstep(0.72, 0.98, projectedPeak);',
      'float reliability = coherenceGate * agreementGate * edgeGate;',
      'if (inputPeak >= 1.0 || projectedPeak >= 1.0)',
      'Output = vec3(centerLuma) + centerChroma * adaptiveChromaGain;',
    ]: need(fragment in shader,'shader semantic anchor missing: '+fragment)
    need('texture(' not in shader and 'mix(localMeanChroma' not in shader,'new stage appears to spatially mix neighbor color')
    # No device/manufacturer-specific appearance tuning.
    combined=node+'\n'+shader
    for forbidden in ('Samsung','Xiaomi','Motorola','\"Pixel\"','Build.MANUFACTURER','Build.MODEL','PreferenceKeys.getCameraID','PreferenceKeys.getCameraID()'):
        need(forbidden not in combined,'manufacturer/model/camera-specific branch token found: '+forbidden)
    print('PASS common-linear-sRGB universal appearance ownership; no manufacturer-specific tuning')

    ver=text(cand,'version.properties')
    need('VERSION_NAME=0.9726563' in ver and 'VERSION_BUILD=26563' in ver,'26563 version/build missing')
    semantic_tests()
    print('PASS 26563 focused architectural validation')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base',type=Path,nargs='?'); ap.add_argument('candidate',type=Path,nargs='?'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        semantic_tests(); return
    if not a.base or not a.candidate: raise SystemExit('base and candidate required')
    validate(a.base,a.candidate)
if __name__=='__main__': main()
