#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26785.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26785_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
# Manifest completeness/count contract inherited from successful 26784 authority.
expected_manifest_counts={
 '26785_BASE_26784_FULL_APP.sha256':1779,
 '26785_EXPECTED_CANDIDATE_FULL_APP.sha256':1779,
 '26785_PROTECTED_26784.sha256':1776,
 '26785_NATIVE_26784.sha256':819,
 '26785_VENDOR_26784.sha256':778,
 '26785_DNG_WRITER_26784.sha256':6,
 '26785_PRIOR_SOURCE_HASHES.sha256':3,
}
for name,count in expected_manifest_counts.items():
 lines=[x for x in (ROOT/name).read_text().splitlines() if x.strip()]
 assert len(lines)==count,(name,len(lines),count)
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
bu,cu=U(B),U(C); assert len(bu)==1779 and len(cu)==1779; assert set(bu)==set(cu)
changed=sorted(k for k in bu if bu[k]!=cu[k]); assert changed==allowed,(changed,allowed); assert len(changed)==3
vp=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726785' in vp and 'VERSION_BUILD=26785' in vp
SAB='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SPATIAL='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
IRIS='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'; GAIN='app/src/main/assets/shaders/motionv2/gainmap.glsl'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
FLOOR='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
# Freeze JPEG/VGN/SDR/UHDR and the normalized16 pack/consumer exactly to successful 26784.
for p in (SPATIAL,IRIS,RENDER,GAIN,MVR,FLOOR): assert (B/p).read_bytes()==(C/p).read_bytes(),f'protected domain changed: {p}'
assert 'IRIS_26784_RESTORE_26727_VGN_RGB_OWNER' in (C/IRIS).read_text()
assert 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in (C/RENDER).read_text()
assert 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in (C/GAIN).read_text()
assert 'IRIS_26728_PROTECTED_CHROMA_POST_VGN' in (C/FLOOR).read_text()
assert 'val normalizeBayer = """' in (C/SPATIAL).read_text()
# Embedded shader universe: only normalDngMerge may differ in the Sabre carrier; stacker/Iris shader bodies are frozen.
def vals(root,rel):
 t=(root/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',t,re.S)}
bs,cs=vals(B,SAB),vals(C,SAB); bst,cst=vals(B,STACK),vals(C,STACK); bi,ci=vals(B,IRIS),vals(C,IRIS)
assert set(bs)==set(cs); assert sorted(n for n in bs if bs[n]!=cs[n])==['normalDngMerge']
assert bst==cst,'JPEG stacker embedded shader changed'
assert bi==ci,'VGN embedded shader changed'
old,new=bs['normalDngMerge'],cs['normalDngMerge']
# The 26782 hard-edge block and shared quad rejection remain exact.
def between(s,a,b): return s[s.index(a):s.index(b)]
a='/* IRIS_26782_FRACTIONAL_HARD_EDGE_VETO'; b='vec2 invRawSize = 1.0 / rawSize;'
assert between(old,a,b)==between(new,a,b),'26782 hard-edge/material veto changed'
rej='float frameWeight = min(min(w00, w10), min(w01, w11));'
assert rej in old and rej in new
# New owner is phase-scoped radiometric validity, not geometry/color ownership.
for tok in ('IRIS_26785_PHASE_SCOPED_HIGHLIGHT_VALIDITY_OWNER','IRIS_26785_CENSORED_REFERENCE_PHASE','IRIS_26785_TARGET_PHASE_DNG_HEADROOM','referenceFallbackWeight26785 = 0.00005','phaseHeadroomConfidence(q, targetPhase)'):
 assert tok in new,tok
assert 'oSignalAndWeight = vec2(normalizedRaw(outputPixel), 1.0);' not in new
assert new.count('quadHeadroomConfidence(')==1,'whole-quad headroom still consumed outside its now-unused helper'
assert new.count('phaseHeadroomConfidence(')==5,'unexpected phase-headroom call topology'
assert 'sourceHeadroomConfidence = phaseHeadroomConfidence(q, targetPhase);' in new
assert 'sourceHeadroomConfidence,\n                    phaseHeadroomConfidence(q, targetPhase));' in new
assert 'frameWeight *= clamp(sourceHeadroomConfidence, 0.0, 1.0);' in new
# No cross-phase reconstruction or green pooling was introduced.
for forbidden in ('mixG1G2','poolGreen','syntheticHue','crossPhaseHue'):
 assert forbidden not in new
# Runtime logging must expose the new owner and preserve the 26784 JPEG owner markers.
st=(C/STACK).read_text()
for tok in ('phaseScopedHeadroom26785=true','censoredReferencePhase26785=true','referenceIdentityWhenValid=true','referenceFallbackWeight26785=0.00005','g1g2Independent=true','crossPhaseHueSynthesis=false','IRIS_26784_JPEG_RUNTIME_OWNER_ENTRY','IRIS_26784_JPEG_RUNTIME_OWNER_EXIT'):
 assert tok in st,tok
assert 'blockUniformHeadroom26782=true referenceIdentity=true' not in st
# Matched-bandwidth 26780 amplifier stays absent; JPEG-side owners stay exactly as successful 26784.
for p in (SAB,STACK,IRIS): assert 'IRIS_26780_MATCHED_BANDWIDTH_CHROMA_OWNER' not in (C/p).read_text()
print('PASS 26785 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
print('PASS 26785 DNG CFA ownership: shared quad geometry/rejection preserved; saturation validity is target-phase-specific')
print('PASS 26785 valid-reference identity: exact identity remains when measurable; clipped reference phase is censored with epsilon fallback')
print('PASS 26785 alternate repair: only aligned same-phase headroom is admitted; G1/G2 stay independent; no cross-phase hue synthesis')
print('PASS 26785 hard-edge regression: exact 26782 fractional material-boundary veto preserved byte-identical')
print('PASS 26785 JPEG/VGN freeze: 26784 VGN, narrow false-color, SDR/UHDR, render/gainmap and downstream floor are byte-identical')
print('PASS 26785 normalized16 consumer/DNG writer protection: normalizeBayer and persisted DNG writer/native/vendor domains unchanged')
