#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26616_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Proven successful 26615 upstream physical reconstruction/Sabre/SHORT/CFA components remain byte-identical.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl',
'app/src/main/assets/shaders/motionv2/cfa_demosaic.glsl',
'app/src/main/assets/shaders/motionv2/cfa_reconstruct_pack.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl']
for rel in protected:
    if not (B/rel).is_file() or not (C/rel).is_file() or h(B/rel)!=h(C/rel): raise SystemExit('26615 protected physical/runtime inheritance changed: '+rel)
# DNG exact unchanged.
for line in (P/'R1_26616_DNG_BASE.sha256').read_text().splitlines():
    sha,rel=line.split('  ',1)
    if h(C/rel)!=sha: raise SystemExit('DNG regression '+rel)
# Permanent repository hygiene regressions.
for root in (B,C):
    if (root/'app/build').exists() and any(p.is_file() for p in (root/'app/build').rglob('*')): raise SystemExit('generated app/build counted as runtime')
    if (root/'app/.cxx').exists() and any(p.is_file() for p in (root/'app/.cxx').rglob('*')): raise SystemExit('generated app/.cxx counted as runtime')
# Exact Wronski source/default regression pins.
ltm=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2WronskiLtm.java').read_text()
for tok in ['DISPLAY_MIP = 2','COARSE_MIP = 6','HIGHLIGHTS_EV = 2.0f','SHADOWS_EV = 1.5f','EXPOSURE_PREFERENCE_SIGMA = 5.0f','BOOST_LOCAL_CONTRAST = false','GUIDED_SPATIAL_SIGMA = 0.7f','LOW_LUMA_UNITY_THRESHOLD = 0.007f','07417fe2132975a193b49cbe9d16a6a02ab9dcc2','5087a8313493aa5eb230b82dc53dd636465d2751']:
    if tok not in ltm: raise SystemExit('Wronski exact-default regression '+tok)
# One owner: old spatial presentation and manual post-LTM tone cannot re-enter Motion graph.
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
a=post.index('IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH'); s=post.index('if (mParameters.motionV2Active) {',a); e=post.index('\n            return;',s); motion=post[s:e]
if motion.count('add(new MotionV2WronskiLtm())')!=1: raise SystemExit('Wronski owner count regression')
for bad in ['add(new MotionV2DisplayExposure())','add(new IrisMotionToneControls())']:
    if bad in motion: raise SystemExit('hybrid Motion tone owner regression '+bad)
# Physical provenance may not be regenerated from post-appearance RGB.
adapt=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26616_wronski.glsl').read_text(); final=(C/'app/src/main/assets/shaders/motionv2/wronski_ltm_final.glsl').read_text(); gain=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
if 'float physicalGuide=max(y,pk(center))' not in adapt or 'float physicalGuide=max(src.a,0.0)' not in final: raise SystemExit('pre-appearance physical provenance regression')
mb=re.search(r'if\(motionHdrHandoff!=0\)\{(.*?)\}else\{',gain,re.S)
if not mb or 'hdrSample.a' not in mb.group(1) or '/(sdr' in mb.group(1): raise SystemExit('Motion UHDR physical-only regression')
# true2x must consume frozen 1x fields and not solve independently.
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['iris26616WronskiFinal','uWronskiField','wronskiMidtone','wronskiFused']:
    if tok not in cpp: raise SystemExit('true2x shared Wronski regression '+tok)

# Permanent R1 real-glslang failure regression: the viewfinder embedded-shader
# extractor must never terminate on a `);` sequence that occurs inside the GLSL
# Java string.  Failed Actions R1 generated a 5-line probe ending after `out vec4 Output;`.
sv=(P/'verify_26616_shaders.py').read_text()
if "end=j.index(');',anchor)" in sv:
    raise SystemExit('viewfinder probe extractor regression: raw ); search restored')
for tok in ['IRIS_26616_R11_VIEWFINDER_PROBE_EXTRACTOR_REGRESSION','java_call_end','vec2(1.0)));}']:
    if tok not in sv:
        raise SystemExit('viewfinder probe extractor repair regression '+tok)


# Permanent R1.1 Actions failure regression: infrastructure-mechanics comparison
# must recognize the successful 26615 R1.1 handoff-scope git-diff command even
# though its authority variable is HANDOFF_PARENT_COMMIT while 26616 correctly
# uses BASE_SUCCESS_COMMIT.  Compare the command family, not that variable name.
infra=(P/'verify_26616_infrastructure.py').read_text()
if "'git diff --name-only \"$BASE_SUCCESS_COMMIT\"..HEAD'" in infra:
    raise SystemExit('infrastructure comparator regression: authority-variable-specific scope matcher restored')
if "'git diff --name-only '" not in infra:
    raise SystemExit('infrastructure comparator regression: generic handoff-scope matcher missing')

# No semantic scene classifiers.
changed=[x for x in (P/'R1_26616_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
for rel in changed:
    q=C/rel
    if q.suffix.lower() not in {'.java','.kt','.cpp','.h','.glsl','.properties'}: continue
    ss=q.read_text(errors='ignore').lower()
    for token in ['ceilingclassifier','curtainclassifier','windowclassifier','chandelierclassifier']:
        if token in ss: raise SystemExit('scene-specific classifier '+rel)
print('PASS 26616 permanent regressions: 26615 physical/Sabre/SHORT/CFA/DNG inherited; exact Wronski owner; no hybrid tone; shared true2x; physical-only UHDR; R1 viewfinder-probe truncation blocked; R1.1 infrastructure-scope comparator false positive blocked')
