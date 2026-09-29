#!/usr/bin/env python3
from pathlib import Path
import sys,re,hashlib
if len(sys.argv)!=3: raise SystemExit('usage: verify_26734_regressions.py BASE26733 CAND26734')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26734_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
expected={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726734' in v and 'VERSION_BUILD=26734' in v
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Lock successful 26727/26728 -> 26733 headroom hierarchy and 26731 transport mechanics.
for t in [
 'IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER',
 'inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY)',
 'highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof)',
 'highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma)',
 'float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma))',
 'IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY',
 'IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP',
 'ivec2(-1,0),3,1,ivec2(1,0),1,3','ivec2(0,-1),0,2,ivec2(0,1),2,0',
 'ivec2(1,-1),4,6,ivec2(-1,1),6,4','ivec2(-1,-1),7,5,ivec2(1,1),5,7']:
 assert t in vgn,t
# Universal achromatic ownership is polarity independent and cannot be vetoed by corrupted center hue.
for t in ['IRIS_26734_POLARITY_INDEPENDENT_ACHROMATIC_PAIR_OWNER',
          'neutralInkPolarity = max(nearBrightA * nearBrightB, nearDarkA * nearDarkB)',
          'IRIS_26734_POLARITY_INDEPENDENT_ACHROMATIC_STRUCTURE_CLEANUP',
          'IRIS_26734_ACHROMATIC_PAIR_RESIDUAL_FLOOR_VETO',
          'IRIS_26734_EARLY_POLARITY_INDEPENDENT_ACHROMATIC_OWNER',
          'neutralOppositePair26734','neutralContaminatedCenterPermission26734']:
 assert t in vgn,t
neutral_block=vgn[vgn.index('IRIS_26734_POLARITY_INDEPENDENT_ACHROMATIC_STRUCTURE_CLEANUP'):vgn.index('/* The physical path may increase',vgn.index('IRIS_26734_POLARITY_INDEPENDENT_ACHROMATIC_STRUCTURE_CLEANUP'))]
assert 'coherentCenterProtection' not in neutral_block
assert 'textRecognition(' not in vgn and 'Tesseract' not in vgn
# Existing real color/material protection survives.
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY',
          'IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO','microObjectProtection','topologyProtection']:
 assert t in vgn,t
# Motion residual chroma policy remains exactly the successful 26733 policy; Night/Custom unchanged.
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE','(0.5f * chromaScale).coerceIn(0f, 2f)',
          '!parameters.irisNightActive && customResidualChroma == null','CUSTOM_EXACT','AUTO_SNR_HALF']:
 assert t in br,t
# All per-lens digital zooms use local output zoom, with clean resource/failure fallback and no >=20 global cliff.
for t in ['IRIS_26734_ALL_DIGITAL_ZOOM_DETAIL_ARCHITECTURE','digitalZoomRequested26734',
          'localOutputZoom > 1.00001f','digitalRoiBudget26734 = 256L * 1024L * 1024L',
          'IRIS_26734_DIGITAL_ZOOM_ACTIVATION','IRIS_26734_DIGITAL_ZOOM_CLEAN_NATIVE_HANDOFF',
          'fallback=NATIVE_SABRE_VGN_NO_DETAIL','directChromaOwner=false','scalar26719Fallback=false']:
 assert t in br,t
activation=br[br.index('IRIS_26734_ALL_DIGITAL_ZOOM_DETAIL_ARCHITECTURE'):br.index('parameters.motionV2HighZoomDetailPath = null')]
assert 'displayedGlobalZoom >= 20f' not in activation
assert '26734 scalar high-zoom fallback is forbidden' in br
# Stacker preserves proven direct-CFA luma/native-chroma route and adds only a fail-closed memory guard.
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26732_HIGH_ZOOM_FAIL_CLOSED_NATIVE_FALLBACK','fallback=NATIVE_SABRE_VGN_NO_DETAIL staleOverlayImpossible=true',
          'IRIS_26734_DIGITAL_ZOOM_RGB32F_RESOURCE_GUARD','DIGITAL_ZOOM_RGB32F_MAX_OUTPUT_BYTES = 256L * 1024L * 1024L',
          'lumaDetailOwner=DIRECT_CFA_TEMPORAL nativeSabreVgnChromaOwner=true directChromaOwner=false']:
 assert t in st,t
# Pipeline/render contract follows local digital zoom and accepts only a complete RGB owner or clean native fallback.
pp=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
contract=pp[pp.index('final boolean highZoomRgbContract26720'):pp.index('if (Math.abs',pp.index('final boolean highZoomRgbContract26720'))]
assert 'motionV2OutputZoom > 1.00001f' in contract and 'motionV2GlobalZoom >= 20.0f' not in contract
rd=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['IRIS_26734_DIGITAL_ZOOM_FAIL_CLOSED_RENDER_CONTRACT','26734 digital-zoom route has a partial/unapplied detail owner']:
 assert t in rd,t
# SR GPU and native CPU mirror are luma-only and cannot increase chroma while lifting luminance.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
cpp=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
for t in ['IRIS_26734_SR_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY = max(guideY * factor, 0.0);',
          'float chromaScale26734 = min(factor, 1.0);','guideRgb - vec3(guideY)']:
 assert t in sh,t
for t in ['IRIS_26734_SR_CPU_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY=std::max(guideY*factor,0.f);',
          'float chromaScale26734=std::min(factor,1.f)','guideRgb[0]-guideY']:
 assert t in cpp,t
# The direct >=20x runtime owner itself is byte-identical; only eligibility changes.
def triple(src,name):
 import re
 m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S); assert m,name
 raw=m.group(1); lines=raw.replace('\r\n','\n').split('\n');
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 nb=[x for x in lines if x.strip()]; ind=min((len(x)-len(x.lstrip()) for x in nb),default=0)
 return '\n'.join(x[ind:] if x.strip() else '' for x in lines)
bsh=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for name in ['highZoomFlowRefine26724','highZoomRgbProtect26724']:
 assert triple(bsh,name)==triple(sh,name),name
# Cross-mode protected owners not intentionally changed.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26734 regressions: 26731 transport + 26727/28/26733 highlight authority frozen; universal polarity-independent achromatic ownership; all-digital local-zoom routing with fail-closed resource guard; direct >=20x runtime bytes unchanged; GPU/CPU SR luma-only detail; Motion 0.5x residual policy and unrelated owners preserved')
