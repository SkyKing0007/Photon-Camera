#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: validate_26815.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
SAB='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
VER='app/version.properties'; MOD={SAB,VGN,VER}
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
DNG={
'app/src/main/cpp/dngCreator.h','app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java'}
SAB_26813_SHA='b6e81869e3ceb29dd02f6d83772be41bfc53031ea1158344694ca5704a825812'
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
def template(text,name):
    m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,f'{name}: declaration missing')
    b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing'); return text[m.end():b]
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
changed={p for p in a if a[p]!=c[p]}; need(changed==MOD,f'modified allowlist mismatch {sorted(changed)}')
print('PASS 26815 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726815' in v and 'VERSION_BUILD=26815' in v,'version')
print('PASS 26815 version 0.9726815 / 26815')
# Failed 26814 Sabre experiment must be gone exactly, not approximately.
need(sha(CAND/SAB)==SAB_26813_SHA,f'Sabre is not exact successful 26813 bytes: {sha(CAND/SAB)}')
sab=(CAND/SAB).read_text()
need('IRIS_26814_UNIFIED_RGB_SHARED_CONFIDENCE_OWNER' not in sab,'failed 26814 shared-confidence owner survived')
need('accumulatedIntensities = correctedRgb26793 * accumulatedWeights;' in template(sab,'merge'),'successful 26813 Sabre accumulation contract not restored')
print('PASS 26815 failed 26814 experiment rollback: Sabre byte-identical to successful 26813')
# Protect all unrelated owners.
for rel in (STACK,BRIDGE,GALLERY): need(sha(BASE/rel)==sha(CAND/rel),f'protected owner changed: {rel}')
for rel in DNG: need(sha(BASE/rel)==sha(CAND/rel),f'DNG protected bytes changed: {rel}')
need('IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER' in (CAND/BRIDGE).read_text(),'26813 no-raise owner missing')
need('IRIS_26812_GALLERY_THUMB_CLICK_ENTRY' not in (CAND/GALLERY).read_text(),'gallery logger unexpectedly restored')
print('PASS 26815 26813 no-raise + quiet exact-item gallery preserved')
# VGN change must be the exact audited independent-neighbor proof only.
base=(BASE/VGN).read_text(); cand=(CAND/VGN).read_text()
insert1='''            /* IRIS_26815_INDEPENDENT_NEIGHBOR_CHROMA_RESTORE_PROOF\n             * Keep a second physically-valid same-surface consensus that explicitly excludes the\n             * center pixel. The 26728 magnitude owner may consult this as independent evidence,\n             * but the center's own pre-VGN chroma can no longer vote to restore itself. */\n            vec3 independentValidNeighborChromaSum = vec3(0.0);\n            float independentValidNeighborWeight = 0.0;\n'''
insert2='''                        independentValidNeighborChromaSum +=\n                            neighborNormalizedChroma * validSameSurfaceWeight;\n                        independentValidNeighborWeight += validSameSurfaceWeight;\n'''
insert3='''            vec3 independentValidNeighborConsensus = independentValidNeighborWeight > 1.0e-6\n                ? independentValidNeighborChromaSum / independentValidNeighborWeight : vec3(0.0);\n            float independentValidNeighborSupport = uSabreSupportValid != 0\n                ? clamp(independentValidNeighborWeight / 2.50, 0.0, 1.0) : 0.0;\n'''
insert4='''                /* IRIS_26815_INDEPENDENT_NEIGHBOR_CHROMA_RESTORE_PROOF\n                 * 26814 device evidence falsified support equalization and the audit then proved\n                 * that admitted 26728 pixels retained about 99.6% of pre-VGN chroma magnitude.\n                 * Require physically-valid same-surface neighbors, excluding the center itself, to\n                 * independently support both the cleaned hue direction and a substantial fraction\n                 * of the requested pre-VGN magnitude. This does not target green/cyan or any hue,\n                 * never changes luma, and never creates a new chroma vector. */\n                vec3 cleanedNormalizedChroma = correctedChroma / centerScale;\n                float independentNeighborMagnitude =\n                    length(independentValidNeighborConsensus) * centerScale;\n                float independentNeighborDirection = hueAgreement(\n                    independentValidNeighborConsensus, cleanedNormalizedChroma);\n                float independentNeighborDirectionProof = smoothstep(0.80, 0.94,\n                    independentNeighborDirection);\n                float independentNeighborMagnitudeProof = smoothstep(0.45, 0.80,\n                    independentNeighborMagnitude / max(preVgnMagnitude, 1.0e-6));\n                float independentNeighborSupportProof = smoothstep(0.35, 0.80,\n                    independentValidNeighborSupport);\n                float independentNeighborRestoreProof = min(independentNeighborDirectionProof,\n                    min(independentNeighborMagnitudeProof, independentNeighborSupportProof));\n'''
oldperm='''                float restorePermission = strictPhysicalProof * cleanedDirectionPresent *\n                    preVgnChromaPresent * artifactPermission * highlightCleanupPermission26807;\n'''
newperm='''                float restorePermission = strictPhysicalProof * independentNeighborRestoreProof *\n                    cleanedDirectionPresent * preVgnChromaPresent * artifactPermission *\n                    highlightCleanupPermission26807;\n'''
for block in (insert1,insert2,insert3,insert4): need(cand.count(block)==1,'26815 VGN audited block missing/duplicate')
need(cand.count(newperm)==1,'26815 restorePermission owner missing/duplicate')
reverted=cand
for block in (insert1,insert2,insert3,insert4): reverted=reverted.replace(block,'',1)
reverted=reverted.replace(newperm,oldperm,1)
need(reverted==base,'VGN changed outside exact 26815 independent-neighbor restoration proof')
uv=template(cand,'universalAdaptiveColor26561')
need('IRIS_26815_INDEPENDENT_NEIGHBOR_CHROMA_RESTORE_PROOF' in uv,'26815 VGN owner not in active shader')
need('independentValidNeighborChromaSum = vec3(0.0)' in uv,'independent neighbor accumulator missing')
need('independentValidNeighborChromaSum +=' in uv,'neighbor evidence not accumulated')
need('centerNormalizedChroma * centerValidConsensusWeight' in uv,'inherited ordinary consensus changed unexpectedly')
need('strictPhysicalProof * independentNeighborRestoreProof' in uv,'26728 restoration not subordinated to independent proof')
need('correctedChroma *= restoredMagnitude / cleanedMagnitude;' in uv,'26728 cleaned hue-direction ownership changed')
print('PASS 26815 VGN semantic owner: center-excluded physically-valid neighbor evidence gates only 26728 magnitude restoration')
print('PASS 26815 chroma contract: no hue targeting, no new chroma vector, no luma modification, 26728 cleaned direction preserved')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26815 protected runtime: 1779 files byte-invariant')
