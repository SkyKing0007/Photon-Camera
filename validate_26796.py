#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26796.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
ALLOW={
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties',
}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==len(c)==1779,(len(a),len(c))); need(set(a)==set(c),'candidate universe changed')
mod={p for p in a if a[p]!=c[p]}; need(mod==ALLOW,f'changed allowlist mismatch {sorted(mod)}')
print('PASS 26796 authority-seeded scope: 1779 files, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726796' in v and 'VERSION_BUILD=26796' in v,'version')
print('PASS 26796 version 0.9726796 / 26796')
shader_rel='app/src/main/assets/shaders/motionv2/render.glsl'
java_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
b=(BASE/shader_rel).read_text(); n=(CAND/shader_rel).read_text(); j=(CAND/java_rel).read_text(); bj=(BASE/java_rel).read_text()
need(n.count('IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY')==1,'26796 shader owner marker')
for s in (
'projectedGuide=iris26653MapMotionSdrFinalGuide(guide)',
'vec2 grad=vec2(dFdx(y),dFdy(y))',
'float relativeGradient=(gradMag*max(irisOutputZoom,1.0))/max(guide,0.03)',
'sourcePixel+normal*3.0','sourcePixel+normal*5.0','sourcePixel-normal*3.0','sourcePixel-normal*5.0',
'bipolarEvidence=smoothstep(0.14,0.52,opponentRatio)',
'materialSupport=smoothstep(0.24,0.68,materialRatio)',
'float correction=clamp(brightRisk*edgeRisk*chromaRisk*bipolarEvidence*unsupported,0.0,1.0)',
'vec3 corrected=vec3(y)+(rgb-vec3(y))*scale'):
    need(s in n,f'missing 26796 contract: {s}')
block=n[n.index('vec3 iris26796SampleCalibratedP3'):n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE')]
need('vec2 tangent' not in block and 'sourcePixel+tangent' not in block and 'sourcePixel-tangent' not in block,'tangent sampling grants permission')
callpos=n.index('linearSrgb=iris26796CalibratedBrightContour(sourcePixel,linearSrgb)')
need(callpos < n.index('linearSrgb=max(linearSrgb*exp2(iris26718HighZoomLogDetail'),'26796 correction must precede high-zoom scalar detail')
need(callpos < n.index('if(iris26592MotionHdrHandoff!=0 && iris26621LocalToneEnabled!=0)'),'26796 correction must precede presentation/tone')
fn=n[n.index('vec3 iris26796CalibratedBrightContour'):n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE')]
need(fn.index('vec2 grad=vec2(dFdx(y),dFdy(y))') < fn.index('if(brightRisk<=1.0e-5)return rgb'),'derivative evaluated inside divergent flow')
need('IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_OWNER' in j,'26796 runtime owner log missing')
need('domain=LINEAR_DISPLAY_P3_AFTER_COLOR_TRANSFORM_ACR3' in j and 'insertion=RENDER_INPUT_BEFORE_PRESENTATION_TONE' in j,'26796 runtime domain log missing')
# Strip only 26796 shader insertion + call and require exact 26795 shader otherwise.
start=n.index('/* IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY')
end=n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE',start)
stripped=n[:start]+n[end:]
call=(
'    if(iris26592MotionHdrHandoff!=0){\n'
'        /* 26796 definitive calibrated-domain validity runs before any presentation/tone magnitude. */\n'
'        linearSrgb=iris26796CalibratedBrightContour(sourcePixel,linearSrgb);\n'
'    }\n')
need(call in stripped,'26796 render call block missing')
need(stripped.replace(call,'',1)==b,'render shader changed outside intended 26796 owner + call')
log=(
'        if (basePipeline.mParameters.motionV2Active) {\n'
'            Log.i(Name, "IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_OWNER"\n'
'                    + " domain=LINEAR_DISPLAY_P3_AFTER_COLOR_TRANSFORM_ACR3"\n'
'                    + " insertion=RENDER_INPUT_BEFORE_PRESENTATION_TONE"\n'
'                    + " support=MATERIAL_INTERIOR_EDGE_NORMAL_DEPTH_3_5"\n'
'                    + " tangentPermission=false bipolarOpponentRequired=true"\n'
'                    + " lumaInvariant=true strongMaterialProtected=true"\n'
'                    + " downstreamDefaultChromaResurrectionOwner=false");\n'
'        }\n')
need(log in j,'26796 java log block missing')
need(j.replace(log,'',1)==bj,'MotionV2Render.java changed outside intended 26796 owner log')
print('PASS 26796 ownership: render GLSL correction + single runtime owner log only; all prior render/tone bytes protected')
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
]: need(sha(BASE/p)==sha(CAND/p),f'protected owner changed: {p}')
print('PASS 26796 26795 bridge + color transform/ACR3 + Sabre/VGN owners byte-identical')
for p in a:
    if p in ALLOW: continue
    need(a[p]==c[p],f'unexpected protected change {p}')
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def scale(projected,relgrad,center,opponent,material):
    bright=ss(.70,.88,projected); edge=ss(.045,.18,relgrad)
    chroma=ss(.012,.045,center)*(1.0-ss(.30,.48,center))
    bipolar=ss(.14,.52,opponent/max(center,1e-6))
    support=ss(.24,.68,material/max(center,1e-6)); corr=bright*edge*chroma*bipolar*(1.0-support)
    supported=max(material,center*.08); target=center+(min(center,supported)-center)*corr
    return corr,target/max(center,1e-6)
cx,s=scale(.96,.30,.22,.16,.01); need(cx>.80 and s<.30,(cx,s))
cx,s=scale(.96,.30,.22,.16,.20); need(cx<.02 and s>.98,(cx,s))
cx,s=scale(.96,.30,.22,0.0,0.0); need(cx==0.0 and s==1.0,(cx,s))
cx,s=scale(.96,.30,.55,.30,0.0); need(cx==0.0 and s==1.0,(cx,s))
cx,s=scale(.55,.30,.22,.16,0.0); need(cx==0.0 and s==1.0,(cx,s))
w=(.22897456,.69173852,.07928691); rgb=(.91,.69,.84); y=sum(a*b for a,b in zip(w,rgb)); chroma=tuple(v-y for v in rgb)
for k in (.08,.27,.73,1.0):
    out=tuple(y+k*q for q in chroma); yy=sum(a*b for a,b in zip(w,out)); need(abs(yy-y)<2e-7,(k,y,yy))
print('PASS 26796 synthetic invariants: bipolar unsupported fringe corrected; real material/high-frequency/pastel/midtone color protected; Display-P3 luma invariant')
print('PASS 26796 no Sabre/VGN/denoise/26795-bridge/color-transform/ACR3/exposure/tone/UHDR/DNG/SR/native/vendor redesign')
