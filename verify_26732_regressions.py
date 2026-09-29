#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26732_regressions.py BASE26731 CAND26732')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26732_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==5
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726732' in v and 'VERSION_BUILD=26732' in v
# Preserve 26729/26730/26731 true-color and frozen-material owners.
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
for t in [
 'IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26730_TRUE_MATERIAL_STEP_GATE',
 'IRIS_26731_ISOLATED_FALSE_COLOR_CLEANUP_FLAG','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY',
 'IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP',
 'IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO',
 'microObjectProtection','topologyProtection']:
 assert t in vgn,t
# 26732: clipped/invalid highlight groups can no longer self-protect or propagate bad hue.
for t in [
 'IRIS_26732_PHYSICAL_INVALID_HIGHLIGHT_CLUSTER_FLAG','highlightInvalidCleanup << 13','highlightInvalidAt',
 'IRIS_26732_TRUSTED_ONE_WAY_CLEANUP_TRANSPORT','IRIS_26732_CLUSTER_CLEANUP_WITHOUT_COLOR_LOSS',
 'IRIS_26732_SUSPICIOUS_CENTER_CANNOT_SELF_PROTECT','IRIS_26732_IIR_CLEANUP_IS_ONE_WAY',
 'IRIS_26732_INVALID_HIGHLIGHT_PAIR_CONSENSUS','IRIS_26732_CONNECTED_INVALID_HIGHLIGHT_CLEANUP',
 'invalidHighlightPairEvidence','measuredColorProtection']:
 assert t in vgn,t
# 26732: black/neutral fine structure lock must remain physical/topology-gated, not a semantic text rule.
for t in ['IRIS_26732_NEUTRAL_INK_PAIR_PROOF','IRIS_26732_NEUTRAL_FINE_STRUCTURE_LOCK','neutralInkPairEvidence','neutralInkRealColorVeto','0.70 * microObjectProtection']:
 assert t in vgn,t
assert 'textRecognition' not in vgn and 'OCR' not in vgn
# Geometry of 26731 teeth fix remains exact.
for t in ['ivec2(-1,0),3,1,ivec2(1,0),1,3','ivec2(0,-1),0,2,ivec2(0,1),2,0','ivec2(1,-1),4,6,ivec2(-1,1),6,4','ivec2(-1,-1),7,5,ivec2(1,1),5,7']:
 assert t in vgn,t
# High zoom: final 26724 shaders are direct runtime strings, not lazy source transforms.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26732_DIRECT_HIGH_ZOOM_FLOW_RUNTIME_OWNER','IRIS_26732_DIRECT_HIGH_ZOOM_RGB_RUNTIME_OWNER','IRIS_26724_WEAK_DISAGREEING_NATIVE_CHROMA_ADAPTATION','IRIS_26724_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT','robustSolveWeight']:
 assert t in sh,t
assert not re.search(r'val\s+highZoomFlowRefine26724\s*:\s*String\s+by\s+lazy',sh)
assert not re.search(r'val\s+highZoomRgbProtect26724\s*:\s*String\s+by\s+lazy',sh)
for stale in ['26724 high-zoom flow anchor missing','26724 high-zoom RGB anchor missing','noise-normalized-cost','weak-native-chroma']:
 assert stale not in sh,stale
# Fail-closed fallback: no scalar detail overlay may be produced after direct high-zoom failure.
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26732_HIGH_ZOOM_FAIL_CLOSED_NATIVE_FALLBACK','IRIS_26732_HIGH_ZOOM_CLEAN_NATIVE_FALLBACK','fallback=NATIVE_SABRE_VGN_NO_DETAIL staleOverlayImpossible=true','scalar26719Fallback=false cleanNativeFallback=true','cleanNativeFallbackOnFailure=true']:
 assert t in st,t
assert 'IRIS_26720_HIGH_ZOOM_RGB_FALLBACK_26719' not in st
# Only the private helper definition may remain; active failure branch must not call it.
assert st.count('reconstructHighZoomDetail26718(')==1
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'DIRECT_CFA_2X_WITH_CLEAN_NATIVE_SABRE_VGN_FALLBACK' in br
assert 'scalar26719Fallback=false cleanNativeFallback=true' in br
assert 'scalar26719Fallback=${highZoomDetailEnabled}' not in br
# Permanent 26729 R2 Java-overload failure regression remains true even though settings are untouched.
pk=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
assert not re.search(r'setInitial\(\s*SCOPE_GLOBAL\s*,\s*"[^"]+"\s*,\s*(?:true|false)\s*\)',pk)
# Unrelated architectural owners must remain byte-identical.
protected=[
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Domain invariance manifests.
def loadm(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26732_{stem}_BASE.sha256'); y=loadm(f'26732_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
print('PASS 26732 regressions: 26731 frozen material/color retention preserved; connected invalid-highlight cleanup + neutral fine-structure lock added; high-zoom final shaders direct and fail-closed to clean native Sabre/VGN; scalar QR/tile fallback removed; unrelated owners protected')
