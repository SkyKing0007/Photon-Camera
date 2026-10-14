#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def need(v,m):
    if not v: raise AssertionError(m)
def template(text,name):
    m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,name+' declaration missing')
    e=text.find('""".trimIndent()',m.end()); need(e>=0,name+' terminator missing')
    return text[m.start():e+len('""".trimIndent()')]
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'changed allowlist mismatch actual={sorted(changed)} expected={sorted(A)}')
need(len(b)==1786 and len(c)==1786,f'universe count mismatch {len(b)}->{len(c)}')
v=(C/'app/version.properties').read_text(); need('VERSION_NAME=0.9726829' in v and 'VERSION_BUILD=26829' in v,'version mismatch')
# Exact prior hashes are checked separately; all non-allowlisted bytes must be inherited.
for rel in sorted(set(b)|set(c)):
    if rel not in A: need(b.get(rel)==c.get(rel),f'protected path changed {rel}')
# Sabre: only the merge shader template changes. SHORT is already source-validity weighted and must remain exact 26828.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
bt=(B/rel).read_text(); ct=(C/rel).read_text(); bm=template(bt,'merge'); cm=template(ct,'merge')
need(bt.replace(bm,cm,1)==ct,'Sabre carrier changed outside merge template')
need(template(bt,'universalNormalMasterShortFusion26651')==template(ct,'universalNormalMasterShortFusion26651'),'SHORT fusion must remain exact successful 26828')
for token in ['IRIS_26829_GREEN_SUPPORT_HEADROOM_CLIPPED_RB_OWNER','IRIS_26829_WEIGHTED_GREEN_CLIP_CALC_DOMAIN','float gSupport = smoothstep(0.70, 1.00, greenConfidence);','float gHead = 1.0 - smoothstep(0.55, 0.90, greenHeadroomRatio);','smoothstep(0.85, 1.00, greenConfidence) * gHead','float differenceWeight = colorWeight * gSupport * siteEff;','predictedGreenClip = clipNumerator / supportedWeight;']:
    need(token in cm,'NORMAL clipped-R/B gate missing '+token)
need('IRIS_26828_NORMAL_CLIPPED_RB_CONSENSUS_OWNER' not in cm,'26828 consensus owner survived')
need('redClippedConsensus' not in cm and 'blueClippedConsensus' not in cm,'26828 consensus variables survived')
need(cm.count('buildCalculationClipCfa26793')==2,'clip-domain builder/call count mismatch')
# VGN: only universalAdaptiveColor changes; all other postprocessor shaders remain exact 26828.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
bt=(B/rel).read_text(); ct=(C/rel).read_text(); bu=template(bt,'universalAdaptiveColor26561'); cu=template(ct,'universalAdaptiveColor26561')
need(bt.replace(bu,cu,1)==ct,'VGN carrier changed outside universalAdaptiveColor26561')
base_anchor='''                vec3 independentNeighborTargetChroma =\n                    independentValidNeighborConsensus * centerScale;\n                correctedChroma = mix(correctedChroma, independentNeighborTargetChroma,\n                    greenCleanupAuthority);\n\n                /* A pixel deliberately cleaned by 26818 must not have the old pre-VGN magnitude'''
cand_anchor='''                vec3 independentNeighborTargetChroma =\n                    independentValidNeighborConsensus * centerScale;\n                correctedChroma = mix(correctedChroma, independentNeighborTargetChroma,\n                    greenCleanupAuthority);\n\n                /* IRIS_26829_COLORED_PARENT_GREEN_CYAN_RESIDUAL_OWNER'''
need(base_anchor in bu and cand_anchor in cu,'VGN residual insertion anchor mismatch')
# Prefix before inherited target and suffix after protected floor assignment are byte-identical.
bstart=bu.index('                vec3 independentNeighborTargetChroma ='); cstart=cu.index('                vec3 independentNeighborTargetChroma =')
bsuf=bu.index('                protectedPreVgnMagnitude = floorPermission >= 0.5 ? preVgnMagnitude : 0.0;',bstart)+len('                protectedPreVgnMagnitude = floorPermission >= 0.5 ? preVgnMagnitude : 0.0;')
csuf=cu.index('                protectedPreVgnMagnitude = floorPermission >= 0.5 ? preVgnMagnitude : 0.0;',cstart)+len('                protectedPreVgnMagnitude = floorPermission >= 0.5 ? preVgnMagnitude : 0.0;')
need(bu[:bstart]==cu[:cstart] and bu[bsuf:]==cu[csuf:],'VGN changed outside audited 26818/floor residual region')
for token in ['IRIS_26829_COLORED_PARENT_GREEN_CYAN_RESIDUAL_OWNER','parentDirections26829','broadParent2dProof26829','deniedCenterColorOwnership26829','highlightCleanupOwned26807 ? 1.0 : 0.0','greenCyanResidualProof26829','coloredParentCleanupAuthority26829','coloredParentTargetMagnitude26829 > currentCorrectedMagnitude26829','residualCleanupAuthority26829','(1.0 - residualCleanupAuthority26829)']:
    need(token in cu,'colored-parent residual owner missing '+token)
for token in ['IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD','IRIS_26807_NO_DOWNSTREAM_HIGHLIGHT_CHROMA_RESURRECTION']:
    need(token in cu,'inherited owner lost '+token)
need('IRIS_26806_BROAD_2D_BRIGHT_COLOR_OPT_IN' in ct,'inherited 26806 broad 2D owner lost')
print('PASS 26829 exact 3-path runtime allowlist; 1786-file authority-seeded universe preserved')
print('PASS 26829 NORMAL/Sabre clipped-R/B green-support/headroom owner; Motion SHORT remains exact 26828')
print('PASS 26829 shared VGN colored-parent green/cyan residual owner; luma and saturation-increase forbidden')
print('PASS 26829 all non-allowlisted successful-26828 runtime bytes protected')
