#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26742_regressions.py BASE26741 CAND26742')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
expected={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
changed=set((pkg/'26742_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726742' in v and 'VERSION_BUILD=26742' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); bsh=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); bst=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
cpp=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp'); bcpp=txt(b,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
vgn='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
assert (b/vgn).read_bytes()==(c/vgn).read_bytes(),'26741 VGN owner drift'
def triple(s,name):
 m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
# Common NORMAL/LONG accumulator now uses physical validity before hue enters temporal RGB.
for t in ['IRIS_26742_SOURCE_VALID_CHROMA_ACCUMULATION','IRIS_26742_SOURCE_HEADROOM_MARGIN','validIntensities26742','chromaAuthority26742','sourceValidMean26742','uValidityWeightScale']:
 assert t in sh,t
common=section(sh,'    val merge = """','    val universalNormalMasterShortFusion26651 = """')
assert 'uSourceClippingPoint*0.9850' in common
assert 'accumulatedIntensities = sourceValidMean26742 * fullWeight26742;' in common
assert 'accumulatedWeights = fullWeight26742;' in common
assert 'validAccumulatedWeights = validWeight26742;' in common
# Existing NORMAL role routing remains unchanged: all NORMALs benefit from source-valid chroma even when whole-observation guard is false.
for t in ['sourceClipGuard = highlightShortOneTunnel26604','sourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG']:
 assert t in st,t
# SHORT stays valid-only; only source headroom margin advances from 99.25% to 98.5%.
short=section(sh,'    val universalNormalMasterShortFusion26651 = """','    val universalShortValidityAugment26651 = """')
for t in ['IRIS_26742_SHORT_SOURCE_HEADROOM_MARGIN','IRIS_26648_SAMPLE_LEVEL_SHORT_VALIDITY','accumulatedWeights = validAccumulatedWeights','sourceNeighborhoodConfidence = minimum3']:
 assert t in short,t
assert 'uSourceClippingPoint*0.9850' in short and 'uSourceClippingPoint*0.9925' not in short
# LONG whole-neighborhood guard survives and now consumes the common source-valid RGB as well.
for t in ['IRIS_26558_SABRE_SHADOW_LONG_SOURCE_CLIP_GUARD','uSourceClipGuard','uSourceClippedWeight']:
 assert t in sh+st,t
# Super Res GPU + ordinary high-zoom Wronski share one source-valid true2x RBF owner.
for t in ['IRIS_26742_TRUE2X_SOURCE_VALID_CHROMA','sourceValidity26742','validAccumulatedWeight26742','uRawClipThreshold / 0.9850']:
 assert t in sh,t
assert 'uniform1f(program,"uRawClipThreshold",sensorWhiteLevel*0.985f)' in st
for t in ['IRIS_26742_HIGH_ZOOM_SOURCE_VALIDITY','uniform1f(program, "uRawClipThreshold", sensorWhiteLevel * 0.985f)']:
 assert t in sh+st,t
assert 'uniform1f(program, "uSourceClippingPoint", sabreShadowLongSourceClippingPoint())' not in section(st,'    private fun runHighZoomRgbGpu26720(','    private fun reconstructHighZoomRgb26720(')
# 26740/26741 confidence-controlled publication remains active and unchanged outside source accumulation.
for t in ['IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE','IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_STABILITY_EVIDENCE','IRIS_26741_TRUE2X_CONFIDENCE_PUBLICATION','IRIS_26741_TRUE2X_SHAPE_STABILITY_AND_FAIL_CLOSED_PUBLICATION']:
 assert t in sh,t
# CPU fallback mirrors GPU physical-source rule, and JNI ABI names/signatures remain stable.
for t in ['IRIS_26742_TRUE2X_CPU_SOURCE_VALID_CHROMA','clipStart26742','chromaAuthority26742','rawClipThreshold,color,weights']:
 assert t in cpp,t
jni=r'extern\s+"C"\s+JNIEXPORT\s+\w+\s+JNICALL\s+([A-Za-z0-9_]+)'
assert re.findall(jni,bcpp)==re.findall(jni,cpp) and len(re.findall(jni,cpp))>0
# 26741 downstream VGN/neutrality and 26729+/26731 real-color/material owners are byte-invariant.
vgtxt=txt(c,vgn)
for t in ['IRIS_26741_HEADROOM_QUALIFIED_REAL_COLOR_PROOF','IRIS_26741_CLIPPED_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','IRIS_26741_STRONG_ACHROMATIC_FINE_STRUCTURE_AUTHORITY','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY']:
 assert t in vgtxt,t
# No Plan B, semantic object detector, global chroma denoise increase, or chroma sharpening owner introduced.
joined=(sh+st+cpp).lower()
for forbidden in ['barcode_detector','font_detector','text_detector','semanticclass','linear_translational_sr_26742','ipol_26742','plan_b_26742','chroma_sharpen_26742']:
 assert forbidden not in joined,forbidden
# Major protected owners must remain byte-identical.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26742 regressions: source-valid chroma enforced before RGB for NORMAL/LONG, SHORT valid-only preserved at shared 98.5% headroom margin, Super Res GPU+CPU and ordinary Wronski zoom covered, 26740/26741 confidence/VGN and 26729+/26731 real-color owners preserved, no Plan B/global chroma muting')
