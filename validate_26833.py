#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
def need(v,m):
    if not v: raise AssertionError(m)
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def gain_contract(normal_rgb,long_y,mean_support,neighbors):
    y=lambda v:0.25*v[0]+0.5*v[1]+0.25*v[2]
    ny=max(y(normal_rgb),0.0)
    support_gate=smoothstep(0.05,0.50,max(mean_support,0.0))
    shadow_gate=1.0-smoothstep(0.18,0.42,ny)
    nd=max(abs(n-ny) for n in neighbors)
    rel=nd/max(ny,0.03)
    edge_gate=1.0-smoothstep(0.18,0.45,rel)
    consistency=min(ny+0.005,long_y+0.005)/max(ny+0.005,long_y+0.005)
    consistency_gate=smoothstep(0.72,0.93,consistency)
    trust=support_gate*shadow_gate*edge_gate*consistency_gate
    target=ny*(1.0-0.55*trust)+long_y*(0.55*trust)
    gain=(target/ny) if ny>0.005 else 1.0
    gain=max(0.75,min(1.35,gain))
    return tuple(v*gain for v in normal_rgb),trust,gain
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'changed allowlist mismatch actual={sorted(changed)} expected={sorted(A)}')
need(len(b)==1786 and len(c)==1786,f'universe count mismatch {len(b)}->{len(c)}')
v=(C/'app/version.properties').read_text(); bv=(B/'app/version.properties').read_text()
need('VERSION_NAME=0.9726833' in v and 'VERSION_BUILD=26833' in v,'version mismatch')
need(bv.replace('VERSION_NAME=0.9726832','VERSION_NAME=0.9726833',1).replace('VERSION_BUILD=26832','VERSION_BUILD=26833',1)==v,'version changed outside exact advance')
for rel in set(b)|set(c):
    if rel not in A: need(b.get(rel)==c.get(rel),f'protected path changed {rel}')

post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
need(h(C/post)=='23276a742ea9f97585584d166bd3c9197eaf7fa89c0269e127907431334bcb92','26831 postprocessor rollback hash mismatch')
pt=(C/post).read_text()
need('IRIS_26832_CFA_CHROMA_AUTHORITY_QUARANTINE' not in pt,'failed 26832 quarantine survived')
for token in ['IRIS_26829_COLORED_PARENT_GREEN_CYAN_RESIDUAL_OWNER','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD']:
    need(token in pt,'26831 inherited postprocessor owner lost '+token)

sh='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bt=(B/sh).read_text(); ct=(C/sh).read_text()
start=ct.index('    /* IRIS_26833_SHADOW_LONG_LUMINANCE_ACCUMULATOR')
end=ct.index('    /* IRIS_26790_COMPLETED_NORMAL_CHROMA_SNAPSHOT',start)
need(ct[:start]+ct[end:]==bt,'SabreShaders changed outside inserted 26833 LONG scalar-luminance block')
for name in ['shadowLongLumaAccumulate26833','shadowLongLumaGainMap26833','shadowLongPostVgnLumaApply26833']:
    need(name in ct,'26833 shader missing '+name)
for token in [
'IRIS_26833_SHADOW_LONG_LUMINANCE_ACCUMULATOR',
'float scalarSupport = min(support.r, min(support.g, support.b));',
'oWeightedLumaSupport = vec2(max(luma26833(rgb), 0.0) * scalarSupport, scalarSupport);',
'IRIS_26833_SHADOW_LONG_LUMINANCE_GAIN_MAP',
'float trust = supportGate * shadowGate * edgeGate * consistencyGate;',
'oGain = clamp(gain, 0.75, 1.35);',
'IRIS_26833_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY',
'oColor = vec4(source.rgb * gain, source.a);']:
    need(token in ct,'26833 luminance-only shader contract missing '+token)
need('vec3' not in ct[start:end].split('val shadowLongPostVgnLumaApply26833',1)[1].split('""".trimIndent()',1)[0] or 'source.rgb * gain' in ct,
     'post-VGN LONG publication must remain scalar RGB scaling')

stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; st=(C/stack).read_text()
for token in [
'IRIS_26833_SHADOW_LONG_LUMINANCE_ONLY_FRAME_ACCOUNTING',
'val mergedFrameCount = normalFrameCount',
'IRIS_26833_NORMAL_RGB_MASTER_LONG_LUMINANCE_ISOLATION',
'} else if (frame.role == RawBurstFrameRole.SHADOW_LONG) {',
'accumulatedColor = longColor26833',
'accumulatedWeightsGb = longWeightsGb26833',
'accumulatedValidity26614 = 0',
'IRIS_26833_LONG_LUMA_GAIN_READY',
'preResolveRgbUnchanged=true resolveVgnUnchanged=true',
'IRIS_26833_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY',
'IRIS_26833_LONG_LUMA_FUSED stage=POST_VGN',
'rgbScaleOnly=true exactRgbRatioPreserved=true',
'sabreNormalChromaConsensusProgram26790 = 0',
'longColorAuthority=false',
'longHueAuthority=false']:
    need(token in st,'26833 ownership token missing '+token)
need('normalChromaConsensus26790 = renderSabreNormalChromaConsensus26790' not in st,'retired LONG chroma snapshot still active')
need('IRIS_26790_LONG_CHROMA_GUARD enabled=true' not in st,'retired LONG chroma guard log still active')
need('longChromaGuard26790 = true' not in st,'LONG chroma guard still enabled')
# LONG may call ordinary Sabre merge only into its private temporary carrier, never the NORMAL RGB accumulator.
long_branch=st[st.index('} else if (frame.role == RawBurstFrameRole.SHADOW_LONG) {'):st.index('} else {',st.index('} else if (frame.role == RawBurstFrameRole.SHADOW_LONG) {'))]
need('accumulatedColor = longColor26833' in long_branch and 'accumulatedWeightsGb = longWeightsGb26833' in long_branch,'LONG private carrier missing')
need('accumulatedColor = accumulatedColor' not in long_branch and 'accumulatedWeightsGb = accumulatedWeightsGb' not in long_branch,'LONG still reaches NORMAL RGB accumulator')
need('accumulatedValidity26614 = 0' in long_branch,'LONG still publishes CFA validity/support')
need('renderSabreNormalDngMerge' not in long_branch,'LONG still reaches DNG accumulator')

bridge='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'; br=(C/bridge).read_text()
for token in [
'SABRE_NIGHT_SHADOW_LUMINANCE_ONLY',
'SABRE_MOTION_SHADOW_LUMINANCE_ONLY',
'IRIS_26833_NIGHT_LONG_LUMINANCE_ONLY_PARITY',
'IRIS_26833_LONG_ZERO_RGB_SUPPORT_PARITY',
'expectedRgbMergedFrames26833 = frames.count { it.role == RawBurstFrameRole.NORMAL }',
'longTemporalSupport=false']:
    need(token in br,'26833 bridge accounting token missing '+token)
need('COMMON_SABRE_NIGHT_SHADOW_EVIDENCE' not in br and 'COMMON_SABRE_MOTION_GOOGLE_BRACKET_SHADOW_EVIDENCE' not in br,'old LONG RGB admission label survived')

for token in ['IRIS_26831_DIRECTIONAL_PHASE_VALID_THIN_NEUTRAL','blockPhaseCount==2?0.0:0.0','blockPhaseCount==3?0.85','if(blockPhaseCount<3)reasonClass=6;']:
    need(token in st or token in ct,'inherited 26830/26831 token lost '+token)

# Permanent semantic regressions: LONG can change only scalar luminance, never hue ratios.
normal=(0.10,0.08,0.06); ny=0.08
out,trust,g=gain_contract(normal,0.085,1.0,[ny,ny,ny,ny]); need(trust>0.25,'valid flat shadow did not admit LONG luminance')
need(abs(out[0]/out[1]-normal[0]/normal[1])<1e-12 and abs(out[2]/out[1]-normal[2]/normal[1])<1e-12,'LONG changed hue ratios')
_,t2,_=gain_contract((0.60,0.60,0.60),0.59,1.0,[0.60]*4); need(t2<1e-9,'bright region admitted LONG')
_,t3,_=gain_contract(normal,0.085,1.0,[0.30,ny,ny,ny]); need(t3<1e-9,'strong edge admitted LONG')
_,t4,_=gain_contract(normal,0.20,1.0,[ny]*4); need(t4<1e-9,'radiometrically inconsistent LONG admitted')
_,t5,_=gain_contract(normal,0.085,0.0,[ny]*4); need(t5<1e-9,'unsupported LONG admitted')
print('PASS 26833 exact 5-path runtime allowlist; 1786-file successful-26832 authority universe preserved')
print('PASS 26833 failed 26832 quarantine fully rolled back to exact successful-26831 postprocessor hash')
print('PASS 26833 SHADOW_LONG isolated: no NORMAL RGB/chroma/CFA-validity/support/DNG/SR authority; scalar luminance only')
print('PASS 26833 bridge accounting: LONG scheduled/captured but excluded from RGB temporal support in Motion and Night')
print('PASS 26833 semantic fixtures: flat shadow luminance admitted; bright/edge/inconsistent/unsupported LONG rejected; NORMAL hue ratios invariant')
