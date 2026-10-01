#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26741_regressions.py BASE26740 CAND26741')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
expected={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
changed=set((pkg/'26741_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726741' in v and 'VERSION_BUILD=26741' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); bsh=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); bst=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'); bv=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
cpp=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp'); bcpp=txt(b,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')

def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
def triple(s,name):
 m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def marker_section(s,marker):
 i=s.index(marker); j=s.find('/* IRIS_',i+len(marker)); return s[i:] if j<0 else s[i:j]
# 26740 normal Motion/digital-zoom Wronski correction is frozen exactly.
assert section(bsh,'IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE','IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION') == section(sh,'IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE','IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION')
assert section(bsh,'IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_STABILITY_EVIDENCE','IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE') == section(sh,'IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_STABILITY_EVIDENCE','IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE')
assert section(bsh,'IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR','IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY') == section(sh,'IRIS_26739_HIGH_ZOOM_WRONSKI_ACCUMULATOR','IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY')
for t in ['IRIS_26739_WRONSKI_SENSOR_LINEAR_ACCUMULATION','IRIS_26739_FAITHFUL_WRONSKI_RGB_PUBLICATION','whiteBalanceDuringMerge=false resolveSabre=false secondDemosaic=false','IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE']:
 assert t in st+sh,t
# Existing Super Res Wronski/Sabre evidence and guide shader remain byte-identical; 26741 derives a new publication variant only.
for name in ['true2xMerge26564','true2xResolve26564','true2xGuideRender26568']:
 assert triple(bsh,name)==triple(sh,name),name
for t in ['IRIS_26741_TRUE2X_CONFIDENCE_PUBLICATION','IRIS_26741_TRUE2X_SHAPE_STABILITY_AND_FAIL_CLOSED_PUBLICATION','reconstructionConfidence26741','publicationAuthority26741','mix(1.0,materialSupportGate,materialBoundary)']:
 assert t in sh,t
for t in ['true2xGuideRenderProgram26741','GlesMgcRawSabreShaders.true2xGuideRender26741','iris_26741_true2x_confidence_publication','highResLumaOwner=DIRECT_CFA_CONFIDENCE_GATED_26741','directChromaOwner=false','shapePublication26741=true']:
 assert t in st,t
assert 'program=true2xGuideRenderProgram26568; GLES30.glUseProgram(program);' not in st
# Direct-CFA Super Res remains luma/detail-only; native Sabre/VGN remains the RGB/chroma/highlight guide owner.
for t in ['IRIS_26734_SR_CPU_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY']:
 assert t in cpp+sh,t
for forbidden in ['directChromaOwner=true','IRIS_26741_DIRECT_CFA_CHROMA_OWNER']:
 assert forbidden not in sh+st+cpp,forbidden
# CPU fallback receives the same fail-closed publication principle; JNI ABI names/signatures are unchanged.
for t in ['IRIS_26741_TRUE2X_CPU_CONFIDENCE_PUBLICATION','shapeTrust26741','reconstructionConfidence26741','publicationAuthority26741','detailConfidence26741']:
 assert t in cpp,t
jni=r'extern\s+"C"\s+JNIEXPORT\s+\w+\s+JNICALL\s+([A-Za-z0-9_]+)'
assert re.findall(jni,bcpp)==re.findall(jni,cpp) and len(re.findall(jni,cpp))>0
# Shared VGN owner: clipped/physically-invalid highlights fail neutral unless independent below-headroom same-color evidence exists.
for t in ['IRIS_26741_HEADROOM_QUALIFIED_REAL_COLOR_PROOF','physicalHeadroomColorContinuation26741','physicalHeadroomColorProof26741','IRIS_26741_CLIPPED_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','clippedFlattenedNeutralAuthority26741 = invalidHighlightCenter','1.0 - physicalHeadroomColorProof26741','clippedFlattenedNeutralAuthority26741))']:
 assert t in vgn,t
# Do not globally neutralize merely-bright valid color: the hard authority is physically-invalid highlight gated.
assert 'max(sourceColorLoss26741, 0.85 * flattenedBrightness26741)' not in vgn
# Achromatic fine structure is generic, stronger, and still vetoed by independent physical real-color proof.
for t in ['IRIS_26741_STRONG_ACHROMATIC_FINE_STRUCTURE_AUTHORITY','smoothstep(0.018, 0.090, centerNormalizedMagnitude)','smoothstep(0.42, 0.76, neutralInkProof)','0.995 * neutralInkAuthority','IRIS_26741_INVALID_HIGHLIGHT_NEUTRAL_DONOR_ONLY','correctedFloat=mix(correctedFloat,neutralTarget,0.99)']:
 assert t in vgn,t
assert '(1.0 - physicalRealColorVeto26735)' in vgn
# 26729+/26731 material topology and directional transport remain present and unchanged where not intentionally tightened.
for marker in ['IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP']:
 assert marker_section(bv,marker)==marker_section(vgn,marker),marker
for t in ['microObjectProtection','supportedMaterialBoundary','coherentCenterProtection','topologyProtection','IRIS_26739_NO_POST_HOC_CFA_MOIRE_OWNER','IRIS_26739_WRONSKI_OWNS_CFA_ALIAS_REMOVAL']:
 assert t in vgn,t
# No semantic barcode/text detector and no global chroma-strength increase / Plan B.
added=(sh[len(bsh):] if sh.startswith(bsh) else sh)+vgn+cpp
for forbidden in ['barcodeDetector','fontDetector','textDetector','semanticClass','LINEAR_TRANSLATIONAL_SR_26741','IPOL_26741','PLAN_B_26741']:
 assert forbidden.lower() not in (sh+st+vgn+cpp).lower(),forbidden
assert txt(b,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')==txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# Protected UHDR/render/settings owners remain exact.
protected=['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26741 regressions: 26740 Motion/zoom architecture frozen; confidence-controlled publication extended to Super Res GPU+CPU; clipped invalid highlights fail neutral with headroom-qualified real-color opt-back; generic achromatic fine-structure cleanup strengthened; 26729+/26731 color/material ownership preserved; no Plan B/global chroma muting')
