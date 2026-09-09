#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26617_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent

def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
# Exact observed 26616 sample failure conditions become permanent classification regressions.
start=0.015; full=0.050
scenes={'playpen_chandelier':0.0035807292,'backdoor':0.006184896,'plant_curtain':0.07845052}
strength={k:smoothstep(start,full,v) for k,v in scenes.items()}
if strength['playpen_chandelier']!=0.0: raise SystemExit('ceiling/X regression: compact chandelier would expand highlight branch')
if strength['backdoor']!=0.0: raise SystemExit('backdoor compact highlight population would expand highlight branch')
if strength['plant_curtain']!=1.0: raise SystemExit('curtain regression: broad physical highlight population not full adaptive authority')

m=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
l=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2WronskiLtm.java').read_text()
s=(C/'app/src/main/assets/shaders/motionv2/wronski_ltm_blend_laplacian.glsl').read_text()
for tok in ['WRONSKI_BROAD_HIGHLIGHT_START = 0.015f','WRONSKI_BROAD_HIGHLIGHT_FULL = 0.050f','WRONSKI_SHADOW_PERCENTILE = 0.375f','WRONSKI_HIGHLIGHT_PERCENTILE = 0.99f','WRONSKI_PREFERRED_LIGHTNESS = 0.5f']:
    if tok not in m: raise SystemExit('adaptive-range regression '+tok)
if 'BOOST_LOCAL_CONTRAST = false' not in l or 'abs(laplacians)' in s: raise SystemExit('boost-local-contrast regression')
if 'fine <= COARSE_MIP - 2 ? 1.0f : 0.0f' not in l or 'BroadWeights' not in s: raise SystemExit('playpen edge-tracing regression: fine-band broad authority missing')
if 'WRONSKI_DEFAULT_SHADOW_EV = 4.0f' in m or 'WRONSKI_DEFAULT_HIGHLIGHT_EV = 4.0f' in m: raise SystemExit('fixed +/-4EV phone-specific policy regression')
# Critical successful 26616 files must be byte-identical, proving ceiling final/gainmap/UHDR/true2x ownership survived.
for rel in [
'app/src/main/assets/shaders/motionv2/wronski_ltm_final.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']:
    if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit('26616 protected regression '+rel)
# Exact failed-build regressions inherited in infrastructure/shader verifier.
infra=(P/'verify_26617_infrastructure.py').read_text() if (P/'verify_26617_infrastructure.py').exists() else ''
if infra and "'git diff --name-only '" not in infra: raise SystemExit('26616 R1.1 comparator false-positive regression')
print('PASS 26617 permanent regressions: 26616 ceiling/physical/UHDR/true2x protected; playpen fine-edge branch switching blocked; plant broad-highlight adaptive branch enabled; backdoor/chandelier compact-highlight default preserved; boost local contrast false; no fixed +/-4EV')
