#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SABRE='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
CLASS='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
PROP='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
A={STACK,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(sorted(changed),sorted(A)); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726823' in v and 'VERSION_BUILD=26823' in v
# Frozen architecture: successful 26819 Sabre, 26818 VGN, 26821 DNG, and all 26822 downstream single-owner bytes.
for rel in (SABRE,POST,SP,CLASS,PROP,RENDER,MVR): assert h(B/rel)==h(C/rel),rel
sabre=(C/SABRE).read_text(); post=(C/POST).read_text(); sp=(C/SP).read_text()
for token in ['IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER','float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);','calculationCfa26793, weights, sourceValidity, type, covariance, 1,']:
    assert token in sabre,token
for token in ['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','smoothstep(0.70, 0.90','greenCleanupAuthority = 0.75']:
    assert token in post,token
for token in ['IRIS_26821_DNG_ALL_FOUR_PHASE_NEUTRAL_COHERENCE_OWNER','IRIS_26821_DNG_NONIDENTIFIABLE_GREEN_PHASE_OVERRIDE','normalized=iris26821NeutralPhaseCorrected(p,normalized,phase26786);']:
    assert token in sp,token
for rel,toks in {
CLASS:['IRIS_26822_SINGLE_OWNER_FALSE_COLOR_CONFIDENCE','IRIS_26822_CONTINUOUS_NEUTRAL_PARENT_EVIDENCE','Output=smoothstep(0.035,0.92,evidence);'],
PROP:['IRIS_26822_CONNECTED_FLOOD_RETIRED_PASS_THROUGH','Output=clamp(confidence,0.0,1.0);'],
RENDER:['IRIS_26822_SINGLE_OWNER_FALSE_COLOR_ATTENUATION','float keepFactor=1.0-attenuation;','vec3 corrected=vec3(y)+centerChroma*keepFactor;','linearSrgb=iris26822ApplySingleOwnerFalseColor(xy,linearSrgb);'],
MVR:['IRIS_26822_SINGLE_OWNER_FALSE_COLOR_ATTENUATION','inherited26797_26798_rgbWriters=RETIRED_NOT_CALLED','compatibilityPassThrough=true connectedFlood=false'],
}.items():
    text=(C/rel).read_text()
    for token in toks: assert token in text,(rel,token)
# New authority is narrowly inside the already-existing pre-VGN suppressor. No lifecycle/allocation redesign.
bs=(B/STACK).read_text(); cs=(C/STACK).read_text(); assert bs!=cs
for token in [
'IRIS_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION',
'float validitySpread26823 = max(strongestValidity - measuredValidity, 0.0);',
'float asymmetricLoss26823 = smoothstep(0.025, 0.120, validitySpread26823);',
'float strictNeutralContext26823 = min(baselineNeutral26788, medianNeutral);',
'float brightHighlight26823 = smoothstep(0.72, 0.92,',
'float strictClipCandidateW26823 = gate * invalidity * asymmetricLoss26823 *',
'float strictClipAppliedW26823 = uStatsPass == 1',
'? min(strictClipCandidateW26823, 0.92) : 0.0;',
'correctedC *= 1.0 - strictClipAppliedW26823;',
'broadClippedNeutral26783Retired=true',
'clippedNeutral26823=PHASE_VALID_BRIGHT_NEUTRAL_ATTENUATION',
'strictClippedNeutral26823=true',
'hueDonation=false',
]: assert token in cs,token
# Old broad OR-neutral candidate remains retired rather than revived.
for forbidden in ['float neutralContext = max(baselineNeutral26788, medianNeutral);','float retiredClipCandidateW = gate * invalidity * neutralContext;']:
    assert forbidden not in cs,forbidden
# Existing isolated-outlier and periodic material-baseline paths remain present.
for token in ['IRIS_26788_MATERIAL_BASELINE_PERIODIC_FALSE_COLOR','float w26778 = gate * smoothstep(uOutlierLo, uOutlierHi, dev);','coherentW = min(coherentW, 0.70);','rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;']:
    assert token in cs,token
# Stats/GPU carrier size and two-pass call mechanics must remain unchanged.
for token in ['ByteBuffer.allocateDirect(Int.SIZE_BYTES * 5)','passes=2','uniform1i(edgeFalseColorSuppressor26778Program, "uStatsPass", statsPass)']:
    assert cs.count(token)==bs.count(token),(token,bs.count(token),cs.count(token))
assert cs.count('uniform int uStatsPass;')==bs.count('uniform int uStatsPass;')==1
for token in ['glGenTextures','glGenBuffers','new GLTexture','GLTexture(']:
    assert cs.count(token)==bs.count(token),(token,bs.count(token),cs.count(token))
# DNG/UHDR/render and all source outside exact allowlist are guaranteed byte-identical by changed-set equality above.
print('PASS 26823 exact 2-path scope: phase-valid bright-neutral pre-VGN center-chroma attenuation; broad 26783 branch retired; successful 26822 single-owner, 26819 Sabre, 26818 VGN, 26821 DNG and GPU lifecycle protected')
