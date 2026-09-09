#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26617.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent; base=B/'app'; root=C/'app'; errors=[]
def text(rel): return (root/rel).read_text()
def btext(rel): return (base/rel).read_text()
def need(cond,msg):
    if not cond: errors.append(msg)

def extract_method(src, marker):
    start=src.index(marker); brace=src.index('{',start); depth=0
    for i in range(brace,len(src)):
        if src[i]=='{': depth+=1
        elif src[i]=='}':
            depth-=1
            if depth==0:return src[start:i+1]
    raise ValueError(marker)

matcher='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
m=text(matcher); bm=btext(matcher)
# Preserve successful 26616 global exposure placement; adaptation supplies only synthetic branch span.
need('solvedEv = clamp(rawSolvedEv * matchStrength, MIN_EV, MAX_EV);' in m,'Motion global 65%-strength exposure solve changed')
need(extract_method(m,'private float solveBounded(')==extract_method(bm,'private float solveBounded('),'global viewfinder solveBounded math changed from 26616')
for tok in [
 'WRONSKI_DEFAULT_SHADOW_EV = 1.5f','WRONSKI_DEFAULT_HIGHLIGHT_EV = 2.0f',
 'WRONSKI_MAX_BRANCH_EV = 6.0f','WRONSKI_SHADOW_PERCENTILE = 0.375f',
 'WRONSKI_HIGHLIGHT_PERCENTILE = 0.99f','WRONSKI_PREFERRED_LIGHTNESS = 0.5f',
 'WRONSKI_BROAD_HIGHLIGHT_START = 0.015f','WRONSKI_BROAD_HIGHLIGHT_FULL = 0.050f',
 'solveAdaptiveWronskiBranches(gain)','solvePreferredBranchMagnitude','for (int i = 0; i < 18; i++)',
 'Math.max(s.r, Math.max(s.g, s.b)) > 1.0f','compactHighlightKeeps26616=true boostLocalContrast=false']:
    need(tok in m,'adaptive Wronski branch solver token missing: '+tok)
need('WRONSKI_DEFAULT_SHADOW_EV = 4.0f' not in m and 'WRONSKI_DEFAULT_HIGHLIGHT_EV = 4.0f' not in m,'fixed +/-4EV policy restored')
need('motionV2WronskiBroadHighlightFraction' in m,'physical broad-highlight evidence not persisted')

params='src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'; ps=text(params)
for tok in ['motionV2WronskiShadowEv = 1.5f','motionV2WronskiHighlightEv = 2.0f','motionV2WronskiBroadHighlightFraction = 0.0f']:
    need(tok in ps,'Parameters adaptive branch field/default missing: '+tok)

ltm='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2WronskiLtm.java'; s=text(ltm)
for tok in ['DISPLAY_MIP = 2','COARSE_MIP = 6','DEFAULT_HIGHLIGHTS_EV = 2.0f','DEFAULT_SHADOWS_EV = 1.5f','MAX_BRANCH_EV = 6.0f','EXPOSURE_PREFERENCE_SIGMA = 5.0f','BOOST_LOCAL_CONTRAST = false','GUIDED_SPATIAL_SIGMA = 0.7f','LOW_LUMA_UNITY_THRESHOLD = 0.007f','motionV2WronskiShadowEv','motionV2WronskiHighlightEv','Math.pow(2.0, shadowEv)','Math.pow(2.0, -highlightEv)','07417fe2132975a193b49cbe9d16a6a02ab9dcc2','5087a8313493aa5eb230b82dc53dd636465d2751']:
    need(tok in s,'26617 LTM invariant missing: '+tok)
need('glProg.setTexture("BroadWeights", weights[COARSE_MIP - 1]);' in s,'mip5 broad exposure authority binding missing')
need('fine <= COARSE_MIP - 2 ? 1.0f : 0.0f' in s,'mips4..2 broad-authority routing missing')
need('motionV2WronskiMidtoneMipGrid' in s and 'motionV2WronskiFusedLumaGrid' in s,'shared true2x mip2 solve missing')
need('physicalHdrGuide=alphaPreLtm' in s,'physical HDR alpha separation telemetry missing')

exp='src/main/assets/shaders/motionv2/wronski_ltm_level2_exposures.glsl'; ex=text(exp)
wgt='src/main/assets/shaders/motionv2/wronski_ltm_level2_weights.glsl'; wg=text(wgt)
for rel,q in [(exp,ex),(wgt,wg)]:
    for tok in ['uniform float highlightExposureScale;','uniform float shadowExposureScale;','packHalf2x16','unpackHalf2x16']:
        need(tok in q,f'{rel}: missing {tok}')
    need('src*0.25' not in q and 'src*2.8284271247461903' not in q,f'{rel}: fixed 26616 branches survived')
need('src*highlightExposureScale' in ex and 'src*shadowExposureScale' in ex,'exposure shader dynamic branches missing')
need('src*highlightExposureScale' in wg and 'src*shadowExposureScale' in wg,'weight shader dynamic branches missing')
need('diff*diff*25.0' in wg,'Wronski sigma=5 changed')
need('dot(weights,vec3(1.0))+0.00001' in wg,'source weight epsilon changed')

lap='src/main/assets/shaders/motionv2/wronski_ltm_blend_laplacian.glsl'; lp=text(lap)
for tok in ['uniform sampler2D BroadWeights;','uniform float useBroadWeightAuthority;','vec3 broadWeights=texture(BroadWeights,uv).rgb;','mix(fineWeights,broadWeights,clamp(useBroadWeightAuthority,0.0,1.0))','laplacians*weights']:
    need(tok in lp,'structure-stable Laplacian token missing: '+tok)
need('abs(laplacians)' not in lp,'boost local contrast must remain disabled')

# Critical 26616 owners not in this runtime allowlist must remain byte-identical.
protected=[
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
 'src/main/assets/shaders/motionv2/wronski_ltm_final.glsl',
 'src/main/assets/shaders/motionv2/wronski_ltm_blend_coarse.glsl',
 'src/main/assets/shaders/motionv2/adaptive_color_appearance_26616_wronski.glsl',
 'src/main/assets/shaders/motionv2/gainmap.glsl',
 'src/main/assets/shaders/motionv2/render.glsl',
 'src/main/cpp/motionv2_jpeg444_jni.cpp',
 'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
for rel in protected:
    need((base/rel).read_bytes()==(root/rel).read_bytes(),'successful 26616 protected owner changed: '+rel)

post=text(protected[0]); anchor=post.index('IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH'); st=post.index('if (mParameters.motionV2Active) {',anchor); en=post.index('\n            return;',st); motion=post[st:en]
need(motion.count('add(new MotionV2WronskiLtm())')==1,'Motion one-LTM owner lost')
need('add(new MotionV2DisplayExposure())' not in motion,'Motion legacy DisplayExposure restored')
need('add(new IrisMotionToneControls())' not in motion,'Motion manual tone owner restored')

# No semantic scene classifier; the policy must generalize from signal statistics.
changed=[x for x in (P/'R1_26617_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
for rel in changed:
    q=C/rel
    if q.suffix.lower() in {'.java','.glsl'}:
        ss=q.read_text(errors='ignore').lower()
        for bad in ['ceilingclassifier','curtainclassifier','playpenclassifier','backdoorclassifier','plantshelfclassifier']:
            need(bad not in ss,'scene-specific classifier introduced: '+bad+' '+rel)

v=text('version.properties'); need('VERSION_NAME=0.9726617' in v and 'VERSION_BUILD=26617' in v,'version/build mismatch')
if errors:
    print('SEMANTIC VALIDATION FAIL')
    for x in errors: print(' -',x)
    raise SystemExit(1)
print('SEMANTIC VALIDATION PASS')
print('ONE_LTM_OWNER=PASS')
print('ADAPTIVE_WRONSKI_RANGE=PASS')
print('COMPACT_HIGHLIGHT_26616_INHERITANCE=PASS')
print('STRUCTURE_STABLE_FINE_BANDS=PASS')
print('NORMAL_TRUE2X_SHARED_SOLVE=PASS')
print('PHYSICAL_UHDR_SEPARATION=PASS')
