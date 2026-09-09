#!/usr/bin/env python3
from pathlib import Path
import re, hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26616.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); root=C/'app'; base=B/'app'
errors=[]

def text(rel): return (root/rel).read_text()
def need(cond,msg):
    if not cond: errors.append(msg)
def count(rel,s): return text(rel).count(s)

post='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
p=text(post)
# Motion block between motion if and return must have sole Wronski owner and no retired nodes.
anchor=p.index('IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH')
start=p.index('if (mParameters.motionV2Active) {', anchor)
end=p.index('\n            return;', start)
motion=p[start:end]
need(motion.count('add(new MotionV2WronskiLtm())')==1,'Motion graph must add Wronski exactly once')
need('add(new MotionV2DisplayExposure())' not in motion,'Motion graph still adds DisplayExposure')
need('add(new IrisMotionToneControls())' not in motion,'Motion graph still adds manual tone controls')
need(motion.count('add(new MotionV2Render())')==1,'Motion graph render count != 1')
# Night remains inherited display owner and does not get Wronski.
night_start=p.index('if(mParameters.irisNightActive){')
night_end=p.index('\n            return;',night_start)
night=p[night_start:night_end]
need('add(new MotionV2WronskiLtm())' not in night,'Night accidentally adds Wronski')
need(night.count('add(new MotionV2DisplayExposure())')==1,'Night DisplayExposure changed/missing')

# DisplayExposure hard rejects Motion.
disp='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java'
need('if (basePipeline.mParameters.motionV2Active)' in text(disp),'DisplayExposure no Motion hard reject')
need('26616 Motion must use MotionV2WronskiLtm' in text(disp),'DisplayExposure reject marker missing')

# Exact Wronski constants / source pins.
ltm='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2WronskiLtm.java'
s=text(ltm)
for token in ['DISPLAY_MIP = 2','COARSE_MIP = 6','HIGHLIGHTS_EV = 2.0f','SHADOWS_EV = 1.5f','EXPOSURE_PREFERENCE_SIGMA = 5.0f','BOOST_LOCAL_CONTRAST = false','GUIDED_SPATIAL_SIGMA = 0.7f','LOW_LUMA_UNITY_THRESHOLD = 0.007f','07417fe2132975a193b49cbe9d16a6a02ab9dcc2','5087a8313493aa5eb230b82dc53dd636465d2751']:
    need(token in s,f'Wronski constant/source pin missing: {token}')
need('motionV2DisplayGain' in s,'Wronski global exposure parameter missing')
need('motionV2WronskiMidtoneMipGrid' in s and 'motionV2WronskiFusedLumaGrid' in s,'shared true2x fields missing')

# Exact exposure packing and half-float storage emulation.
exp='src/main/assets/shaders/motionv2/wronski_ltm_level2_exposures.glsl'
wgt='src/main/assets/shaders/motionv2/wronski_ltm_level2_weights.glsl'
for rel in [exp,wgt]:
    q=text(rel)
    need('packHalf2x16' in q and 'unpackHalf2x16' in q,f'{rel}: missing HalfFloat emulation')
    need('src*0.25' in q and 'src*2.8284271247461903' in q,f'{rel}: wrong exposure branches')
need('diff*diff*25.0' in text(wgt),'weight sigmaSq != 25')
need('dot(weights,vec3(1.0))+0.00001' in text(wgt),'level0 weight epsilon mismatch')

# Linked-demo blend epsilons and no local contrast boost.
coarse='src/main/assets/shaders/motionv2/wronski_ltm_blend_coarse.glsl'
lap='src/main/assets/shaders/motionv2/wronski_ltm_blend_laplacian.glsl'
need('dot(weights,vec3(1.0))+0.0001' in text(coarse),'coarse weight epsilon mismatch')
need('dot(weights,vec3(1.0))+0.00001' in text(lap),'lap weight epsilon mismatch')
need('abs(laplacians)' not in text(lap),'boostLocalContrast hybrid survived')

# Exact guided final constants and physical guide separation.
fin='src/main/assets/shaders/motionv2/wronski_ltm_final.glsl'
f=text(fin)
for tok in ['0.7*0.7','+0.00001','const float threshold=0.007','sqrt(max(ACESFilmicToneMapping']:
    need(tok in f,f'final combine missing exact token {tok}')
need('float physicalGuide=max(src.a,0.0)' in f,'Wronski recomputes physical guide instead of alpha')
need('physicalLuma(sourceP3)' not in f,'post-adaptive physical luma recompute survived')

adapt='src/main/assets/shaders/motionv2/adaptive_color_appearance_26616_wronski.glsl'
a=text(adapt)
need('out vec4 Output;' in a,'adaptive Motion shader not RGBA physical carrier')
need('float physicalGuide=max(y,pk(center))' in a,'adaptive pre-appearance physical guide missing')
need(a.count('max(physicalGuide,0.0)')==2,'adaptive physical alpha write count mismatch')
code_no_comments=re.sub(r'/\*.*?\*/','',a,flags=re.S)
for bad in ['displayGain','sceneWhite','outputExposureScale']:
    need(bad not in code_no_comments,f'adaptive Motion shader contains forbidden tone term {bad}')

# Motion render must bypass legacy projection when hdr handoff flag is set.
render='src/main/assets/shaders/motionv2/render.glsl'
r=text(render)
branch=re.search(r'if\(iris26592MotionHdrHandoff!=0\)\{(.*?)return;\s*\}',r,re.S)
need(branch is not None,'Motion render passthrough branch missing')
if branch:
    body=branch.group(1)
    for bad in ['mapExtendedLinearHeadroom','fitDisplayGamut','srgbEncode','outputExposureScale']:
        need(bad not in body,f'Motion render passthrough contains tone op {bad}')

# JNI true2x shared solve and zero Motion manual controls.
enc='src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
e=text(enc)
for tok in ['parameters.motionV2Active ? 0.0f','motionV2WronskiMidtoneMipGrid','motionV2WronskiFusedLumaGrid','IRIS_26616_TRUE2X_SHARED_WRONSKI_LTM=true']:
    need(tok in e,f'encoder true2x invariant missing: {tok}')

cpp='src/main/cpp/motionv2_jpeg444_jni.cpp'; c=text(cpp)
need('Vec3 physical;if(!profileColor(s,p,x,y,&physical))return false;' in c,'CPU uncached physical provenance not pre-adaptive')
need('Vec3 physical;if(!s.at(x,y,&physical))return false;' in c,'CPU cached physical provenance not pre-adaptive')
need('vec3 physical=irisProfileColor(p);vec3 c=irisAdaptive(p);' in c,'GPU physical provenance not pre-adaptive')
need('if(p.motionHdrHandoff){out->rgb=c;out->physicalGuide=' in c,'CPU Motion pre-render branch missing')
need('if(uMotionHdrHandoff!=0)return rgb; /* Wronski Motion never enters this Night helper. */' in c,'GPU old headroom helper not hard bypassed')
need('uMotionHdrHandoff!=0?irisWronskiFinal' in c,'GPU Motion not routed through Wronski final')
need('if(p.motionHdrHandoff){if(!iris26616WronskiFinal' in c,'CPU Motion not routed through Wronski final')

# UHDR Motion only reads physical guide, not SDR quotient.
gain='src/main/assets/shaders/motionv2/gainmap.glsl'; g=text(gain)
mb=re.search(r'if\(motionHdrHandoff!=0\)\{(.*?)\}else\{',g,re.S)
need(mb is not None,'Motion UHDR branch missing')
if mb:
    body=mb.group(1)
    need('hdrSample.a' in body,'Motion UHDR does not consume physical alpha')
    need('/(sdr' not in body and 'sdr+' not in body,'Motion UHDR reinterprets LTM as gain')

# No stale Motion owner telemetry.
for rel in [
'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',enc,render.replace('/assets/shaders/motionv2/render.glsl','/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')]:
    q=text(rel)
    need('displayGainOwner=MotionV2DisplayExposure' not in q,f'{rel}: stale DisplayExposure owner telemetry')
need('BASE_26598_MOTION' not in text(enc),'encoder stale Motion scene-white telemetry')

# Version exact.
v=text('version.properties')
need('VERSION_NAME=0.9726616' in v and 'VERSION_BUILD=26616' in v,'version/build mismatch')

if errors:
    print('SEMANTIC VALIDATION FAIL')
    for x in errors: print(' -',x)
    raise SystemExit(1)
print('SEMANTIC VALIDATION PASS')
print('ONE_LTM_OWNER=PASS')
print('WRONSKI_EXACT_DEFAULTS=PASS')
print('NORMAL_TRUE2X_SHARED_SOLVE=PASS')
print('PRE_APPEARANCE_PHYSICAL_GUIDE=PASS')
print('MOTION_UHDR_PHYSICAL_ONLY=PASS')
