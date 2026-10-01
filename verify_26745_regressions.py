#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re,math
if len(sys.argv)!=3: raise SystemExit('usage: verify_26745_regressions.py BASE26743 CAND26745')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected={
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties'}
changed=set((pkg/'26745_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726745' in v and 'VERSION_BUILD=26745' in v
vgp='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; gp='app/src/main/assets/shaders/motionv2/color_transform.glsl'; cppp='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
vg=txt(c,vgp); gs=txt(c,gp); cpp=txt(c,cppp); bvg=txt(b,vgp); bgs=txt(b,gp); bcpp=txt(b,cppp)
# 26744 reconstruction architecture is not inherited.
for t in ['26744','REFERENCE_RBF','referenceNormalRbf','NORMAL_ONLY_TEMPORAL_RGB_MASTER','LONG_SHADOW_SCALAR_ONLY']:
 assert t not in vg+gs+cpp,t
# Exact 26743 core/immediate-fringe authority is retained byte-for-byte, then only one connected hop is added.
legacy='''float visibleFringeAuthority26743 = neighboringVisibleCore26743 *\n                smoothstep(0.58, 0.72, visibleCenterLuma26743);'''
assert legacy in bvg and legacy in vg
for t in ['IRIS_26743_VISIBLE_HIGHLIGHT_NEUTRALITY_WB_DOMAIN','IRIS_26743_RENDERED_HIGHLIGHT_APPEARANCE_AUTHORITY','IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','IRIS_26745_CONNECTED_BRIGHT_FRINGE_COLOR_AUTHORITY','connectedSecondRingCore26745','visibleHighlightLuma26743(p + 2 * d26745)','connectedBridge26745','0.85 * connectedSecondRingCore26745','physicalRealColorVeto26735','physicalHeadroomColorProof26741','visibleHighlightNeutralAuthority26745']:
 assert t in vg,t
assert vg.index('IRIS_26745_CONNECTED_BRIGHT_FRINGE_COLOR_AUTHORITY')>vg.index('IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY')
# ACR3 itself is unchanged; only a post-ACR3 bright-near-neutral hue authority is appended.
def block(s,start,end):
 i=s.index(start); j=s.index(end,i); return s[i:j]
assert block(bgs,'vec3 iris26638ApplyAcr3','\n\nvoid main')==block(gs,'vec3 iris26638ApplyAcr3','\n\n/* IRIS_26745_POST_VGN_ACR3_HUE_AUTHORITY')
assert bcpp.count('iris26638ApplyAcr3')==cpp.count('iris26638ApplyAcr3')
for t in ['IRIS_26745_POST_VGN_ACR3_HUE_AUTHORITY','iris26745ProtectBrightNeutralHue','brightAuthority=smoothstep(0.58,0.78,targetY)','nearNeutralAuthority=1.0-smoothstep(0.035,0.090,normalizedBase)','rotationAuthority=1.0-smoothstep(0.997,0.9998,directionAgreement)','trustedChroma=trustedDirection*max(renderedMagnitude,baseMagnitude)','linearDisplay=iris26745ProtectBrightNeutralHue']:
 assert t in gs,t
# Native CPU and embedded GPU use the same thresholds and preserve ACR3/luminance ownership.
assert cpp.count('iris26745ProtectBrightNeutralHue')==4
for t in ['smoothstep(0.58f,0.78f,targetY)','smoothstep(0.035f,0.090f,normalizedBase)','smoothstep(0.997f,0.9998f,agreement)','smoothstep(0.58,0.78,targetY)','smoothstep(0.035,0.090,normalizedBase)','smoothstep(0.997,0.9998,agreement)']:
 assert t in cpp,t
# No broad denoise/saturation/sharpening or semantic color detector was introduced.
joined=(vg+gs+cpp).lower()
for forbidden in ['barcode_detector','font_detector','text_detector','semanticclass','plan_b_26745','ipol_26745','global_chroma_denoise_26745','chroma_sharpen_26745','orange_detector','yellow_detector','cyan_detector','foliage_detector']:
 assert forbidden not in joined,forbidden
# Major fusion/reconstruction/tone/UHDR/DNG owners stay byte-identical to successful 26743 authority.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Pure math regression: guard is off for dark, neutral and strong color; bright near-neutral rotation is corrected.
def smooth(a,z,x):
 q=max(0.0,min(1.0,(x-a)/(z-a))); return q*q*(3.0-2.0*q)
def authority(base,out,Y):
 bc=[x-Y for x in base]; oc=[x-Y for x in out]; bm=math.sqrt(sum(x*x for x in bc)); om=math.sqrt(sum(x*x for x in oc)); nb=bm/max(Y,.08)
 present=smooth(.0025,.012,bm)*smooth(.0025,.012,om); agree=sum(x*y for x,y in zip(bc,oc))/max(bm*om,1e-8)
 return smooth(.58,.78,Y)*(1-smooth(.035,.090,nb))*present*(1-smooth(.997,.9998,agree))
assert authority([.35,.36,.34],[.36,.34,.35],.35)==0
assert authority([.8,.8,.8],[.8,.8,.8],.8)==0
assert authority([.9,.7,.7],[.92,.68,.70],.75)==0
assert authority([.82,.80,.78],[.80,.82,.78],.80)>.99
print('PASS 26745 regressions: exact 26743 reconstruction/tone/UHDR owners preserved; connected radius-two bright fringe only; physical real-color veto retained; ACR3 curve unchanged; bright near-neutral hue rotation constrained with Normal/true2x parity; 26744 architecture absent')
