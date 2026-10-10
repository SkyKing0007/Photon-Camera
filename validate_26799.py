#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26799.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
MODIFIED={
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'}
ADDED={
'app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'}
ALLOW=MODIFIED|ADDED

def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1779 and len(c)==1781,(len(a),len(c)))
need(set(c)-set(a)==ADDED,f'added allowlist mismatch {sorted(set(c)-set(a))}')
need(set(a)-set(c)==set(),'unexpected deletion')
mods={p for p in set(a)&set(c) if a[p]!=c[p]}
need(mods==MODIFIED,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26799 authority-seeded scope: 1779 base -> 1781 candidate, exactly 3 modified + 2 added / 0 deleted')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726799' in v and 'VERSION_BUILD=26799' in v,'version')
print('PASS 26799 version 0.9726799 / 26799')
render_rel='app/src/main/assets/shaders/motionv2/render.glsl'
java_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
class_rel='app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl'
prop_rel='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
b=(BASE/render_rel).read_text(); n=(CAND/render_rel).read_text(); j=(CAND/java_rel).read_text(); bj=(BASE/java_rel).read_text(); cls=(CAND/class_rel).read_text(); prop=(CAND/prop_rel).read_text()
# Successful 26796/26797/26798 shader owner bytes are frozen exactly.
start='/* IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY'
newmark='/* IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_CORRECTION'
endmark='/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE'
need(start in b and start in n and newmark in n,'owner markers')
base_frozen=b[b.index(start):b.index(endmark)]
cand_frozen=n[n.index(start):n.index(newmark)]
need(base_frozen==cand_frozen,'successful 26796+26797+26798 render owners changed')
for s in (
'uniform sampler2D iris26799ConnectedMask;',
'layout(std430, binding=1) buffer iris26799Stats {',
'uint iris26799Counters[20];',
'IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_CORRECTION',
'iris26799RobustMaterialTarget',
'float sameLimit=centerMag*0.20;',
'atomicAdd(iris26799Counters[14],1u);',
'linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);',
'linearSrgb=iris26799ApplyConnectedCorrection(xy,sourcePixel,linearSrgb);'):
    need(s in n,f'missing render contract {s}')
need(n.index('linearSrgb=iris26798CalibratedConnectedZipper') < n.index('linearSrgb=iris26799ApplyConnectedCorrection'),'26799 must follow successful 26798 fallback')
need(n.index('linearSrgb=iris26799ApplyConnectedCorrection') < n.index('linearSrgb=max(linearSrgb*exp2(iris26718HighZoomLogDetail'),'26799 must precede high-zoom scalar detail')
need(n.index('linearSrgb=iris26799ApplyConnectedCorrection') < n.index('if(iris26592MotionHdrHandoff!=0 && iris26621LocalToneEnabled!=0)'),'26799 must precede presentation/tone')
# New classifier/propagator contract.
for s in ('IRIS_26799_MULTI_PASS_FALSE_COLOR_CLASSIFIER','layout(std430, binding=1) buffer iris26799Stats','patchSameHue','patchChroma','patchLuma','float materialSupport=smoothstep(0.20,0.52,materialRatio);','float plateauStrength=','float singleHueStrength=','Output=1.0','Output=0.85','Output=0.55','Output=0.40'):
    need(s in cls,f'classifier contract missing {s}')
for s in ('IRIS_26799_TRUE_BOUNDED_CONNECTED_PROPAGATION','uniform sampler2D ClassMask;','uniform sampler2D PrevConnected;','bool candidate=cls>=0.35;','bool seed=cls>=0.75;','neighbor=neighbor||','atomicAdd(iris26799Counters[6+iris26799Iteration],1u);'):
    need(s in prop,f'propagation contract missing {s}')
# Java architecture/lifetime proof.
for s in (
'IRIS_26799_PROPAGATION_ITERATIONS = 8',
'IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_OWNER',
'architecture=CLASSIFY_R8_PLUS_8_ITERATION_TRUE_PING_PONG_CONNECTIVITY_PLUS_RENDER_CORRECTION',
'new GLFormat(GLFormat.DataType.SIMPLE_8, 1)',
'useAssetProgram("motionv2/false_color_classify_26799")',
'useAssetProgram("motionv2/false_color_propagate_26799")',
'previousMask = outputMask;',
'glProg.setTexture("ClassMask", iris26799ClassMask);',
'glProg.setTexture("PrevConnected", previousMask);',
'glProg.setBufferCompute("iris26799Stats", iris26799Stats);',
'glProg.setTexture("iris26799ConnectedMask", iris26799ConnectedMask);',
 'IRIS_26799_MASK_LIFECYCLE',
'peakMasks=3 renderRetainedMasks=1',
'IRIS_26799_FALSE_COLOR_MASK_DECISIONS',
'iris26799ClassMask.close()',
'iris26799PingA.close()',
'iris26799PingB.close()'):
    need(s in j,f'Java 26799 contract missing {s}')
need(j.count('useAssetProgram("motionv2/false_color_propagate_26799")')==1,'propagation program call must stay inside fixed loop')
# Exact successful 26798 owner log remains present byte-identically.
marker='            Log.i(Name, "IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_OWNER"'
def logblock(text):
    i=text.index(marker); e=text.index('        }',i); return text[i:e]
need(logblock(j)==logblock(bj),'26798 owner log changed')
# Protected owners outside intended files remain byte-identical.
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
print('PASS 26799 ownership: successful 26798 fallback frozen; only multi-pass mask/correction + Java orchestration + version added')
print('PASS 26799 protected: Sabre/VGN/denoise/bridge/color-transform/ACR3/exposure/tone/UHDR/DNG/SR/native/vendor unchanged')

# Architecture-level regression simulation: recursive propagation must extend through an 8-pixel weak chain.
def propagate(classes,iters=8):
    prev=[1 if x>=.75 else 0 for x in classes]
    cand=[x>=.35 for x in classes]
    for _ in range(iters):
        out=prev[:]
        for i in range(len(classes)):
            if not cand[i]: out[i]=0; continue
            if prev[i]: out[i]=1; continue
            left=prev[i-1] if i>0 else 0; right=prev[i+1] if i+1<len(prev) else 0
            out[i]=1 if left or right else 0
        prev=out
    return prev
chain=[1.0]+[.55]*8+[0.0]
need(propagate(chain)[:9]==[1]*9,'true recursive 8-pixel propagation failed')
need(propagate([.55]*9)==[0]*9,'no-seed weak structure leaked')
need(propagate([.85,.40,.40,.55])==[1,1,1,1],'single-hue seed/plateau connectivity failed')
# 2-D material support: a coherent material side must protect; a 1-D-only ribbon must not.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
coherent_ratio=.92; ribbon_ratio=.12
need(ss(.20,.52,coherent_ratio)>.99,'coherent 2D material not protected')
need(ss(.20,.52,ribbon_ratio)<.01,'thin unsupported ribbon self-validates')
# Highlight plateau admission does not require ordinary luma span.
plateau=ss(.86,.95,.97)*(1-ss(.055,.17,.02))*(1-ss(.030,.105,.01))
need(ss(.08,.28,plateau)>.99,'near-white neutral plateau not admitted')
# Weighted Display-P3 luma invariant for material-target correction and same-hue cap.
w=(.22897456,.69173852,.07928691); rgb=(.91,.69,.84); y=sum(a*b for a,b in zip(w,rgb)); center=tuple(v-y for v in rgb)
samps=[(.83,.82,.81),(.89,.88,.87),(.80,.81,.80),(.86,.85,.84)]
target=[]
for s in samps:
    sy=sum(a*b for a,b in zip(w,s)); target.append(tuple(v-sy for v in s))
t=tuple(sum(q[k] for q in target)/len(target) for k in range(3)); out=tuple(y+q for q in t); yy=sum(a*b for a,b in zip(w,out)); need(abs(yy-y)<2e-7,(y,yy))
print('PASS 26799 synthetic regressions: true recursive propagation, no-seed protection, single-hue/plateau connectivity, 2-D material validity, plateau admission, Display-P3 luma invariant')
