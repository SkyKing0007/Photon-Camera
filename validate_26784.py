#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26784.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26784_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
bu,cu=U(B),U(C); assert len(bu)==1779 and len(cu)==1779; assert set(bu)==set(cu)
changed=sorted(k for k in bu if bu[k]!=cu[k]); assert changed==allowed,(changed,allowed); assert len(changed)==3
vp=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726784' in vp and 'VERSION_BUILD=26784' in vp
SAB='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
IRIS='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'; GAIN='app/src/main/assets/shaders/motionv2/gainmap.glsl'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
FLOOR='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
# Protected domains: clean DNG/CFA, current SDR contrast/UHDR rebase, and downstream floor implementation remain byte-identical.
for p in (SAB,RENDER,GAIN,MVR,FLOOR): assert (B/p).read_bytes()==(C/p).read_bytes(),f'protected domain changed: {p}'
assert 'IRIS_26782_DNG_EDGE_SAFE_QUAD_OWNER' in (C/SAB).read_text()
assert 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in (C/RENDER).read_text()
assert 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in (C/GAIN).read_text()
assert 'IRIS_26728_PROTECTED_CHROMA_POST_VGN' in (C/FLOOR).read_text()
# Embedded shader extraction.
def vals(root,rel):
 t=(root/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',t,re.S)}
bs,cs=vals(B,STACK),vals(C,STACK); bi,ci=vals(B,IRIS),vals(C,IRIS)
# Stacker: exactly one embedded shader changes. Keep legacy 26778 + coherent 26782 mechanism; retire only independent clipped-neutral application.
stack_changed=sorted(n for n in bs if bs[n]!=cs.get(n)); assert stack_changed==['EDGE_FALSE_COLOR_SUPPRESSOR_26778'],stack_changed
assert set(bs)==set(cs)
bedge,cedge=bs['EDGE_FALSE_COLOR_SUPPRESSOR_26778'],cs['EDGE_FALSE_COLOR_SUPPRESSOR_26778']
assert 'IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD' in cedge and 'IRIS_26784_RETIRE_BROAD_CLIPPED_NEUTRAL' in cedge
assert 'correctedC = mix(correctedC, pairMid, coherentW);' in cedge
assert 'correctedC = mix(correctedC, vec2(0.0), clipW);' not in cedge
assert 'float retiredClipCandidateW = gate * invalidity * neutralContext;' in cedge
# Prove the coherent building-protection block itself is byte-identical through the start of clipped-neutral section.
def between(s,a,b): return s[s.index(a):s.index(b)]
coh_a='/* IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD'
coh_b='/* IRIS_26782_CLIPPED_NEUTRAL_GUARD'
assert between(bedge,coh_a,coh_b)==between(cedge,coh_a,coh_b),'26782 coherent bipolar building-protection block changed'
# Iris shader universe: remove only 26783 guard; modify only universalAdaptiveColor to restore corrected RGB owner.
assert set(bi)-set(ci)=={'postVgnNeutralGuard26783'},set(bi)-set(ci)
assert not(set(ci)-set(bi)),set(ci)-set(bi)
for n in ci:
 if n!='universalAdaptiveColor26561': assert bi[n]==ci[n],f'inherited Iris shader changed: {n}'
old=bi['universalAdaptiveColor26561']; new=ci['universalAdaptiveColor26561']
# Normalize exactly the ownership assignment/comment; all metadata/CFA logic must otherwise be identical.
def norm_universal(s):
 # Ignore only the 26784 ownership annotation and the one correctedRgb assignment; dedent changes leading spaces.
 s=re.sub(r'\n\s*/\* IRIS_26784_RESTORE_26727_VGN_RGB_OWNER.*?\*/\s*','\n',s,flags=re.S)
 s=re.sub(r'(?m)^\s*vec3 correctedRgb = center; // IRIS_26766_BJZHOU_CAMERA_RGB_CONTRACT: preserve VGN camera RGB; alpha metadata remains unchanged\.$','<CORRECTED_RGB_OWNER>',s)
 s=re.sub(r'(?m)^\s*vec3 correctedRgb = clamp\(vec3\(centerLuma\) \+ correctedChroma, 0\.0, 1\.0\);$','<CORRECTED_RGB_OWNER>',s)
 return s
assert norm_universal(old)==norm_universal(new),'unexpected universalAdaptiveColor delta outside corrected RGB ownership'
assert 'IRIS_26784_RESTORE_26727_VGN_RGB_OWNER' in new
assert 'vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma, 0.0, 1.0);' in new
assert 'uint encodedProtection = uPhysicalPreVgnValid != 0' in new
# No 26783 post-VGN executable owner survives.
it=(C/IRIS).read_text(); st=(C/STACK).read_text()
for tok in ('postVgnNeutralGuard26783Program','dispatchPostVgnNeutralGuard26783','Iris26529SpatialRgbChromaShaders.postVgnNeutralGuard26783','val postVgnNeutralGuard26783 = """'): assert tok not in it,tok
assert 'val postVgnNeutralGuard26783Applied = false' in it and 'assembledRgb = finalScratch' in it
assert 'IRIS_26784_SINGLE_VGN_RGB_OWNER' in it
# Runtime proof contract.
assert 'IRIS_26784_JPEG_RUNTIME_OWNER_ENTRY' in st and 'IRIS_26784_JPEG_RUNTIME_OWNER_EXIT' in st
for tok in ('coherentBipolar26782=true','clippedNeutral26782=false','postVgnGuard26783=false','vgnRgbOwner26784=IRIS_26727_CORRECTED_VGN_RGB','dngReconstructionFrozen26782=true','broadClippedNeutralRetired=true'): assert tok in st,tok
assert 'IRIS_26784_NARROW_FALSE_COLOR_OWNER' in st and 'broadClippedNeutralApplied=false' in st
# 26769 is preserved and remains the single narrow downstream exception; its floor-veto semantics stay unchanged.
assert bi['bipolarColorTrust26769']==ci['bipolarColorTrust26769']
for tok in ('float finalFloor=(eradicate?0.0:existingFloor)','IRIS_26776_NO_PHASE_INVALID_CHROMA_RESURRECTION'): assert tok in ci['bipolarColorTrust26769'],tok
# Matched-bandwidth 26780 amplifier remains absent.
for p in (SAB,STACK,IRIS): assert 'IRIS_26780_MATCHED_BANDWIDTH_CHROMA_OWNER' not in (C/p).read_text()
print('PASS 26784 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
print('PASS 26784 DNG/CFA freeze: Sabre/DNG authority byte-identical to successful 26783')
print('PASS 26784 clean-building protection: exact 26782 coherent-bipolar block byte-identical; legacy 26778 path preserved')
print('PASS 26784 broad overreach retired: clipped-neutral candidate remains telemetry-only and cannot alter RGB')
print('PASS 26784 VGN ownership: 26727 corrected-RGB handoff restored while current 26783 alpha/provenance contract remains byte-identical')
print('PASS 26784 stale owner removal: 26783 post-VGN guard is absent from compiled/active shader ownership')
print('PASS 26784 downstream subordination: 26769 floor veto unchanged; 26728 floor implementation protected unchanged')
print('PASS 26784 SDR/UHDR protection: render, gainmap, MotionV2Render byte-identical to successful 26783')
