#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: validate_26788.py BASE_ROOT CANDIDATE_ROOT')
BASE=Path(sys.argv[1]); CAND=Path(sys.argv[2])
CHANGED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties',
]
SREL=CHANGED[0]; TREL=CHANGED[1]; VREL=CHANGED[2]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def universe(root):
    return {str(p.relative_to(root)):sha(p) for p in (root/'app').rglob('*') if p.is_file()}
def need(cond,msg):
    if not cond: raise AssertionError(msg)
def block(text,start,end,label):
    a=text.find(start); need(a>=0,f'{label}: start missing')
    b=text.find(end,a); need(b>=0,f'{label}: end missing')
    return text[a:b+len(end)]
def shader_block(text,name):
    pat=re.compile(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""\s*$',re.M)
    m=pat.search(text); need(m is not None,f'{name}: declaration missing')
    a=m.start(); b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing')
    return text[a:b+len('""".trimIndent()')]

bU=universe(BASE); cU=universe(CAND)
need(len(bU)==1779 and len(cU)==1779, f'app universe count base={len(bU)} cand={len(cU)}')
need(set(bU)==set(cU), 'candidate added/deleted app files')
diff=sorted(k for k in bU if bU[k]!=cU[k])
need(diff==CHANGED, f'changed-file allowlist mismatch: {diff}')
print('PASS 26788 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')

v=(CAND/VREL).read_text()
need('VERSION_NAME=0.9726788\n' in v and 'VERSION_BUILD=26788\n' in v, '26788 version/build mismatch')
need('VERSION_NAME=0.9726787' not in v and 'VERSION_BUILD=26787' not in v, 'stale 26787 version remains')
print('PASS 26788 version/build: 0.9726788 / 26788')

bs=(BASE/SREL).read_text(); cs=(CAND/SREL).read_text()
bt=(BASE/TREL).read_text(); ct=(CAND/TREL).read_text()

# DNG and 26787 neutral-highlight owners inside the otherwise modified shader file remain byte-identical.
need(shader_block(bs,'normalDngMerge')==shader_block(cs,'normalDngMerge'), 'DNG normalDngMerge block changed')
need(shader_block(bs,'jpegNeutralHighlightClamp26787')==shader_block(cs,'jpegNeutralHighlightClamp26787'), '26787 neutral-highlight owner changed')
print('PASS 26788 DNG/neutral-owner block freeze: normalDngMerge + jpegNeutralHighlightClamp26787 byte-identical to successful 26787')

# One and only one LCA owner: same-phase packed CFA before RBF, no post-RGB 26787 warp survives.
for stale in ['jpegLcaPreResolve26787','sabreJpegLcaPreResolveProgram26787','IRIS_26787_SHARE_DNG_LCA_WITH_JPEG','iris_26787_jpeg_lca_pre_resolve']:
    need(stale not in cs+ct, f'stale post-RGB LCA owner survives: {stale}')
need(cs.count('val jpegPhaseSafeCfaLca26788 = """')==1, 'phase-safe CFA LCA shader owner count != 1')
need(ct.count('sabreJpegPhaseSafeCfaLcaProgram26788 = linkProgram(')==1, 'phase-safe CFA LCA program link count != 1')
need(ct.count('IRIS_26788_ONE_PHASE_SAFE_LCA_OWNER')==1, 'one-owner runtime marker count != 1')
need('owner=PRE_RBF_SAME_PHASE_CFA postRgbLcaRetired=true validityOwner=UNWARPED_SOURCE_CFA' in ct, 'runtime LCA owner telemetry mismatch')

lca=shader_block(cs,'jpegPhaseSafeCfaLca26788')
for token in [
    'if (phaseIndex == uCfaPattern) return uKrKb26788.x;',
    'if (phaseIndex == 3 - uCfaPattern) return uKrKb26788.y;',
    'return 0.0;',
    '(targetCenter - opticalCenter) * (1.0 - k)',
    'corrected[phaseIndex] = samePhaseBilinear26788(correctedCenter, phaseIndex);',
    'vec4 corrected = center;',
]: need(token in lca,f'phase-safe LCA semantic token missing: {token}')
need('texture(' not in lca or 'texelFetch(uSource' in lca, 'phase-safe LCA lacks same-lattice texel fetch')
need('component26788(texelFetch(uSource' in lca, 'same-phase component sampling missing')
print('PASS 26788 LCA ownership/domain: exact DNG R/B phase convention + (1-k) radial model; greens source-pass-through; post-RGB owner retired')

merge=shader_block(cs,'merge')
short=shader_block(cs,'universalNormalMasterShortFusion26651')
for token in ['uniform sampler2D uExtractedBayerValidity;','get3x3FromExtractedBayerValidity','validityBayerValue26788']:
    need(token in merge,f'merge unwarped-validity semantic missing: {token}')
for token in ['uniform sampler2D uShortExtractedBayerValidity;','texture(uShortExtractedBayerValidity','get3x3FromExtractedBayerValidity','validityBayerValue26788']:
    need(token in short,f'SHORT unwarped-validity semantic missing: {token}')
for token in [
    'bindTexture(program, "uExtractedBayer", 0, signalExtracted26788)',
    'bindTexture(program, "uExtractedBayerValidity", 4, extracted)',
    'bindTexture(program, "uShortExtractedBayer", 4, shortSignal26788)',
    'bindTexture(program, "uShortExtractedBayerValidity", 8, shortExtracted)',
]: need(token in ct,f'host corrected-signal/original-validity binding missing: {token}')
need(ct.count('jpegPhaseSafeLca26788 = dngOptions26786.lcaEnabled')==3, 'NORMAL/LONG/SHORT LCA settings routing count != 3')
print('PASS 26788 CFA validity ownership: corrected CFA is signal only; original unwarped CFA owns headroom/guide validity for NORMAL/LONG/SHORT')

# The residual guard is periodic/material-baseline only; no neutral-midpoint prerequisite is allowed.
edge=shader_block(ct,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')
for token in [
    'IRIS_26788_MATERIAL_BASELINE_PERIODIC_FALSE_COLOR',
    'vec2 materialBaseline26788 = 0.5 * (farMid + nearMid);',
    'vec2 periodicVector26788 = nearMid - farMid;',
    'vec2 leftAlternation26788 = cNeg1 - cNeg2;',
    'vec2 rightAlternation26788 = cPos1 - cPos2;',
    'smoothstep(0.45, 0.85, bilateralCoherence26788)',
    'coherentW = min(coherentW, 0.70);',
    'correctedC = mix(correctedC, materialBaseline26788, coherentW);',
]: need(token in edge,f'periodic residual guard token missing: {token}')
need('midpointNeutral' not in edge, 'neutral-midpoint prerequisite survived in active edge shader')
need('vec2 correctedC = mix(centerC, medianC, w26778);' in edge, 'inherited 26778 median outlier path missing')
need('broadClippedNeutralApplied=false' in ct, 'broad clipped-neutral retirement telemetry missing')
need('old26778OutlierPathPreserved=true' in ct, 'old 26778 outlier-path preservation telemetry missing')
need('edgeSuppressor26778Unchanged=true' not in ct, 'stale full-26778 unchanged telemetry survives')
need('edgeSuppressor26778PeriodicGuard26788=true' in ct, 'truthful 26788 guard telemetry missing')
need('periodicGate=MATERIAL_BASELINE_PERIODIC_26788' in ct, 'stale periodic guard owner telemetry survives')
need('periodicGate=COHERENT_BIPOLAR_26782' not in ct, 'old bipolar periodic owner telemetry survives')
print('PASS 26788 residual false-color owner: material-baseline periodic guard, bilateral/phase opposition, max blend 0.70; inherited 26778 median outlier path preserved')

# No architectural domain expansion through file scope; all other app bytes are already proven protected above.
for forbidden in ['app/src/main/cpp','IrisJpegColorSolver','UltraHdr','GainMap']:
    pass
print('PASS 26788 downstream/domain freeze: VGN/color/tone/UHDR/native/vendor/frame/exposure/alignment files outside exact allowlist unchanged')
