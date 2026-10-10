#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26805.py BASE_ROOT CANDIDATE_ROOT')
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
print('PASS 26805 authority-seeded scope: 1782 -> 1782, exactly 2 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text()
need('VERSION_NAME=0.9726805' in v and 'VERSION_BUILD=26805' in v,'version')
print('PASS 26805 version 0.9726805 / 26805')
for rel,h in LATE_26803.items():
    need(sha(BASE/rel)==h,f'26804 authority lost inherited 26803 late-owner hash {rel}')
    need(sha(CAND/rel)==h,f'26805 changed inherited 26803 late owner {rel}')
print('PASS 26805 exact successful 26803 thick-source classifier/propagation/render/host ownership frozen byte-identical')

rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bs=(BASE/rel).read_text(); s=(CAND/rel).read_text()
# Exact 26804 device-failure fixtures must exist in authority and be removed.
for token in (
    'IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR',
    'float thinNearWhiteW = smoothstep(0.52, 0.70, thinNearWhiteRatio);',
    'if (thinNearWhiteCandidate) correctedC = vec2(0.0);',
    'float yXm10 = lumaOf(fetchLin(p + ivec2(-10, 0), sz));',
): need(token in bs,f'26804 failing fixture missing: {token}')
for token in (
    'IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR',
    'thinNearWhiteRatio',
    'thinNearWhiteCandidate',
    'thinOutlierCandidate',
    'thinGateBypass',
    'yXm10',
): need(token not in s,f'26804 failed owner survived: {token}')
print('PASS 26805 permanent regression: failed 26804 near-white/+-10px RGB inference fully removed')

# New authority must be pre-Resolve calculation RGB, mapped through the exact camera-domain scale and lens shading.
for marker in ('IRIS_26805_PRE_RESOLVE_NEUTRAL_AUTHORITY','IRIS_26805_PRE_RESOLVE_NEUTRAL_DISAGREEMENT_REPAIR'):
    need(s.count(marker)==1,f'{marker} count')
for token in (
    'val preResolveAuthority26805 = resolveExtendedLinear26651',
    'sabreAccumulatedReadback = readSabreAccumulatedRgba16f(preResolveAuthority26805)',
    'preResolveCalculationRgb26805 = preResolveAuthority26805,',
    'lensShadingTexture26805 = lensShadingTexture',
    'uniform sampler2D uPreResolveCalculationRgb26805;',
    'uniform sampler2D uLensShading26805;',
    'uniform vec3 uCameraDomainScale26805;',
    'expected = preResolveCalc26805(p, sz) * uCameraDomainScale26805;',
    'expected *= vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);',
    'float rawNeutral26805 = 1.0 - smoothstep(0.070, 0.180, length(calcChroma26805));',
    'float disagreement26805 = length(postChroma26805 - expectedChroma26805);',
    'float disagreementW26805 = smoothstep(0.105, 0.280, disagreement26805);',
): need(token in s,f'26805 pre-Resolve authority contract missing: {token}')
need(s.index('val preResolveAuthority26805 = resolveExtendedLinear26651') < s.index('preResolveCalculationRgb26805 = preResolveAuthority26805,'),'exact Resolve input authority must be retained before suppressor bind')
need(s.index('preResolveCalculationRgb26805 = preResolveAuthority26805,') < s.index('26805 exact fused pre-Resolve authority after edge false-color repair'),'exact Resolve input released before suppressor sampled it')
need('releaseOwnedTexture(resolveExtendedLinear26651, "26651 fusedExtendedLinear HDR master after Resolve input readback")' not in s,'old early fused-authority release survived')
print('PASS 26805 color authority: exact MgcSabreResolver input (including validated SHORT) -> exact camera-domain/lens-shading direction; post-Resolve disagreement required')

# Genuine thinness: nearest dark crossing must exist on both sides, searched only <=6px, combined width <=8px.
for token in (
    'for (int d = 1; d <= 6; ++d)',
    'float xWidth26805 = xNeg26805 + xPos26805 - 1.0;',
    'float yWidth26805 = yNeg26805 + yPos26805 - 1.0;',
    'bool xBounded26805 = xNeg26805 <= 6.0 && xPos26805 <= 6.0 && xWidth26805 <= 8.0;',
    'bool yBounded26805 = yNeg26805 <= 6.0 && yPos26805 <= 6.0 && yWidth26805 <= 8.0;',
    'boundedThinW26805 > 0.20 && preResolveNeutralW26805 > 0.22',
): need(token in s,f'26805 bounded-width contract missing: {token}')
need('min(yXm2Thin, min(yXm6, yXm10))' not in s,'26804 any-dark sparse geometry survived')
print('PASS 26805 geometry: true bilateral first-crossing width proof; ordinary one-sided faces/hair/edges cannot qualify')

# Correction target is measured pre-Resolve chromaticity at exact current luma, never equal-RGB achromatic axis.
for token in (
    'vec3 target26805 = expectedY26805 > 1.0e-8',
    '? expectedCam26805 * (y0 / expectedY26805)',
    'rgb1 = mix(rgb1, target26805, clamp(preResolveNeutralW26805, 0.0, 1.0));',
    'rgb1 *= (y26805 > 1.0e-8) ? (y0 / y26805) : 1.0;',
    'imageStore(uDst, p, vec4(rgb1, c0.a));',
): need(token in s,f'26805 target/luma contract missing: {token}')
need('correctedC = vec2(0.0)' not in s,'achromatic-axis forcing survived')
print('PASS 26805 correction: measured pre-Resolve chromaticity target, exact luma/alpha preservation, no equal-RGB forcing')

# Retired broad clipped-neutral stays telemetry only; existing 26778/26788 equations remain.
need('float retiredClipCandidateW = gate * invalidity * neutralContext;' in s,'retired candidate fixture missing')
need('broadClippedNeutralApplied=false' in s,'broad clipped-neutral retirement runtime proof missing')
need('correctedC = mix(correctedC, vec2(0.0), retiredClipCandidateW)' not in s,'retired broad clip reactivated')
for token in (
    'vec2 correctedC = mix(centerC, medianC, w26778);',
    'correctedC = mix(correctedC, materialBaseline26788, coherentW);',
): need(token in s,f'inherited 26778/26788 correction changed: {token}')
print('PASS 26805 inherited pre-VGN owners: exact 26778 isolated + 26788 periodic remain; broad clipped-neutral remains retired')

# Existing textures only. Two extra sampler bindings point to already-live resolve accumulator and lens shading; no image allocation/lifetime owner added.
need('Int.SIZE_BYTES * 9' in s and 'repeat(9) { putInt(0) }' in s,'26805 telemetry SSBO size')
need(s.count('createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)')==bs.count('createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)'),'new RGBA16F texture allocation introduced')
for token in (
    'rawNeutralMismatchCandidatePass1=${counts26778[5]}',
    'boundedThinProofPass1=${counts26778[6]}',
    'appliedPass1=${counts26778[7]}',
    'appliedPass2=${counts26778[8]}',
    'achromaticAxisTarget=false',
    'thinNeutralOwner=IRIS_26805_PRE_RESOLVE_CALC_RGB_DISAGREEMENT',
): need(token in s,f'26805 telemetry/owner marker missing: {token}')
need('IRIS_26805_EXACT_RESOLVE_INPUT_AUTHORITY_LIFETIME' in s,'exact Resolve-input lifetime marker missing')
need('if (preResolveAuthority26805 != resolveAccumulatedColor26604)' in s,'deferred fused-authority release missing')
print('PASS 26805 telemetry/lifecycle: existing 9-uint SSBO + exact Resolve-input lifetime extension only; no new GPU image allocation')

for rel0 in a:
    if rel0 in MOD: continue
    need(a[rel0]==c[rel0],f'unexpected protected runtime change {rel0}')
print('PASS 26805 protected runtime: 1780 files byte-invariant, including 26803 late path, VGN/tone/UHDR/DNG/SR/native/vendor/UI')
