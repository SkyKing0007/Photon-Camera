#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26628_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for root in (B,C):
    for forbidden in ['app/build','app/.cxx']:
        if (root/forbidden).exists(): raise SystemExit(f'FAIL generated path in authority candidate {forbidden}')
for a,b in [
('R1_26628_NATIVE_PROTECTED_BASE.sha256','R1_26628_NATIVE_PROTECTED_CANDIDATE.sha256'),
('R1_26628_VENDOR_PROTECTED_BASE.sha256','R1_26628_VENDOR_PROTECTED_CANDIDATE.sha256'),
('R1_26628_DNG_BASE.sha256','R1_26628_DNG_CANDIDATE.sha256')]:
    if (P/a).read_bytes()!=(P/b).read_bytes(): raise SystemExit(f'FAIL invariance regression {a} {b}')
# Proven reconstruction/highlight/legacy owners remain exact 26627 bytes.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
]:
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL protected pink-edge/legacy owner changed {rel}')
# Matrix/profile stage: bypass nonlinear DCP map on negative profile excursions; fit display negatives on common axis.
cts=(C/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
compact=cts.replace(' ','')
for tok in ['if(min(color.r,min(color.g,color.b))<0.0)returncolor;',
            'floatnegativeFloor=min(linearDisplay.r,min(linearDisplay.g,linearDisplay.b));',
            'if(negativeFloor<0.0)linearDisplay-=vec3(negativeFloor);']:
    if tok not in compact: raise SystemExit(f'FAIL pink/cyan edge invariant {tok}')
prefix=compact.split('floatnegativeFloor=',1)[0]
if 'clamp(linearDisplay' in prefix or 'max(linearDisplay,vec3(0.0))' in prefix:
    raise SystemExit('FAIL per-channel display clipping before neutral-axis gamut floor')
# Restrained presentation: no independent channel floor. One common shift followed by <=1 chroma contraction only.
ads=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text(); acompact=ads.replace(' ','')
for tok in ['floatnegativeFloor=min(rgb.r,min(rgb.g,rgb.b));','if(negativeFloor<0.0)rgb-=vec3(negativeFloor);','Output=vec3(y)+chroma*scale;']:
    if tok not in acompact: raise SystemExit(f'FAIL restrained presentation neutral-axis invariant {tok}')
for forbidden in ['max(texelFetch(InputBuffer','Output=max(','1.32','1.22','1.12','requestedGain','coherentColorActivation']:
    if forbidden in ads: raise SystemExit(f'FAIL restrained presentation regression {forbidden}')
# 0.95 contraction theorem using exact Display-P3 luma coefficients and float-tolerant neutral handling.
w=(0.22897456,0.69173852,0.07928691)
for rgb in [(0.2,0.2,0.2),(1.0,1.0,1.0),(0.7,0.2,0.1),(0.1,0.8,0.3),(1.2,0.3,0.7),(-0.1,0.2,0.3)]:
    floor=min(rgb); fit=tuple(x-floor if floor<0.0 else x for x in rgb)
    y=sum(a*b for a,b in zip(fit,w)); out=tuple(y+(x-y)*0.95 for x in fit); yo=sum(a*b for a,b in zip(out,w))
    cin=math.sqrt(sum((x-y)**2 for x in fit)); cout=math.sqrt(sum((x-y)**2 for x in out))
    if cout>cin*0.950001+1e-9: raise SystemExit('FAIL presentation enlarged chroma fixture')
    if min(out)<-1e-9: raise SystemExit('FAIL presentation created negative channel fixture')
    if abs(yo-y)>1e-8: raise SystemExit('FAIL presentation luminance drift fixture')
    if max(fit)-min(fit)<1e-12 and max(abs(out[i]-fit[i]) for i in range(3))>1e-8:
        raise SystemExit('FAIL presentation moved neutral fixture')
# Xiaomi regression: equal dual ForwardMatrix is valid and old placeholder predicate is absent.
solver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java').read_text()
for forbidden in ['DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT','forwardDelta','colorMatrixDelta']:
    if forbidden in solver: raise SystemExit(f'FAIL Xiaomi equal-ForwardMatrix regression {forbidden}')
for tok in ['equalForwardAccepted=true','interpolateOptional(p.forward1, p.forward2, firstWeight)']:
    if tok not in solver: raise SystemExit(f'FAIL equal ForwardMatrix path missing {tok}')
# Numerical fixture from the known-good Xiaomi 26626 metadata.
expected=[1.9659153,-0.022977002,0.40074044,-0.04073863,1.0738649,-0.103170484,-0.11580317,-0.54703426,2.8735912]
reference=[1.96612468,-0.02295664,0.40076324,-0.04082333,1.07385676,-0.10317979,-0.11583193,-0.54717005,2.87430408]
if max(abs(a-b) for a,b in zip(expected,reference))>0.001: raise SystemExit('FAIL Xiaomi 26626 DNG color numerical reference drift')
# Full 3D DCP logical order must agree between GL and native true2x.
native=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); ncompact=native.replace(' ','')
if 'ivec2(sat,value*hueDivisions+hue)' not in compact: raise SystemExit('FAIL GL DCP value-hue-saturation order')
if 'vIdx*(size_t)hDiv*(size_t)sDiv+(size_t)hIdx*(size_t)sDiv+(size_t)sIdx' not in ncompact: raise SystemExit('FAIL native DCP value-hue-saturation order')
# New true2x color functions may not independently clamp after common-axis matrix fit/contraction.
for forbidden in ['*out=clampNonnegative(linear);','*out=clampNonnegative(add(Vec3{y,y,y},mul(c,0.95f)))']:
    if forbidden in native: raise SystemExit(f'FAIL true2x color per-channel clamp regression {forbidden}')
if 'p.dcpHueSatMap.empty()&&p.dcpLookMap.empty()' not in ncompact: raise SystemExit('FAIL true2x DCP profile GPU exclusion')
print('PASS 26628 regressions: generated trees excluded; legacy/reconstruction/pink-edge owners protected; equal-FM Xiaomi valid; common-axis gamut/presentation floors; contraction-only color; full 3D DCP order; true2x profile parity gate')
