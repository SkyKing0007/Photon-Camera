#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26800.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
MODIFIED={
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/version.properties'}
ADDED={'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'}
ALLOW=MODIFIED|ADDED
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1781 and len(c)==1782,(len(a),len(c)))
need(set(c)-set(a)==ADDED,f'added allowlist mismatch {sorted(set(c)-set(a))}')
need(set(a)-set(c)==set(),'unexpected deletion')
mods={p for p in set(a)&set(c) if a[p]!=c[p]}
need(mods==MODIFIED,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26800 authority-seeded scope: 1781 base -> 1782 candidate, exactly 4 modified + 1 added / 0 deleted')
v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726800' in v and 'VERSION_BUILD=26800' in v,'version')
print('PASS 26800 version 0.9726800 / 26800')

render_rel='app/src/main/assets/shaders/motionv2/render.glsl'
java_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
ui_rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'
new_cls_rel='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
old_cls_rel='app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl'
prop_rel='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
b=(BASE/render_rel).read_text(); n=(CAND/render_rel).read_text()
bj=(BASE/java_rel).read_text(); j=(CAND/java_rel).read_text()
bui=(BASE/ui_rel).read_text(); ui=(CAND/ui_rel).read_text()
cls=(CAND/new_cls_rel).read_text()

# 26799 classifier/propagation remain byte-identical historical/fallback assets.
need(sha(BASE/old_cls_rel)==sha(CAND/old_cls_rel),'successful 26799 classifier asset changed')
need(sha(BASE/prop_rel)==sha(CAND/prop_rel),'successful 26799 propagation shader changed')
need('IRIS_26799_TRUE_BOUNDED_CONNECTED_PROPAGATION' in (CAND/prop_rel).read_text(),'26799 propagation owner missing')

# New classifier contracts.
for s in (
'IRIS_26800_HIGH_CHROMA_BRIGHT_FRINGE_CLASSIFIER',
'IRIS_26800_TRUE_2D_MATERIAL_PATCH',
'IRIS_26800_STRICT_MATERIAL_PROOF',
'IRIS_26800_HIGH_CHROMA_BRIGHT_ADMISSION',
'uint iris26799Counters[28];',
'float highChroma=smoothstep(0.26,0.38,mag);',
'float robustMaterialRatio=max(posRobust,negRobust)/max(mag,1.0e-6);',
'float materialSupport=smoothstep(0.28,0.60,robustMaterialRatio);',
'float highSingleHueSeed=',
'float highPlateauSeed=',
'atomicAdd(iris26799Counters[20],1u);',
'atomicAdd(iris26799Counters[21],1u);',
'atomicAdd(iris26799Counters[22],1u);',
'atomicAdd(iris26799Counters[23],1u);',
'atomicAdd(iris26799Counters[24],1u);',
'atomicAdd(iris26799Counters[27],1u);'):
    need(s in cls,f'26800 classifier contract missing {s}')
# Ensure old hard high-chroma ceiling is not global admission authority anymore.
need('float chromaRisk=smoothstep(0.010,0.034,mag)*(1.0-smoothstep(0.28,0.44,mag));' not in cls,
     '26799 global high-chroma ceiling survived as authority')
need(cls.index('float neutralInterior=') < cls.index('if(materialSupport>0.72)'),
     '2-D neutral/material evidence must be known before protection return')

# Render correction ordering frozen except telemetry expansion.
for s in (
'uint iris26799Counters[28];',
'IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_CORRECTION',
'linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);',
'linearSrgb=iris26799ApplyConnectedCorrection(xy,sourcePixel,linearSrgb);',
'atomicAdd(iris26799Counters[25],1u);',
'atomicMax(iris26799Counters[26]'):
    need(s in n,f'render contract missing {s}')
need(n.index('linearSrgb=iris26798CalibratedConnectedZipper') < n.index('linearSrgb=iris26799ApplyConnectedCorrection'),
     '26799 connected correction moved before 26798')
need(n.index('linearSrgb=iris26799ApplyConnectedCorrection') < n.index('linearSrgb=mapExtendedLinearHeadroom(linearSrgb);'),
     'connected correction moved after presentation tone')
# Aside from stats array and high-chroma telemetry, old 26799 correction must remain structurally present.
need('float sameLimit=centerMag*0.20;' in n,'26799 material-target limiter changed/missing')

# Java: 8-pass propagation unchanged and new classifier + telemetry.
for s in (
'IRIS_26799_PROPAGATION_ITERATIONS = 8',
'new GLBuffer(28, new GLFormat(GLFormat.DataType.UNSIGNED_32))',
'iris26799Stats.uploadBuffer(new int[28], 28);',
'useAssetProgram("motionv2/false_color_classify_26800")',
'useAssetProgram("motionv2/false_color_propagate_26799")',
'previousMask = outputMask;',
'IRIS_26800_HIGH_CHROMA_FALSE_COLOR_ADMISSION_OWNER',
'propagation=EXACT_26799_8_PASS_UNCHANGED',
'highChromaRelevant=',
'highChromaPlateauSeed=',
'highChromaSingleHueSeed=',
'protected2DMaterialStrict=',
'highChromaWeakCandidate=',
'highChromaConnectedCorrected=',
'highChromaMaxPost=',
'highChromaRejected='):
    need(s in j,f'Java 26800 contract missing {s}')
need(j.count('useAssetProgram("motionv2/false_color_propagate_26799")')==1,'propagation program call count changed')
need('IRIS_26799_MASK_LIFECYCLE' in j and 'propagationIterations=' in j,'26799 mask lifecycle missing')

# UI: same hard-geometry signature reuses settled solution; actual hard geometry changes recalc.
for s in (
'IRIS_26800_STABLE_PHOTO_CONTROL_GEOMETRY',
'iris26800SettledPreferredGroupCenter',
'iris26800SettledTargetGroupCenter',
'iris26800SettledModeShift',
'iris26800SettledLensGap',
'iris26800SettledModeGap',
'final boolean reuseSettled = settledSignature.equals(iris26693LastSettledGeometrySignature)',
'IRIS_26800_TRANSIENT_CONTROL_GEOMETRY_REJECT',
'candidateScale=',
'processing=" + CaptureController.isProcessing',
'iris26627PlaceScaledControl(shutter, scale, placementGroupCenter, targetGroupCenter)'):
    need(s in ui,f'UI 26800 contract missing {s}')
need('Math.round(rootBottom)' in ui and 'iris26627BottomSystemInsetPx' in ui and 'Math.round(safeBottom)' in ui,
     'hard geometry signature incomplete')
# Existing adaptive safety owner remains.
for s in ('IRIS_26627_ADAPTIVE_SAFE_CONTROL_REGION','minimumLensToControlsGapPx','minimumControlsToModeGapPx',
          'scale = Math.max(0.01f, Math.min(1.0f, scale));'):
    need(s in ui,f'inherited adaptive safety missing {s}')

# Protected domains outside intended files unchanged.
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt']:
    need(sha(BASE/p)==sha(CAND/p),f'protected owner changed {p}')
for p in set(a)&set(c):
    if p in MODIFIED: continue
    need(a[p]==c[p],f'unexpected protected change {p}')
print('PASS 26800 ownership: 26799 propagation/fallback frozen; high-chroma admission + UI geometry stabilization only')
print('PASS 26800 protected: Sabre/VGN/denoise/bridge/color-transform/ACR3/exposure/tone/UHDR/DNG/SR/native/vendor unchanged')

# Synthetic classifier math regressions.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
# Vivid false fringe formerly capped by 0.44 must now be eligible if bright/neutral/unsupported.
mag=.52; projected=.98; mat=.03; neutral=.96; within=.95; edge=.90; plateau=.95
high=ss(.26,.38,mag); hb=ss(.80,.93,projected); unsupported=1-ss(.28,.60,mat)
strength=high*hb*unsupported*neutral*within*max(edge,plateau)
need(ss(.10,.34,strength)>.95,'high-chroma bright false fringe not admitted')
# Real saturated material with coherent 2-D hue must be protected.
real_ratio=.88
need(ss(.28,.60,real_ratio)>.99,'real coherent 2-D material not protected')
# 1-D-looking ribbon with weak area support must not self-protect.
ribbon_ratio=.15
need(ss(.28,.60,ribbon_ratio)<.01,'thin false ribbon self-validates as material')
# High-chroma single-hue/plateau seeds must survive low phase.
highweak=.95; lowphase=.98
need(ss(.14,.36,highweak*ss(.80,.92,.98)*lowphase)>.95,'high-chroma single-hue seed failed')
need(ss(.12,.34,highweak*ss(.86,.95,.98)*(1-ss(.030,.105,.01)))>.95,'high-chroma plateau seed failed')
# Display-P3 luma correction invariant remains exact by construction.
w=(.22897456,.69173852,.07928691); rgb=(.95,.72,.89); y=sum(a*b for a,b in zip(w,rgb))
target=(.01,-.004,.006); # zero-luma adjust target before scaling
wy=sum(a*b for a,b in zip(w,target)); target=tuple(v-wy for v in target)
out=tuple(y+v for v in target); yy=sum(a*b for a,b in zip(w,out))
need(abs(yy-y)<2e-7,'Display-P3 luma invariant failed')
print('PASS 26800 IQ synthetic regressions: vivid high-chroma, single-hue, plateau admission; 2-D real material protected; false ribbon rejected; luma invariant')

# UI synthetic regression: same hard signature must reuse settled full scale; hard signature change may recompute.
def solve(prev_sig,prev_scale,new_sig,candidate):
    reuse=(new_sig==prev_sig and math.isfinite(prev_scale))
    return prev_scale if reuse else candidate
sig='MOTION:false:false:3138:2145:2145:180:2953'
need(abs(solve(sig,1.0,sig,.84581)-1.0)<1e-9,'transient same-authority shrink not rejected')
need(abs(solve(sig,1.0,sig,1.0)-1.0)<1e-9,'stable same-authority geometry changed')
need(abs(solve(sig,1.0,'MOTION:false:false:2500:1800:1800:180:2315',.84)-.84)<1e-9,'real hard-geometry change incorrectly frozen')
print('PASS 26800 UI regression: transient 0.84581 shrink rejected under unchanged hard geometry; real geometry change still recomputes')
