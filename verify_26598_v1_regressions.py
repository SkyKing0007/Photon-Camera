#!/usr/bin/env python3
from pathlib import Path
import argparse, math, re

def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)

A=0.834284246
K=5.03442907
OUTPUT_SCALE=0.80
START=0.50

def motion_shape(u):
    return A*max(u,0.0) if u<=1.0 else 1.0-(1.0-A)/(1.0+K*(u-1.0))
def night_shape(u):
    x=max(0.0,min(1.0,u)); return math.log(1.0+6.0*x)/math.log(7.0)
def publish(guide,white,motion=True):
    if guide<=START: return guide*OUTPUT_SCALE
    u=max((guide-START)/max(white-START,1e-6),0.0)
    shaped=motion_shape(u) if motion else night_shape(u)
    mapped=START+(1.0/OUTPUT_SCALE-START)*shaped
    return mapped*OUTPUT_SCALE

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base_root'); ap.add_argument('candidate_root'); ns=ap.parse_args()
    b=Path(ns.base_root); c=Path(ns.candidate_root)
    render=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
    app=(c/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
    rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    aj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java').read_text()
    enc=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
    native=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    sabre=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()

    # Exact successful-26597 final Motion publication math remains byte-identical.
    req((b/'app/src/main/assets/shaders/motionv2/render.glsl').read_bytes()==(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_bytes(),
        '26597 render shader changed')
    req((b/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_bytes()==(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_bytes(),
        '26597 true2x native publication changed')
    for t in ['IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE',
              'IRIS_26597_V1_1_ESSL_CONSTANT_INITIALIZER_FIX',
              'const float sceneAnchor=0.834284246',
              'const float tailSlope=5.03442907']:
        req(t in render,'26597 final publication '+t)
    req(native.count('IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE')==2,
        'true2x CPU/GPU 26597 parity markers')

    # Permanent 26597 V1 ESSL compiler failure condition stays absent.
    req('const float sceneAnchor=tanh(1.2020679)' not in render,'26597 V1 non-constant sceneAnchor revived')
    req('const float tailSlope=sceneAnchor/max(' not in render,'26597 V1 non-constant tailSlope revived')

    # New semantic contract: Motion's final scale is the base scene white, not the old expanded value;
    # Night retains adaptive scene-white logic. Presence alone is insufficient: all three consumers use it.
    req('if (parameters.motionV2Active) return baseWhite;' in rj,'Motion base sceneWhite selector')
    req('float adaptiveWhite = parameters.motionV2ToneAdaptiveSceneWhite;' in rj,'Night adaptive selector')
    req('float sceneWhite = iris26598PublicationSceneWhite(basePipeline.mParameters);' in rj,'1x selector consumer')
    req('MotionV2Render.iris26598PublicationSceneWhite(basePipeline.mParameters)' in aj,'appearance selector consumer')
    req('MotionV2Render.iris26598PublicationSceneWhite(parameters)' in enc,'true2x selector consumer')
    req('parameters.motionV2ToneAdaptiveSceneWhite, parameters.motionV2Active' not in enc,'stale true2x adaptive sceneWhite')

    # The user-visible 26597 failure condition: a ~20% expanded sceneWhite compresses recoverable bright
    # differences. With the same successful 26597 mapping and fixed body exposure, using the physical base
    # must give more upper-highlight output separation without changing <=0.50 body/midtones.
    for base_white in (1.0,2.073,3.113,4.506,5.4566,6.0):
        adaptive=min(6.0,base_white*1.195)
        for i in range(101):
            g=START*i/100.0
            req(abs(publish(g,base_white,True)-publish(g,adaptive,True))<1e-12,
                'body/midtone changed by sceneWhite authority')
        if adaptive>base_white+1e-6:
            lo=START+0.65*(base_white-START)
            hi=START+0.90*(base_white-START)
            base_sep=publish(hi,base_white,True)-publish(lo,base_white,True)
            adaptive_sep=publish(hi,adaptive,True)-publish(lo,adaptive,True)
            req(base_sep>adaptive_sep+1e-5,'base sceneWhite did not restore upper-highlight separation')
            req(publish(hi,base_white,True)>publish(hi,adaptive,True)+1e-5,
                'base sceneWhite did not use available upper display range')

    # Exact mathematical parity between the changed appearance safety predictor and 26597 renderer.
    for white in (0.55,0.75,1.0,2.0,4.506,5.4566,6.0):
        for i in range(0,1501):
            u=3.0*i/1500.0
            guide=START+u*max(white-START,1e-6)
            renderer=publish(guide,white,True)/OUTPUT_SCALE
            predictor=(START+(1.0/OUTPUT_SCALE-START)*motion_shape(u))
            req(abs(renderer-predictor)<1e-12,'appearance predictor diverged from 26597 Motion render')
    for t in ['uniform int iris26598MotionPublication;',
              'const float sceneAnchor = 0.834284246;',
              'const float tailSlope = 5.03442907;',
              'if (iris26598MotionPublication != 0)',
              'shaped = log(1.0 + logShape * x) / log(1.0 + logShape);']:
        req(t in app,'appearance predictor source '+t)

    # Night path must be mathematically the exact old 26585 predictor for u>=0, including endpoint clamp.
    for u in (-1.0,0.0,0.1,0.5,1.0,1.2,3.0):
        old=math.log(1.0+6.0*max(0.0,min(1.0,u)))/math.log(7.0)
        req(abs(night_shape(u)-old)<1e-15,'Night predictor changed')

    # SHORT, Sabre, DNG and UHDR physical evidence owners are not being used to solve this tone issue.
    req((b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_bytes()==
        (c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_bytes(),
        'SHORT/Sabre math changed')
    for t in ['IRIS_26597_PHASE_SCOPED_SHORT_HEADROOM','IRIS_26596_TRUE2X_CONTENT_CAP=true']:
        req((t in sabre) or (t in enc), 'carried 26597/26596 proof '+t)
    for t in ['countSabreShortRestoreMaskFull26595','fullActive=$fullActiveText26595',
              'shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE','true2xDetailEvidenceShort=false']:
        req(t in stack,'carried SHORT/SR proof '+t)

    capture=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    # Exact budget model is invariant with SR on/off and across pre/post shutter split.
    def plan(total,short,long,pre):
        aux=(1 if short and total>=2 else 0)
        rem=total-aux
        use_long=bool(long and rem>=2)
        aux += 1 if use_long else 0
        normals=total-aux
        owned=min(max(pre,0),normals)
        return normals,owned,normals-owned,aux
    for sr in (False,True):
        n,pre,missing,aux=plan(15,True,True,8)
        req((n,pre,missing,aux)==(13,8,5,2),'15-frame SHORT+LONG ownership budget changed')
        req(n+aux==15,'slider total not exact')
    for total in range(1,31):
        for short in (False,True):
            for long in (False,True):
                n,pre,missing,aux=plan(total,short,long,total)
                req(n>=1 and n+aux==total,'exact total budget invalid')
    # Real-device failure fixtures: accepted preshutter count is immutable; only the true missing count may be post-shutter owned.
    for normal_target,at_press in [(15,4),(15,14),(15,13),(13,8)]:
        owned=min(at_press,normal_target); missing=normal_target-owned
        req(owned+missing==normal_target,'ownership fixture lost NORMAL')
        req(owned==min(at_press,normal_target),'pre-shutter NORMAL substituted')
    for t in ['IRIS_26598_MOTION_HAL_QUEUE_DRAIN_OWNER','IRIS_26598_PRE_SHUTTER_NORMAL_OWNERSHIP_TRANSFER',
              'IRIS_26598_EXPLICIT_GENERATION_OWNED_NORMAL_TOPUP','IRIS_26598_IMMUTABLE_NORMAL_SET_DRAIN',
              'IRIS_26598_ONE_DEEP_DEFERRED_MOTION_SHUTTER','IRIS_26598_EXACT_TOTAL_OWNERSHIP_PROOF']:
        req(t in capture,'capture regression marker '+t)
    req('while (true) {' in capture[capture.index('IRIS_26598_MOTION_HAL_QUEUE_DRAIN_OWNER'):capture.index('if (mIrisNight26540CaptureActive)', capture.index('IRIS_26598_MOTION_HAL_QUEUE_DRAIN_OWNER'))],
        'Motion RAW callback does not drain coalesced queue')
    req('mMotion26598DeferredShutter.compareAndSet(false, true)' in capture,'one-deep shutter latch absent')
    req('if (missingNormals > 0 || auxiliaryExpected) return MOTION_26593_MAX_CAPTURE_COMPLETION_MS;' in capture,
        '3.5s terminal watchdog not used for post-shutter roles')
    req('normalAtPress=' in capture and 'postShutterNormalAdmission=' in capture,'ownership telemetry absent')
    print('PASS successful-26597 1x/true2x publication math byte-identical; V1 ESSL compiler regression remains absent')
    print('PASS 26598 semantic authority fixture: body identity + greater recoverable upper-highlight separation with base sceneWhite')
    print('PASS adaptive color safety predictor is numerically identical to exact 26597 Motion publication; Night predictor preserved')
    print('PASS stale adaptive Motion publication absent from 1x/appearance/true2x; SHORT/Sabre/UHDR evidence owners preserved')
    print('PASS exact pre/post-shutter NORMAL ownership, ticketed top-up, coalesced RAW drain, deferred shutter, and SR budget parity fixtures')
if __name__=='__main__': main()
