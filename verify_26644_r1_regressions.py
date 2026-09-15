#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26644_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def t(r): return (cand/r).read_text()
def sh(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
# Exact historical failures now permanent.
k=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
seg=k[k.index('val shortRescueWeight26607 = """'):k.index('""".trimIndent()',k.index('val shortRescueWeight26607 = """'))]
if 'mirrorUvs(referenceUv + flow.xy)' in seg: raise SystemExit('REGRESSION: mirrored SHORT rescue border returned')
if 'texelFetch(uShortExtractedBayer, clampExtracted' in seg: raise SystemExit('REGRESSION: clamped SHORT bilinear border returned')
if 'if (!shortSupportValid)' not in seg or 'oWeight = 0.0;' not in seg: raise SystemExit('REGRESSION: invalid SHORT support does not fail closed')
g=t('app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
if 'float smallResidualWeight=mix(1.0,0.78,upperGate);' not in g: raise SystemExit('REGRESSION: proven smooth-field 26635 suppression removed')
if 'sourceStructureGate' not in g: raise SystemExit('REGRESSION: source-proven bright structure preservation absent')
h=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
if 'MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL' not in h: raise SystemExit('REGRESSION: full-range hardware HEVC request absent')
if 'outRange != MediaFormat.COLOR_RANGE_FULL' not in h: raise SystemExit('REGRESSION: hardware HEVC range mismatch not rejected')
# All 26643 native HEIF/ISO21496/libheif-patch owners remain byte-identical.
for r in ['app/src/main/cpp/iris_heic_jni.cpp','app/src/main/cpp/CMakeLists.txt','app/src/main/cpp/iris26643_libheif_aosp_contract.patch']:
 if sh(base,r)!=sh(cand,r): raise SystemExit('REGRESSION: protected 26643 HEIC native owner changed: '+r)
# No adaptive-EV/capture rewrite in this build: only the six declared runtime paths may differ.
A={str(p.relative_to(base)):sh(base,str(p.relative_to(base))) for p in (base/'app').rglob('*') if p.is_file()}
B={str(p.relative_to(cand)):sh(cand,str(p.relative_to(cand))) for p in (cand/'app').rglob('*') if p.is_file()}
changed={r for r in A if A[r]!=B[r]}
expected={x for x in (Path(__file__).parent/'R1_26644_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x}
if changed!=expected: raise SystemExit(f'REGRESSION: runtime scope mismatch {changed^expected}')
print('PASS 26644 permanent regressions: no mirrored/clamped SHORT borders; 26635 smooth-field behavior retained with source-structure escape; HEVC full-range mismatch fails; 26643 native HEIC/ISO21496/libheif owners and capture/EV policy protected')
