#!/usr/bin/env python3
"""Independent CPU reference for exact RawLens LDR 0.70..0.99 camera-native white transition.
Local math tests are NOT substitutes for real GLSL compiler or device image quality.
"""
import sys,math,random
from build_26939_incremental import R,fail

# Direct mirror of RawLens SceneLinearColorProcessor.neutralizeCameraHighlight,
# pinned upstream commit 36e5141df568e74e2708dd4f50413b3aa51dab20.
def smooth(a,b,x):
    t=min(1.,max(0.,(x-a)/(b-a)))
    return t*t*(3.-2.*t)
def upstream(camera,white):
    v=tuple(max(0.,x) for x in camera)
    fade=smooth(.70,.99,max(v))
    return tuple(x+(w-x)*fade for x,w in zip(v,white)),fade

def iris(post,wb):
    # Equivalent to corrected=(cameraRGB mixed to normalized neutral)*wb.
    sensor=tuple(max(0.,x)/w for x,w in zip(post,wb))
    inv=tuple(1./w for w in wb)
    white=tuple(x/max(inv) for x in inv)
    fade=max(smooth(.70,.99,x) for x in sensor)
    native=tuple(x+(w-x)*fade for x,w in zip(sensor,white))
    return tuple(x*w for x,w in zip(native,wb)),fade

def verify():
    for wb in ((2.,1.,1.6),(2.4,1.,1.8),(.75,1.,1.4),(.3,.6,.9),(1.,1.,1.)):
        inv=tuple(1./w for w in wb)
        neutral=tuple(x/max(inv) for x in inv)
        # The real shader must numerically reproduce upstream for every
        # camera-native RGB vector; no physical mask or chroma gate input.
        rng=random.Random(26939)
        samples=[(0.,0.,0.),(.699999,.03,.02),(.70,.04,.02),
                 (.700001,.04,.02),(.77,.12,.69),(.81,.15,.75),
                 (.94,.19,.92),(.989999,.15,.95),(.99,.20,.96),
                 (1.,.20,.96),(1.2,.4,.3),(.25,.28,.16),
                 (.20,.65,.30),(.93,.88,.04)]
        samples.extend(tuple(rng.uniform(0,1.3) for _ in range(3)) for _ in range(25000))
        for src in samples:
            post=tuple(x*w for x,w in zip(src,wb))
            actual,fade=iris(post,wb)
            ref,t=upstream(src,neutral)
            expected=tuple(x*w for x,w in zip(ref,wb))
            if max(abs(a-b) for a,b in zip(actual,expected))>1e-12 or abs(fade-t)>1e-12:
                fail('26939 differs from original RawLens 0.70..0.99 white blend '+str((src,wb,actual,expected)))
            if not (0<=fade<=1):fail('invalid fade bounds')
    wb=(2.,1.,1.6)
    # Test what 26937/38 failed: bright magenta BEFORE any clipping witness.
    for src in ((.90,.23,.86),(.98,.18,.94),(.995,.2,.93),(.99,.12,.99)):
        post=tuple(x*w for x,w in zip(src,wb))
        corrected,fade=iris(post,wb)
        if fade<.6:fail('pink glint not addressed at early highlight shoulder '+str((src,fade)))
        if src[0]>=.99 and any(abs(x-1.)>1e-9 for x in corrected):fail('already visually blown pink not neutral white')
    # Earlier, visibly colored wall must remain colored if below shoulder.
    for yellow in ((.40,.33,.10),(.62,.52,.12),(.699,.69,.2)):
        post=tuple(x*w for x,w in zip(yellow,wb))
        corrected,fade=iris(post,wb)
        if fade!=0 or max(abs(a-b) for a,b in zip(corrected,post))>1e-12:fail('yellow wall shifted below highlight shoulder')
    # Above the shoulder true bright yellow obeys user's ANY visually clipped rule.
    yellow=(.99,.89,.07)
    corrected,fade=iris(tuple(x*w for x,w in zip(yellow,wb)),wb)
    if fade!=1 or max(corrected)-min(corrected)>1e-8:fail('bright yellow excluded from any-bright rule')
    # No discontinuity or dark border at either window boundary.
    src=(.40,.18,.38)
    for thresh in (.70,.99):
        samples=[]
        for delta in (-1e-5,0,1e-5):
            v=(thresh+delta,src[1],src[2]);o,t=iris(tuple(x*w for x,w in zip(v,wb)),wb)
            samples.append((o,t))
        for (a,x),(b,y) in zip(samples,samples[1:]):
            if max(abs(u-v) for u,v in zip(a,b))>2e-4 or abs(y-x)>1e-6:
                fail('visible threshold jump '+str((thresh,samples)))
    # Synthetic 2D neighborhood with a hot lamp and less-bright yellow wall:
    # test monotonic continuous analytic fade, not actual visual artifact removal.
    f=[iris((2.*v,.28,1.6*(v*.9)),wb)[1] for v in (.69+i*.001 for i in range(311))]
    if any(y+1e-10<x for x,y in zip(f,f[1:])) or max(y-x for x,y in zip(f,f[1:]))>.007:
        fail('abrupt or nonmonotonic highlight fade')
    shader=(R if '--live' in sys.argv else R/'handoff_payload_26939')/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt'
    s=shader.read_text().split('val shader = """',1)[1]
    for literal in ('vec3 whiteBlendRgb=smoothstep(vec3(0.70),vec3(0.99),cameraRgb);',
                    'float whiteBlend=max(whiteBlendRgb.r,max(whiteBlendRgb.g,whiteBlendRgb.b));',
                    'vec3 neutralCameraRgb=mix(cameraRgb,cameraWhite,whiteBlend);'):
        if s.count(literal)!=1:fail('shader no longer matches tested upstream RawLens expression')
    print('PASS 26939 independent 125000+ RawLens parity color inputs; early no-mask pink; yellow below/above shoulder; threshold continuity and normalized as-shot WB white')

if __name__=='__main__':
    try:verify()
    except Exception as e:
        print('26939 BLOCKED:',e,file=sys.stderr)
        sys.exit(1)
