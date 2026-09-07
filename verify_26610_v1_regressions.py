#!/usr/bin/env python3
from pathlib import Path
import math,sys

def fail(m): raise SystemExit('FAIL: '+m)
def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))

def short_weight(ordinary,physical,component,headroom,residual,literal_loss,effective_loss):
    rescue=min(headroom,component,residual)
    shared=min(physical,residual)
    censored=min(shared,rescue)
    # effective_loss remains evidence/telemetry only; only physical literal censorship may relax
    # the exposure-normalized ordinary NORMAL photometric term.
    physical_censor=clamp(literal_loss)
    return (1-physical_censor)*ordinary+physical_censor*censored
# Exact 26609 misses: literal clipping may not erase geometry, and effective-only loss may not
# bypass exposure-normalized ordinary NORMAL protection.
if short_weight(.9,1,1,1,0,1,1)!=0: fail('clipped core bypassed bad local residual')
if abs(short_weight(.37,.0,1,1,0,0,0)-.37)>1e-12: fail('noncensored path did not preserve exact ordinary weight')
if abs(short_weight(.37,1,1,1,1,0,1)-.37)>1e-12: fail('effective-only loss bypassed ordinary NORMAL protection')
if short_weight(.1,.8,.9,.95,.85,1,1) <= .75: fail('valid clipped core failed to survive')
if short_weight(.9,.4,1,1,1,1,1) > .400001: fail('physical cap exceeded')

def baseline(x):
    body=.40
    if x<=body:return x
    return body+.60*(x-body)/(x-body+.60)
def sdr(x,a,b):
    base=baseline(x); body=.40
    if x<=body or not (a>body+.02 and b>a+.01):return base
    if x<=a: y=body+clamp((x-body)/(a-body))*(.95-body)
    elif x<=b:y=.95+clamp((x-a)/(b-a))*(.995-.95)
    else:
        e=x-b;span=max(b-a,.05);y=.995+.005*e/(e+span)
    return y
# Body exact; source-domain map may move below old shoulder (26609 clamp-to-old could not).
for x in [0,.1,.25,.3999,.4]:
    if abs(sdr(x,3,4)-x)>1e-9: fail('body changed')
if not (sdr(.8,3,4) < baseline(.8)): fail('source-domain map still one-way post-shoulder stretch')
if abs(sdr(3,3,4)-.95)>1e-9 or abs(sdr(4,3,4)-.995)>1e-9: fail('p99/p998 SDR targets')
vals=[sdr(i/100,3,4) for i in range(0,1001)]
if any(vals[i+1]+1e-9<vals[i] for i in range(len(vals)-1)): fail('SDR map not monotonic')
if max(vals)>1.000001: fail('SDR map overflow')

def hdr(hdr_base,source,a,b,p99boost,p998boost):
    if hdr_base<=0 or not(a>.42 and b>a+.01): return hdr_base
    start=max(.40,.75*a)
    if source<=start:return hdr_base
    if source<=a:boost=1+(p99boost-1)*clamp((source-start)/(a-start))
    elif source<=b:boost=p99boost+(p998boost-p99boost)*clamp((source-a)/(b-a))
    else:boost=p998boost
    return hdr_base*boost
# Source position, not luma alone, owns tail activation.
a,b=2.0,3.0;p1=4.4/a;p2=max(p1,5.15/b)
if hdr(1.2,1.0,a,b,p1,p2)!=1.2: fail('UHDR activated below source tail')
if hdr(1.2,2.0,a,b,p1,p2) <= 1.2: fail('UHDR source-domain p99 did not activate')
if abs(hdr(a,a,a,b,p1,p2)-4.4)>1e-6: fail('UHDR p99 calibration')
# Same max-RGB guide with different luma still shares source-tail placement.
if not (hdr(.8,2.5,a,b,p1,p2)>.8 and hdr(1.3,2.5,a,b,p1,p2)>1.3): fail('UHDR source guide parity')

if len(sys.argv)>=2:
    # Build wrapper passes BASE then CANDIDATE; direct fixture use may pass only CANDIDATE.
    c=Path(sys.argv[2] if len(sys.argv)>=3 else sys.argv[1])
    render=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
    gain=(c/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
    adaptive=(c/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
    cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
    java=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    enc=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
    required={
      '1x SDR shader':(render,['targetP99=0.95','targetP998=0.995','iris26610SourceP99Final','iris26610SourceP998Final']),
      '1x UHDR shader':(gain,['4.40','5.15','iris26610SourceP99Final','iris26610SourceP998Final','sourceFinal=max3(hdrPositive)*hdrTargetScale']),
      'adaptive predictor':(adaptive,['targetP99=0.95','targetP998=0.995','iris26610SourceP99Final','iris26610SourceP998Final']),
      'true2x CPU/GPU':(cpp,['targetP99=0.95f,targetP998=0.995f','targetP99=0.95,targetP998=0.995','iris26610MapHdrTarget(float hdrBase,float sourceFinal','uIris26610SourceP99Final','uIris26610SourceP998Final']),
      'shared Java plan':(java,['IRIS_26610_SDR_P99_TARGET = 0.95f','IRIS_26610_SDR_P998_TARGET = 0.995f','IRIS_26610_HDR_P99_TARGET = 4.40f','IRIS_26610_HDR_P998_TARGET = 5.15f']),
      'true2x Java transport':(enc,['iris26610Tone.sourceP99Final','iris26610Tone.sourceP998Final','iris26610Tone.hdrP99Boost','iris26610Tone.hdrP998Boost'])}
    for label,(text,tokens) in required.items():
        for tok in tokens:
            if tok not in text: fail(label+' parity token '+tok)
print('PASS SHORT two-phase physical-censorship-only rescue, effective-loss ordinary identity, bad-residual rejection, physical cap and valid clipped-core recovery')
print('PASS source-domain SDR body identity, bidirectional de-plateau redistribution, p99/p998 targets and monotonicity')
print('PASS source-domain UHDR activation/calibration and 1x/SR shared-tail parity')
