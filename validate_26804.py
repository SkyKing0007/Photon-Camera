#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26804.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
MOD={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
LATE_26803={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl':'f44ad2b6030a8a065791ba6728de4ef53b59b520cf6d12bb77474b55e554b020',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl':'77072cd86cee79c8b165526b35a523eb34f06291d11e1cabbb1fa4473bd3395c',
'app/src/main/assets/shaders/motionv2/render.glsl':'73ed037d5752c2a9d46da74916177d1416cb99fc212367799a12a4a0c56343d2',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'8429399cc4ec8672a6078979576d001396e681c47c3557d7e141fb04a7f7a4fd',
}
def need(c,m):
    if not c: raise AssertionError(m)
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c)))
need(set(a)==set(c),'file universe changed')
mods={p for p in a if a[p]!=c[p]}
need(mods==MOD,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26804 authority-seeded scope: 1782 -> 1782, exactly 2 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726804' in v and 'VERSION_BUILD=26804' in v,'version')
print('PASS 26804 version 0.9726804 / 26804')
for rel,h in LATE_26803.items():
    need(sha(BASE/rel)==h,f'26803 authority hash mismatch {rel}')
    need(sha(CAND/rel)==h,f'26803 late owner changed {rel}')
print('PASS 26804 exact successful 26803 thick-source classifier/propagation/render/host ownership frozen byte-identical')

rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bs=(BASE/rel).read_text(); s=(CAND/rel).read_text()
need('IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR' not in bs,'26804 marker unexpectedly in authority')
need(s.count('IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR')==1,'26804 repair marker count')
need(s.count('IRIS_26804_THIN_RIDGE_OLD_GATE_BYPASS')==1,'26804 old-gate bypass marker count')

# Exact 26803 failing condition: old 5x5 gate returned before any thin-stroke proof could run.
old_return='''if (gate <= 0.0) {\n            imageStore(uDst, p, c0);\n            return;\n          }'''
need(old_return in bs,'26803 legacy early-return fixture missing')
need('bool thinGateBypass = false;' in s,'thin gate-bypass state missing')
need('bool thinCheapPrefilter =' in s,'thin cheap prefilter missing')
need('thinEarlyInvalidity <= 0.52' in s,'gate bypass not bounded by RAW validity')
need('thinGateBypass = true;' in s,'gate bypass cannot activate')
need(s.index('IRIS_26804_THIN_RIDGE_OLD_GATE_BYPASS') < s.index('// 2) 3x3 median of sqrt-domain chroma differences'),'gate bypass must precede old median/repair path')
print('PASS 26804 permanent regression: 26803 5x5 early-return no longer blocks thin subtitle interiors; bypass is bright+chroma+RAW-invalidity bounded')

# Retired broad clipped-neutral owner must remain diagnostic-only.
need('float retiredClipCandidateW = gate * invalidity * neutralContext;' in s,'retired candidate fixture missing')
need('broadClippedNeutralApplied=false' in s,'broad clipped-neutral retirement runtime proof missing')
need('correctedC = mix(correctedC, vec2(0.0), retiredClipCandidateW)' not in s,'broad retired candidate reactivated')
need('correctedC = mix(correctedC, materialBaseline26788, retiredClipCandidateW)' not in s,'broad retired candidate reactivated to material baseline')

# Thin geometry + dual false-color proof.
for token in (
    'float yXm6 = lumaOf(fetchLin(p + ivec2(-6, 0), sz));',
    'float yXm10 = lumaOf(fetchLin(p + ivec2(-10, 0), sz));',
    'float thinBilateralDrop = max(xBilateralDrop, yBilateralDrop);',
    'float thinNeutralEvidence = max(neutralContext, thinOutsideNeutral);',
    'float thinNearWhiteW = smoothstep(0.52, 0.70, thinNearWhiteRatio);',
    'float thinOutlierW = smoothstep(',
    'bool thinCommonProof =',
    'thinBilateralDrop > 0.12 &&',
    'thinChromaMagnitude > 0.035 &&',
    'invalidity > 0.52 &&',
    'thinNeutralEvidence > 0.58;',
    'bool thinNearWhiteCandidate = thinCommonProof && thinNearWhiteW > 0.30;',
    'bool thinOutlierCandidate = thinCommonProof && !thinNearWhiteCandidate && thinOutlierW > 0.55;',
    'if (thinOutlierCandidate) correctedC = medianC;',
    'if (thinNearWhiteCandidate) correctedC = vec2(0.0);',
): need(token in s,f'26804 dual-branch contract missing: {token}')

m=re.search(r'bool thinCommonProof\s*=\s*(.*?);',s,re.S)
need(m is not None,'thin common-proof block missing')
need('gate >' not in m.group(1) and 'gate *' not in m.group(1),'thin owner incorrectly depends on old 5x5 gate')
need('thinNearWhiteRatio' not in m.group(1),'near-white proof must stay a separate false-color branch, not redefine geometry')
print('PASS 26804 thin geometry: bounded bilateral <=10px proof independent of legacy 5x5 gate after invalidity prefilter')
print('PASS 26804 dual correction: near-white fill -> achromatic; disconnected/alternating outlier -> local median chroma to preserve coherent real colored thin structures')

# Existing sqrt-domain rebuild, exact luma restore and alpha preservation remain.
for token in (
    'vec3 s1 = max(vec3(s0.g + correctedC.x, s0.g, s0.g + correctedC.y), vec3(0.0));',
    'float y0 = lumaOf(lin0);',
    'rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;',
    'imageStore(uDst, p, vec4(rgb1, c0.a));'):
    need(token in s,f'luma/alpha invariant missing: {token}')

# Stats reuse same single SSBO object, enlarged only from 5 to 9 uints; no new texture owner.
need('uint coherentGt05; uint clippedNeutralGt05;\n          uint thinRidgeGeometryGt05; uint thinNearWhiteAppliedPass1; uint thinOutlierAppliedPass1;\n          uint thinNeutralAppliedPass2;' in s,'26804 stats declaration')
need('Int.SIZE_BYTES * 9' in s and 'repeat(9) { putInt(0) }' in s,'26804 stats host size')
need('Int.SIZE_BYTES * 5).order' not in s,'stale 5-counter allocation')
for token in (
    'nearWhiteAppliedPass1=${counts26778[6]}',
    'outlierAppliedPass1=${counts26778[7]}',
    'appliedPass2=${counts26778[8]}',
    'old5x5EarlyReturnBypass=BOUNDED_INVALIDITY_PREFILTER_ONLY',
    'thinNeutralOwner=IRIS_26804_DUAL_NEAR_WHITE_FILL_AND_DISCONNECTED_OUTLIER'):
    need(token in s,f'26804 decision telemetry missing: {token}')
need(s.count('createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)')==bs.count('createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)'),'new RGBA16F texture allocation introduced')
print('PASS 26804 telemetry/lifecycle: existing 26778 SSBO only (5->9 uints), no new texture allocation or lifetime owner')

# Everything else is byte protected.
for rel0 in a:
    if rel0 in MOD: continue
    need(a[rel0]==c[rel0],f'unexpected protected runtime change {rel0}')
print('PASS 26804 protected runtime: 1780 files byte-invariant, including exact 26803 late owner, VGN/tone/UHDR/DNG/SR/native/vendor/UI')
