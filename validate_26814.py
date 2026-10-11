#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: validate_26814.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
VER='app/version.properties'; MOD={SHADERS,VER}
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
DNG={
'app/src/main/cpp/dngCreator.h','app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java'}
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
print('PASS 26814 authority-seeded scope: 1782 -> 1782, exactly 2 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726814' in v and 'VERSION_BUILD=26814' in v,'version')
print('PASS 26814 version 0.9726814 / 26814')
for rel in (STACK,BRIDGE,GALLERY,VGN): need(sha(BASE/rel)==sha(CAND/rel),f'protected owner changed: {rel}')
for rel in DNG: need(sha(BASE/rel)==sha(CAND/rel),f'DNG protected bytes changed: {rel}')
need('IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER' in (CAND/BRIDGE).read_text(),'26813 no-raise owner missing')
need('IRIS_26812_GALLERY_THUMB_CLICK_ENTRY' not in (CAND/GALLERY).read_text(),'gallery logger unexpectedly restored')
print('PASS 26814 26813 baseline frozen: stacker/bridge/gallery/VGN/DNG byte-identical; no-raise and quiet gallery preserved')
base_text=(BASE/SHADERS).read_text(); cand_text=(CAND/SHADERS).read_text()
old='''            accumulatedIntensities = correctedRgb26793 * accumulatedWeights;\n            validAccumulatedWeights = vec3(\n                validReorderedWeights.r,\n                validReorderedWeights.g + validReorderedWeights.b,\n                validReorderedWeights.a\n            );\n'''
new='''            /* IRIS_26814_UNIFIED_RGB_SHARED_CONFIDENCE_OWNER\n             * correctedRgb26793 is one same-location RGB observation. Keep the existing CFA/RBF\n             * topology and per-channel means above unchanged, but do not split that unified RGB\n             * back into three independent homogeneous accumulation confidences. Normalize the\n             * legacy R/G/B supports by the number of CFA samples in each phase topology, then use\n             * the weakest normalized support as one conservative RGB confidence. Multiplying by\n             * three retains the legacy average nine-sample support scale without changing hue.\n             * Physical/headroom validity remains a sidecar ratio per color; it cannot rotate RGB. */\n            vec4 topologyCounts26814 = swizzleForType(vec4(4.0, 2.0, 2.0, 1.0), type);\n            vec3 rgbTopologyCounts26814 = vec3(\n                topologyCounts26814.r,\n                topologyCounts26814.g + topologyCounts26814.b,\n                topologyCounts26814.a\n            );\n            vec3 legacyAccumulatedWeights26814 = accumulatedWeights;\n            vec3 normalizedSupport26814 = legacyAccumulatedWeights26814 /\n                max(rgbTopologyCounts26814, vec3(1.0));\n            float sharedNormalizedSupport26814 = min(\n                normalizedSupport26814.r,\n                min(normalizedSupport26814.g, normalizedSupport26814.b));\n            float sharedAccumulationWeight26814 = 3.0 * max(sharedNormalizedSupport26814, 0.0);\n            vec3 legacyValidAccumulatedWeights26814 = vec3(\n                validReorderedWeights.r,\n                validReorderedWeights.g + validReorderedWeights.b,\n                validReorderedWeights.a\n            );\n            vec3 physicalValidityRatio26814 = clamp(\n                legacyValidAccumulatedWeights26814 /\n                    max(legacyAccumulatedWeights26814, vec3(1.0e-7)),\n                vec3(0.0), vec3(1.0));\n            accumulatedWeights = vec3(sharedAccumulationWeight26814);\n            accumulatedIntensities = correctedRgb26793 * sharedAccumulationWeight26814;\n            validAccumulatedWeights = accumulatedWeights * physicalValidityRatio26814;\n'''
need(base_text.count(old)==1,'26813 ordinary merge anchor count')
need(cand_text.count(new)==1,'26814 shared-confidence owner count')
need(cand_text.replace(new,old,1)==base_text,'Sabre shader changed outside exact 26814 owner')
merge=template(cand_text,'merge')
need('IRIS_26814_UNIFIED_RGB_SHARED_CONFIDENCE_OWNER' in merge,'26814 owner not in merge')
need('accumulatedIntensities = correctedRgb26793 * accumulatedWeights;' not in merge,'ordinary merge still independently weights unified RGB')
need('accumulatedWeights = vec3(sharedAccumulationWeight26814);' in merge,'shared RGB denominator missing')
need('accumulatedIntensities = correctedRgb26793 * sharedAccumulationWeight26814;' in merge,'shared RGB numerator missing')
need('validAccumulatedWeights = accumulatedWeights * physicalValidityRatio26814;' in merge,'physical validity sidecar missing')
need('accumulatedWeights = vec3(\n                reorderedWeights.r,\n                reorderedWeights.g + reorderedWeights.b,\n                reorderedWeights.a\n            );' in merge,'upstream CFA/RBF per-channel reconstruction weights were altered')
need('sameLocationChroma26793(' in merge and 'vec3 correctedRgb26793' in merge,'26793 same-location RGB owner missing')
print('PASS 26814 semantic owner: CFA/RBF reconstruction remains per-channel upstream; unified correctedRgb26793 uses one topology-normalized shared accumulation confidence downstream')
print('PASS 26814 validity contract: per-channel physical/headroom validity remains sidecar-only and cannot rotate RGB')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26814 protected runtime: 1780 files byte-invariant')
