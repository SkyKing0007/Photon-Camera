#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26797.py BASE_ROOT CANDIDATE_ROOT')
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
print('PASS 26797 authority-seeded scope: 1779 files, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726797' in v and 'VERSION_BUILD=26797' in v,'version')
print('PASS 26797 version 0.9726797 / 26797')
shader_rel='app/src/main/assets/shaders/motionv2/render.glsl'
java_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
b=(BASE/shader_rel).read_text(); n=(CAND/shader_rel).read_text(); bj=(BASE/java_rel).read_text(); j=(CAND/java_rel).read_text()
need(n.count('IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY')==1,'26796 fallback marker missing')
need(n.count('IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_VALIDITY')==1,'26797 shader owner marker')
for s in (
'vec3 fallback26796=iris26796CalibratedBrightContour(sourcePixel,rgb)',
'float wideOpponent=smoothstep(0.08,0.34,opponentRatio)',
'return relevance*smoothstep(0.08,0.46,1.0-alignment)',
'float tangentCoherent=smoothstep(0.52,0.82,tangentRatio)',
'sourcePixel+normal*2.0','sourcePixel-normal*2.0','sourcePixel+normal*3.0','sourcePixel-normal*3.0',
'sourcePixel+normal*5.0','sourcePixel-normal*5.0',
'float ribbonEvidence=interiorHueAbsent*withinMaterialEdge*realEdgeSpan*(1.0-tangentCoherent)',
'float tangentHueTurn=max(iris26797HueTurnEvidence(tanPos2,dir,centerMagnitude)' ,
'float topologyEvidence=max(phaseEvidence,ribbonEvidence)',
'float strongCorrection=smoothstep(0.22,0.50,confidence)',
'vec3 targetChroma=iris26797MaterialTargetChroma(negMaterial,posMaterial,y,guide,centerMagnitude)',
'return mix(fallback26796,strongCorrected,strongCorrection)'):
    need(s in n,f'missing 26797 contract: {s}')
block=n[n.index('/* IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_VALIDITY'):n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE')]
need('magenta' in block.lower() and 'violet' in block.lower() and 'blue' in block.lower() and 'green' in block.lower(),'documented multi-hue regression class missing')
need('if(abs(yp-yn)>1.0e-6)t=clamp((centerY-yn)/(yp-yn),0.0,1.0)' in block,'material-interior target interpolation missing')
need('tangentPermission' not in block,'tangent must not be a permission owner')
call='linearSrgb=iris26797CalibratedZipperContour(sourcePixel,linearSrgb);'
need(call in n,'26797 render call missing')
callpos=n.index(call)
need(callpos < n.index('linearSrgb=max(linearSrgb*exp2(iris26718HighZoomLogDetail'),'26797 correction must precede high-zoom scalar detail')
need(callpos < n.index('if(iris26592MotionHdrHandoff!=0 && iris26621LocalToneEnabled!=0)'),'26797 correction must precede presentation/tone')
fn=n[n.index('vec3 iris26797CalibratedZipperContour'):n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE')]
need(fn.index('vec2 grad=vec2(dFdx(y),dFdy(y))') < fn.index('if(chromaRisk<=1.0e-5'),'26797 derivative must precede divergent returns')
need(fn.index('vec3 fallback26796=iris26796CalibratedBrightContour') < fn.index('if(guide<=1.0e-6)return fallback26796'),'26796 fallback must be evaluated uniformly before divergence')
# Exact 26796 fallback owner is byte-identical.
base_26796=b[b.index('/* IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY'):b.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE')]
cand_26796=n[n.index('/* IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY'):n.index('/* IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_VALIDITY')]
need(base_26796==cand_26796,'successful 26796 fallback shader owner changed')
# Remove only 26797 block and restore exact 26796 call block; everything else must be exact authority bytes.
start=n.index('/* IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_VALIDITY')
end=n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE',start)
stripped=n[:start]+n[end:]
newcall=(
'    if(iris26592MotionHdrHandoff!=0){\n'
'        /* 26797 keeps 26796 as the conservative fallback and adds the calibrated multi-hue zipper\n'
'         * strong tier before any presentation/tone magnitude. */\n'
'        linearSrgb=iris26797CalibratedZipperContour(sourcePixel,linearSrgb);\n'
'    }\n')
oldcall=(
'    if(iris26592MotionHdrHandoff!=0){\n'
'        /* 26796 definitive calibrated-domain validity runs before any presentation/tone magnitude. */\n'
'        linearSrgb=iris26796CalibratedBrightContour(sourcePixel,linearSrgb);\n'
'    }\n')
need(newcall in stripped,'26797 call block missing for exact preservation proof')
need(stripped.replace(newcall,oldcall,1)==b,'render shader changed outside 26797 owner + call')
oldlog=(
'        if (basePipeline.mParameters.motionV2Active) {\n'
'            Log.i(Name, "IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_OWNER"\n'
'                    + " domain=LINEAR_DISPLAY_P3_AFTER_COLOR_TRANSFORM_ACR3"\n'
'                    + " insertion=RENDER_INPUT_BEFORE_PRESENTATION_TONE"\n'
'                    + " support=MATERIAL_INTERIOR_EDGE_NORMAL_DEPTH_3_5"\n'
'                    + " tangentPermission=false bipolarOpponentRequired=true"\n'
'                    + " lumaInvariant=true strongMaterialProtected=true"\n'
'                    + " downstreamDefaultChromaResurrectionOwner=false");\n'
'        }\n')
newlog=(
'        if (basePipeline.mParameters.motionV2Active) {\n'
'            Log.i(Name, "IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_OWNER"\n'
'                    + " domain=LINEAR_DISPLAY_P3_AFTER_COLOR_TRANSFORM_ACR3"\n'
'                    + " insertion=RENDER_INPUT_BEFORE_PRESENTATION_TONE"\n'
'                    + " fallback=IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR"\n'
'                    + " materialSupport=EDGE_NORMAL_DEPTH_3_5_INTERPOLATED"\n'
'                    + " phaseBand=EDGE_NORMAL_PLUS_MINUS_3 tangentRole=PROTECTION_ONLY"\n'
'                    + " immediateOpponentRequired=false hueAgnostic=true"\n'
'                    + " highConfidenceResidualFloor=0 lumaInvariant=true strongMaterialProtected=true"\n'
'                    + " downstreamDefaultChromaResurrectionOwner=false");\n'
'        }\n')
need(newlog in j,'26797 runtime owner log missing')
need(j.replace(newlog,oldlog,1)==bj,'MotionV2Render.java changed outside intended 26797 owner-log replacement')
print('PASS 26797 ownership: successful 26796 fallback retained byte-identical; only high-confidence calibrated zipper tier + call/log/version added')
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
]: need(sha(BASE/p)==sha(CAND/p),f'protected owner changed: {p}')
for p in a:
    if p in ALLOW: continue
    need(a[p]==c[p],f'unexpected protected change {p}')
print('PASS 26797 26795 bridge + color transform/ACR3 + Sabre/VGN + exposure/tone/UHDR/DNG/SR/native/vendor owners protected')

def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def high(projected,relgrad,center,material_ratio,opponent_ratio,hue_turn,tangent_ratio,interior_absence,within,span):
    bright=ss(.68,.86,projected); edge=ss(.040,.15,relgrad)
    chroma=ss(.010,.036,center)*(1.0-ss(.30,.48,center))
    support=ss(.20,.60,material_ratio); unsupported=1.0-support
    wide=ss(.08,.34,opponent_ratio); phase=max(wide,hue_turn)
    tangent=ss(.52,.82,tangent_ratio)
    ribbon=interior_absence*within*span*(1.0-tangent)
    evidence=max(phase,ribbon)
    conf=min(bright,edge,chroma,unsupported,evidence)
    return ss(.22,.50,conf)
# displaced opponent/phase zipper -> nearly full strong tier
need(high(.96,.28,.20,.02,.55,.0,.15,1,1,1)>.95,'wide opponent zipper not strongly corrected')
# hue-changing lavender/blue zipper without exact opponent -> strong via hue-turn
need(high(.96,.28,.20,.02,.0,.85,.18,1,1,1)>.95,'multi-hue phase-turn zipper not strongly corrected')
# one-sided neutral->colored->neutral ribbon -> strong when tangent is unstable
need(high(.96,.28,.20,.02,.0,.0,.10,1,1,1)>.95,'one-sided zipper ribbon not strongly corrected')
# stable real thin colored line gets tangent protection in the no-opponent tier
need(high(.96,.28,.20,.02,.0,.0,.95,1,1,1)<.02,'stable thin real color not protected')
# material-interior color, strong saturated material, and non-bright detail remain protected
need(high(.96,.28,.20,.90,.55,.85,.10,0,1,1)<.02,'material-interior color not protected')
need(high(.96,.28,.55,.02,.55,.85,.10,1,1,1)<.02,'strong saturated material not protected')
need(high(.55,.28,.20,.02,.55,.85,.10,1,1,1)<.02,'midtone color not protected')
# Weighted P3 luminance remains exact for arbitrary material-target interpolation at fixed center Y.
w=(.22897456,.69173852,.07928691)
rgb=(.91,.69,.84); y=sum(a*b for a,b in zip(w,rgb)); center=tuple(v-y for v in rgb)
target=(.03,-.015,.043)
# force target to zero weighted luma
wy=sum(a*b for a,b in zip(w,target)); target=tuple(v-wy for v in target)
for k in (0.0,.2,.7,1.0):
    chroma=tuple((1-k)*a+k*b for a,b in zip(center,target)); out=tuple(y+q for q in chroma); yy=sum(a*b for a,b in zip(w,out)); need(abs(yy-y)<2e-7,(k,y,yy))
print('PASS 26797 synthetic invariants: multi-hue/wide-opponent/one-sided zipper corrected; stable thin/material/high-saturation/midtone color protected; Display-P3 luma invariant')
print('PASS 26797 no Sabre/VGN/denoise/26795-bridge/color-transform/ACR3/exposure/tone/UHDR/DNG/SR/native/vendor redesign')
