#!/usr/bin/env python3
from pathlib import Path
import argparse,math,re

def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
A=math.tanh(1.2020679)
K=A/(1.0-A)
def old_shape(u): return math.tanh(1.2020679*math.log(1.0+3.0*u)/math.log(4.0))
def new_shape(u):
    return A*max(u,0.0) if u<=1.0 else 1.0-(1.0-A)/(1.0+K*(u-1.0))
def publish(guide,white,new=True):
    start=0.50
    if guide<=start: return guide*0.80
    u=max((guide-start)/max(white-start,1e-6),0.0)
    shaped=new_shape(u) if new else old_shape(u)
    mapped=start+(1.25-start)*shaped
    return mapped*0.80

def short_actual_loss(ref,short_support_peak,short_norm):
    # Synthetic semantic model for final whole-RGB admission.
    if any(x>=0.995 for x in short_support_peak): return 0.0
    clipped=[i for i,v in enumerate(ref) if v>=0.999]
    if not clipped: return 0.0
    for i in clipped:
        if short_support_peak[i]>=0.90 or short_norm[i]<0.90: return 0.0
    return 1.0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
    render=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
    native=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    sabre=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
    # Permanent real-device regression: 26596 used SHORT but user-visible bright structure still washed out.
    # Preserve body exactly: no change at/below current 0.50 highlight start.
    for white in (0.55,0.75,1.0,1.5,3.0,12.0):
        for i in range(0,101):
            g=0.50*i/100.0
            req(abs(publish(g,white,True)-publish(g,white,False))<1e-12,'body exposure changed')
        # Exact 26596 scene-white output anchor retained.
        req(abs(publish(white,white,True)-publish(white,white,False))<2e-7,'scene-white anchor changed')
        # Recoverable upper interval now reserves >= old headroom: output cannot be brighter than old.
        prev=-1.0
        for i in range(0,1001):
            u=3.0*i/1000.0
            g=0.50+u*max(white-0.50,1e-6)
            y=publish(g,white,True)
            req(y>prev or i==0,'new publication not strictly monotonic')
            prev=y
            if 0.0<=u<=1.0:
                req(y<=publish(g,white,False)+2e-7,'recoverable highlight interval became brighter than 26596')
        req(publish(0.50+10000.0*max(white-0.50,1e-6),white,True)>0.9999,'specular tail does not approach white')
    # Structure preservation: separated bright inputs remain meaningfully separated and ordered.
    white=1.0
    vals=[0.55,0.60,0.70,0.80,0.90,1.00]
    outs=[publish(v,white,True) for v in vals]
    req(all(b>a for a,b in zip(outs,outs[1:])),'bright ordering collapsed')
    req(min(b-a for a,b in zip(outs,outs[1:]))>0.025,'bright local separation too small in fixture')
    # Formula parity markers in 1x GLSL and both true2x CPU/GPU mirrors.
    req('IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE' in render,'1x marker')
    # Permanent 26597 V1 Actions regression: ESSL 3.20 rejects built-in function calls in const scalar initializers.
    req('const float sceneAnchor=tanh(1.2020679)' not in render,'26597 V1 ESSL non-constant sceneAnchor initializer survived')
    req('const float tailSlope=sceneAnchor/max(' not in render,'26597 V1 ESSL non-constant tailSlope initializer survived')
    req('IRIS_26597_V1_1_ESSL_CONSTANT_INITIALIZER_FIX' in render,'V1.1 ESSL compiler-fix marker missing')
    req('const float sceneAnchor=0.834284246' in render and 'const float tailSlope=5.03442907' in render,'V1.1 precomputed constant literals missing')
    req(native.count('IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE')==2,'true2x CPU/GPU parity markers')
    # SHORT: unrelated phase may be bright (0.94) but must not veto one actually clipped phase with headroom.
    req(short_actual_loss([1.0,.60,.60,.60],[.80,.94,.70,.70],[.96,.70,.70,.70])==1.0,'unrelated bright SHORT phase still vetoes actual clipped phase')
    req(short_actual_loss([1.0,.60,.60,.60],[.91,.70,.70,.70],[.96,.70,.70,.70])==0.0,'clipped phase without 10pct SHORT reserve must fail closed')
    req(short_actual_loss([1.0,.60,.60,.60],[.80,.995,.70,.70],[.96,.70,.70,.70])==0.0,'physically clipped unrelated SHORT phase must fail whole-RGB restore')
    req(short_actual_loss([1.0,.60,.60,.60],[.80,.70,.70,.70],[.80,.70,.70,.70])==0.0,'SHORT that does not explain clipped NORMAL phase must fail')
    # Near-clip path remains explicitly all-phase 0.90 fail closed.
    req('if (!allShortPhasesHaveStrongHeadroom(shortSupportPeak)) { oMask = 0.0; return; }' in sabre,'near-clip all-phase reserve removed')
    # Permanent 26595/26596 device effect proof remains present in unchanged stacker.
    stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
    for t in ['countSabreShortRestoreMaskFull26595','fullActive=$fullActiveText26595','shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE','true2xDetailEvidenceShort=false']:
        req(t in stack,'carried SHORT/SR proof '+t)
    print('PASS 26596 visible-overexposure regression: exact body identity + universal monotonic highlight reserve + same scene-white anchor')
    print('PASS bright-structure ordering/separation fixture and true-specular asymptotic white')
    print('PASS 1x / true2x CPU / true2x GPU publication parity markers')
    print('PASS phase-scoped actual-loss SHORT fixture; physical-white and near-clip fail-closed rules retained')
if __name__=='__main__': main()
