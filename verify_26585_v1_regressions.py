#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math, re

def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
def smoothstep(a,b,x):
    if b<=a: return 1.0 if x>=b else 0.0
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)
def mix(a,b,t): return a+(b-a)*t
L=(0.22897456,0.69173852,0.07928691)
def lum(rgb): return sum(a*b for a,b in zip(rgb,L))
def map_headroom(g,sw):
    if g<=0.50:return g
    x=max(0.0,min(1.0,(g-0.50)/max(max(sw,0.55)-0.50,1e-6)))
    shaped=math.log(1.0+6.0*x)/math.log(7.0)
    return 0.50+(1.25-0.50)*shaped
def pre_gamut_peak(rgb,gain,sw):
    post=[max(v,0.0)*max(gain,1e-6) for v in rgb]
    y=max(lum(post),0.0); peak=max(post); guide=max(y,peak)
    if guide<=1e-7:return 0.0
    return peak*(map_headroom(guide,sw)/guide)*0.80
def chroma(rgb):
    y=lum(rgb); return y,[v-y for v in rgb]
def floor_limit(y,c):
    v=4.0
    for q in c:
        if q < -1e-7: v=min(v,(0.0-y)/q)
    return v
def safe_gain(rgb,gain,sw,request):
    y,c=chroma(rgb); hi=max(1.0,min(request,floor_limit(y,c)));lo=1.0
    for _ in range(7):
        mid=.5*(lo+hi); cand=[y+q*mid for q in c]
        if pre_gamut_peak(cand,gain,sw)<=.995:lo=mid
        else:hi=mid
    return lo

def required_white(display_gain,source_guide,target):
    base=max(1.0,min(6.0,.90*max(1.0,display_gain)))
    post=source_guide*max(display_gain,1e-6)
    if post<=.5:return base
    pre=max(.80,min(.995,target))/.80
    shape=max(0.0,min(1.0,(pre-.5)/(1.25-.5)))
    x=(math.exp(shape*math.log(7.0))-1.0)/6.0
    rw=.5+(post-.5)/max(x,1e-4)
    return max(base,min(12.0,rw))

def percentile_from_hist(vals,p,bins):
    hist=[0]*bins; mx=0.0
    for v in vals:
        mx=max(mx,v);i=max(0,min(bins-1,int(math.floor(min(v,7.999)*(bins/8.0)))));hist[i]+=1
    target=max(1,int(math.ceil(len(vals)*p)));acc=0;chosen=0
    for i,n in enumerate(hist):
        acc+=n
        if acc>=target:chosen=i;break
    return min(mx,(chosen+1.0)*(8.0/bins))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();root=Path(ns.candidate_root)
    matcher=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
    jav=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java').read_text()
    sh=(root/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
    render=root/'app/src/main/assets/shaders/motionv2/render.glsl'
    jin=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java'
    native=root/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
    ver=(root/'app/version.properties').read_text()
    for tok in ['IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER','histTotal * 0.98','gain, structuredGuide, 0.945f','structuredGuidePercentile=0.98','structuredHighlightTarget=0.945']:
        req(tok in matcher,'matcher contract '+tok)
    for tok in ['MAX_HIGHLIGHT_CHROMA_GAIN = 1.12f','motionV2ToneAdaptiveSceneWhite','glProg.setVar("sceneWhite", sceneWhite)','toneAwareHighlightChroma=true']:
        req(tok in jav,'appearance Java contract '+tok)
    for tok in ['IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION','uniform float sceneWhite;','legacyChromaGain','legacyHighlightSuppression','toneSafeHighlightGain','<= 0.995','min(1.12, highlightFloorGainLimit)','Output = vec3(centerLuma) + centerChroma * adaptiveChromaGain;']:
        req(tok in sh,'appearance shader contract '+tok)
    req('VERSION_NAME=0.9726585' in ver and 'VERSION_BUILD=26585' in ver,'version')
    req(hashlib.sha256(render.read_bytes()).hexdigest()=='e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71','render shader changed')
    req(hashlib.sha256(native.read_bytes()).hexdigest()=='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d','native GPU owner changed')
    req(hashlib.sha256(jin.read_bytes()).hexdigest()=='b7595a8a347fcfe3bdf9a0225ecb393406718adf1479c2a68a38eff8d962dbcd','26584 Jin cleanup changed')

    # Structured top tail: P98 and lower target must never ask for less headroom than 26584 P90/0.965.
    fixtures=[
      [0.45]*20+[0.70]*8+[0.92,0.95,0.99,1.04],
      [0.62]*40+[0.78]*10+[0.92]*4+[1.05,1.18],
      [0.85,0.88,0.90,0.92,0.95,0.98,1.02,1.06,1.10,1.14,1.18,1.22,1.26,1.30,1.34,1.38,1.42,1.46],
    ]
    for vals in fixtures:
        oldg=percentile_from_hist(vals,.90,64);newg=percentile_from_hist(vals,.98,256)
        oldw=required_white(4.7,oldg,.965);neww=required_white(4.7,newg,.945)
        req(neww+1e-7>=oldw,f'structured tail regressed {oldg=} {newg=} {oldw=} {neww=}')

    # Exact neutral cannot gain chroma regardless of headroom.
    neutral=(0.22,0.22,0.22); y,c=chroma(neutral)
    req(max(abs(q) for q in c)<1e-7,'neutral math')
    req(max(abs((y+q*1.12)-y) for q in c)<1e-7,'neutral changed')

    # Warm weak highlight that old projectedPeak rule would suppress can now retain supported direction.
    warm=(0.30,0.24,0.14); gain=4.0; sw=5.4
    projected=max(warm)*gain
    req(projected>=1.0,'fixture must be legacy-suppressed')
    basepeak=pre_gamut_peak(warm,gain,sw)
    req(basepeak<.94,'fixture must have post-tone headroom')
    sg=safe_gain(warm,gain,sw,1.12)
    req(sg>1.10 and sg<=1.12+1e-7,f'warm highlight not restored {sg=}')
    yy,cc=chroma(warm); cand=[yy+q*sg for q in cc]
    req(pre_gamut_peak(cand,gain,sw)<=.9950001,'tone-aware highlight exceeds pre-gamut safety')
    # Hue direction: chroma vector remains a positive scalar of source chroma.
    cc2=[v-lum(cand) for v in cand]
    ratios=[cc2[i]/cc[i] for i in range(3) if abs(cc[i])>1e-7]
    req(max(ratios)-min(ratios)<1e-5 and min(ratios)>=1.0,'hue/chroma direction changed')

    # No output amplification beyond requested 1.12 and no negative channel.
    for rgb in [(0.40,.32,.18),(.18,.15,.08),(.36,.30,.24),(.24,.18,.16)]:
        gg=safe_gain(rgb,5.0,6.0,1.12); yy,cc=chroma(rgb); out=[yy+q*gg for q in cc]
        req(1.0-1e-7<=gg<=1.12+1e-7,'gain bounds')
        req(min(out)>=-1e-7,'negative channel')
        req(pre_gamut_peak(out,5.0,6.0)<=.9950001,'post-tone gamut bound')
    print('PASS 26585 structured P98/0.945 tonal allocation floor')
    print('PASS 26585 exact-neutral preservation + tone-aware weak highlight chroma')
    print('PASS 26585 hue direction / zero-floor / <=1.12 / post-tone gamut safety')
    print('PASS frozen render/Jin/native owners')
if __name__=='__main__':main()
