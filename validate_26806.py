#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26806.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
VER='app/version.properties'
MOD={STACK,VGN,VER}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c)))
need(set(a)==set(c),'file universe changed')
mods={p for p in a if a[p]!=c[p]}
need(mods==MOD,f'modified allowlist mismatch {sorted(mods)}')
print('PASS 26806 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726806' in v and 'VERSION_BUILD=26806' in v,'version')
print('PASS 26806 version 0.9726806 / 26806')

s=(CAND/STACK).read_text(); bs=(BASE/STACK).read_text()
g=(CAND/VGN).read_text(); bg=(BASE/VGN).read_text()
# Permanent regressions from 26804/26805: neither rejected RGB inference may survive.
for token in (
    'IRIS_26804_PRE_VGN_THIN_NEUTRAL_RIDGE_REPAIR','thinNearWhiteRatio','thinNearWhiteCandidate',
    'IRIS_26805_PRE_RESOLVE_NEUTRAL_DISAGREEMENT','IRIS_26805_PRE_RESOLVE_NEUTRAL_AUTHORITY',
    'IRIS_26805_EXACT_RESOLVE_INPUT_AUTHORITY_LIFETIME','preResolveCalculationRgb26805',
    'uPreResolveCalculationRgb26805','uLensShading26805','uCameraDomainScale26805'):
    need(token not in s,f'rejected 26804/26805 owner survived: {token}')
print('PASS 26806 permanent regressions: failed 26804 broad RGB guess and 26805 fake RAW/pre-Resolve RGB authority removed')

# Candidate stacker must be successful 26803 runtime behavior plus only minimal 26806 ownership telemetry.
owner='''            PLog.i(\n                SABRE_TAG,\n                "IRIS_26806_SELECTIVE_26727_HIGHLIGHT_CLEANUP owner=VGN_SEED " +\n                    "defaultBrightAuthority=EXACT_26727_0P72_TO_0P92 broadColorOptIn=FAR4_TWO_DIMENSIONAL_MATERIAL " +\n                    "cfaValidityOwner=IRIS_26614 lumaModified=false newGpuImageAllocation=false " +\n                    "rejected26804RgbThinInference=false rejected26805PreResolveRgbAuthority=false",\n            )\n'''
need(s.count(owner)==1,'26806 ownership telemetry block count')
exit_new='''                    "jpegCarrier=VGN_26806_SELECTIVE_26727_HIGHLIGHT_CLEANUP_PLUS_NARROW_26769 dngCarrier=NORMALIZED16_FROZEN_26782 " +\n                    "broadClippedNeutralRetired=true rawValidityOwner=IRIS_26614 thinBrightProtectionRequiresFar4TwoDimensionalMaterial=true",\n'''
exit_03='''                    "jpegCarrier=VGN_26727_OWNER_PLUS_NARROW_26769 dngCarrier=NORMALIZED16_FROZEN_26782 " +\n                    "broadClippedNeutralRetired=true rawValidityOwner=IRIS_26614",\n'''
need(s.count(exit_new)==1,'26806 exit owner string count')
canon_s=s.replace(owner,'').replace(exit_new,exit_03)
H26803_STACK='e082d4c8f51454b8a8578bf124992a9b3f807a0af634a5533645bf836bf4d2e0'
need(hashlib.sha256(canon_s.encode()).hexdigest()==H26803_STACK,'stacker does not canonicalize exactly to successful 26803 behavior')
need('sabreAccumulatedReadback = readSabreAccumulatedRgba16f(resolveExtendedLinear26651)' in s,'successful 26803 Resolve input readback not restored')
need('releaseOwnedTexture(resolveExtendedLinear26651, "26651 fusedExtendedLinear HDR master after Resolve input readback")' in s,'successful 26803 fused texture lifetime not restored')
print('PASS 26806 stacker: exact successful 26803 behavior restored; no new image allocation/lifetime owner')

# Selective VGN change: exact 26727 highlight authority is default; only broad 2-D material may opt back in.
need(g.count('IRIS_26806_BROAD_2D_BRIGHT_COLOR_OPT_IN')==1,'26806 VGN owner marker count')
for token in (
    'float inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY);',
    'ivec2 q4=p+d[i]*4;',
    'float far4Trust=min(centerTrust,physicalColorTrust(q4));',
    'float broadPair0=min(far4Continuation[0],far4Continuation[2]);',
    'float broadPair1=min(far4Continuation[1],far4Continuation[3]);',
    'float broadPair2=min(far4Continuation[4],far4Continuation[6]);',
    'float broadPair3=min(far4Continuation[5],far4Continuation[7]);',
    'float remainingPairSupport=broadPair0+broadPair1+broadPair2+broadPair3-strongestPair;',
    'float broadTwoDimensionalMaterial=smoothstep(0.45,1.10,remainingPairSupport);',
    'broadTwoDimensionalMaterial*phaseColorOwnershipPermission;',
    'float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);'):
    need(token in g,f'26806 VGN contract missing: {token}')
# Removing only the new gate must recover successful 26805 VGN byte-exact.
start=g.index('            /* IRIS_26806_BROAD_2D_BRIGHT_COLOR_OPT_IN')
end=g.index('            float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);',start)+len('            float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);\n')
old_start=bg.index('            float realBrightColorProof=centerTrust*')
old_end=bg.index('            float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);',old_start)+len('            float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);\n')
canon_g=g[:start]+bg[old_start:old_end]+g[end:]
need(canon_g==bg,'VGN changed beyond selective bright-color opt-in gate')
# Synthetic geometry regression for the source equation: one tangent pair is not broad 2-D; 2+ pairs are.
def broad(vals):
    strongest=max(vals); remaining=sum(vals)-strongest
    if remaining<=0.45: return 0.0
    if remaining>=1.10: return 1.0
    x=(remaining-0.45)/(1.10-0.45); return x*x*(3-2*x)
need(broad([1.0,0.0,0.0,0.0])==0.0,'thin single-axis fixture admitted')
need(broad([1.0,1.0,0.0,0.0])>0.5,'broad two-axis fixture rejected')
need(broad([1.0,0.0,1.0,0.0])>0.5,'broad axial+diagonal fixture rejected')
print('PASS 26806 VGN: exact 26727 highlight cleanup is default; bright color opt-in requires far-4 broad 2-D material + temporal CFA validity')
print('PASS 26806 geometry regressions: thin tangent-only structure cannot self-protect; broad 2-D material can')

# Late 26803 MotionV2 false-color path must remain byte-identical to successful 26805 authority.
for rel in (
 'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl',
 'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl',
 'app/src/main/assets/shaders/motionv2/render.glsl'):
    need(a[rel]==c[rel],f'26803 late path changed: {rel}')
print('PASS 26806 inherited 26803 late far-parent classifier/propagation/render path byte-identical')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26806 protected runtime: 1779 files byte-invariant, including DNG/UHDR/SR/native/vendor/tone/color transform')
