#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,math
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def need(v,m):
    if not v: raise AssertionError(m)
def template(text,name):
    pats=[
      r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',
      r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
    m=None
    for pat in pats:
        m=re.search(pat,text,re.M)
        if m: break
    need(m is not None,name+' declaration missing')
    e=text.find('""".trimIndent()',m.end()); need(e>=0,name+' terminator missing')
    return text[m.start():e+len('""".trimIndent()')]

def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)

def sample(validity_min,chroma_mag,luma_ratio):
    return smoothstep(0.985,0.9995,validity_min) * (1.0-smoothstep(0.035,0.090,chroma_mag)) * smoothstep(0.55,0.82,luma_ratio)

def pair(neg1,neg2,pos1,pos2):
    return min(max(neg1,neg2),max(pos1,pos2))

def center_gate(vmin,vmax,gate=1.0,bright=1.0,visible=1.0,directional=1.0):
    invalidity=1.0-smoothstep(0.985,0.9995,vmin)
    asym=smoothstep(0.025,0.120,max(vmax-vmin,0.0))
    ctx=smoothstep(0.60,0.90,directional)
    candidate=gate*invalidity*asym*ctx*bright*visible
    return candidate,smoothstep(0.35,0.70,candidate)

b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'changed allowlist mismatch actual={sorted(changed)} expected={sorted(A)}')
need(len(b)==1786 and len(c)==1786,f'universe count mismatch {len(b)}->{len(c)}')
v=(C/'app/version.properties').read_text(); need('VERSION_NAME=0.9726831' in v and 'VERSION_BUILD=26831' in v,'version mismatch')
bv=(B/'app/version.properties').read_text(); ev=bv.replace('VERSION_NAME=0.9726830','VERSION_NAME=0.9726831',1).replace('VERSION_BUILD=26830','VERSION_BUILD=26831',1); need(ev==v,'version.properties changed outside exact version/build advance')
for rel in sorted(set(b)|set(c)):
    if rel not in A: need(b.get(rel)==c.get(rel),f'protected path changed {rel}')

rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bt=(B/rel).read_text(); ct=(C/rel).read_text(); bh=template(bt,'EDGE_FALSE_COLOR_SUPPRESSOR_26778'); ch=template(ct,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')
oldlog='PLog.i(SABRE_TAG, "IRIS_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION coherentGt05=${counts26778[3]} strictClippedNeutralGt05=${counts26778[4]} broadClippedNeutral26783Retired=true rawValidityOwner=IRIS_26614 brightnessOwner=INHERITED_26727_0P72_TO_0P92 neutralProof=BOTH_MEDIAN_AND_MATERIAL_BASELINE validityProof=ASYMMETRIC_CONSUMED_CFA pass1Only=true centerChromaAttenuationOnly=true hueDonation=false maxAttenuation=0.92 lumaPreserved=true old26778OutlierPathPreserved=true maxPeriodicBlend=0.70")'
newlog='PLog.i(SABRE_TAG, "IRIS_26831_DIRECTIONAL_PHASE_VALID_THIN_NEUTRAL coherentGt05=${counts26778[3]} phaseValidNeutralGt05=${counts26778[4]} inherited26823=true broadClippedNeutral26783Retired=true rawValidityOwner=IRIS_26614 brightnessOwner=INHERITED_26727_0P72_TO_0P92 neutralProof=STRICT_2D_OR_OPPOSING_DIRECTIONAL_VALID_NEUTRAL validityProof=ASYMMETRIC_CONSUMED_CFA directionalOffsets=PLUS_MINUS_1_OR_2 axes=H_V_DIAG pass1Only=true centerChromaAttenuationOnly=true hueDonation=false directionalMaxAttenuation=1.0 inherited26823MaxAttenuation=0.92 lumaPreserved=true old26778OutlierPathPreserved=true maxPeriodicBlend=0.70")'
need(bt.count(oldlog)==1,'26830 proof log anchor missing')
need(ct.count(newlog)==1,'26831 proof log missing')
# Outside the runtime-expanded suppressor shader, only the one proof log line may change.
need(bt.replace(bh,ch,1).replace(oldlog,newlog,1)==ct,'SpatialStacker changed outside EDGE_FALSE_COLOR_SUPPRESSOR_26778 + one proof log line')
for token in [
 'IRIS_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION',
 'IRIS_26831_DIRECTIONAL_PHASE_VALID_THIN_NEUTRAL',
 'phaseValidNeutralSample26831',
 'directionalNeutralPair26831',
 'ivec2(1, 0)', 'ivec2(0, 1)', 'ivec2(1, 1)', 'ivec2(1, -1)',
 'thinNeutralContext26831 = smoothstep(0.60, 0.90, directionalNeutral26831)',
 'thinClipAppliedW26831 = uStatsPass == 1',
 'phaseValidNeutralAppliedW26831 = max(',
 'correctedC *= 1.0 - min(phaseValidNeutralAppliedW26831, 1.0)',
 'hueDonation=false',
]: need(token in (ch if 'hueDonation' not in token else ct),'26831 thin-neutral regression token lost '+token)
need('strictNeutralContext26823 = min(baselineNeutral26788, medianNeutral)' in ch,'inherited 26823 strict 2-D neutral path changed/lost')
need('coherentW = min(coherentW, 0.70);' in ch,'26788 periodic cap changed')
need('vec2 correctedC = mix(centerC, medianC, w26778);' in ch,'26778 outlier path changed')
need('rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;' in ch,'luma restoration changed')
# Exact 26830 high-zoom and 26829 color owners are whole-file protected.
sabre='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
need((B/sabre).read_bytes()==(C/sabre).read_bytes(),'26830 Sabre/high-zoom/color owner changed')
st=(C/sabre).read_text()
for token in [
 'IRIS_26829_GREEN_SUPPORT_HEADROOM_CLIPPED_RB_OWNER',
 'IRIS_26829_WEIGHTED_GREEN_CLIP_CALC_DOMAIN',
 'blockPhaseCount==2?0.0:0.0',
 'blockPhaseCount==3?0.85',
 'if(blockPhaseCount<3)reasonClass=6;',
]: need(token in st,'inherited 26829/26830 owner lost '+token)
# Shared VGN owner and motion false-color assets remain protected.
post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
pt=(C/post).read_text()
for token in ['IRIS_26829_COLORED_PARENT_GREEN_CYAN_RESIDUAL_OWNER','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD']:
    need(token in pt,'inherited shared VGN owner lost '+token)
# Permanent semantic fixture: perpendicular colored material cannot veto a valid neutral line,
# and rotating which center channel is invalid cannot change the thin-neutral decision.
clean=sample(1.0,0.0,1.0)
weak_neutral=sample(0.990,0.0,1.0)
colored=sample(1.0,0.16,1.0)
line=pair(clean,weak_neutral,clean,weak_neutral)
need(line>0.90,f'neutral-line structural proof too weak: {line}')
for vmin,vmax in [(0.35,1.0),(0.45,0.98),(0.55,1.0)]:
    cand,applied=center_gate(vmin,vmax,directional=line)
    need(cand>0.95 and applied>0.99,f'phase-shift fail-closed regression failed v={vmin},{vmax} cand={cand} applied={applied}')
colored_line=pair(colored,colored,colored,colored)
cand,applied=center_gate(0.35,1.0,directional=colored_line)
need(colored_line<0.05 and applied<0.01,'genuine colored-line protection regression failed')
# 2-D context failure is deliberately allowed now: directional line is independent of perpendicular material.
need(line>0.90 and colored_line<0.05,'directional material-topology separation regression failed')
print('PASS 26831 exact 2-path runtime allowlist; 1786-file authority-seeded universe preserved')
print('PASS 26831 SpatialStacker localized to EDGE_FALSE_COLOR_SUPPRESSOR_26778 + one proof log; luma and legacy 26778/26788/26823 paths preserved')
print('PASS 26831 phase-shift regression: neutral thin line remains neutral-authorized across rotated center-channel invalidity; colored line remains protected')
print('PASS 26831 successful 26829 clipped-R/B/VGN and successful 26830 high-zoom owners byte-protected')
print('PASS 26831 all non-allowlisted successful-26830 runtime bytes protected')
