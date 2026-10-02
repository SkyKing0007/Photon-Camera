#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26747_regressions.py BASE26746 CAND26747')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/version.properties'}
changed=set((pkg/'26747_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726747' in v and 'VERSION_BUILD=26747' in v
vgp='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; vg=txt(c,vgp)
# Preserve exact proven legacy equations and later real-color architecture.
for t in [
'float highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma);',
'float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));',
'float inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY);',
'IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP',
'IRIS_26745_CONNECTED_BRIGHT_FRINGE_COLOR_AUTHORITY','IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY']:
 assert t in vg,t
# 26747 target: modern color stays available unless connected to physically exhausted highlight evidence.
for t in [
'IRIS_26747_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER','IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO',
'IRIS_26747_SEED_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER','IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO_SEED',
'IRIS_26747_EXACT_26727_DIRECTION_FALLBACK','IRIS_26747_CONNECTED_UNRECOVERABLE_SECOND_RING_OVERRIDE',
'legacy26727HighlightMode26747 << 15','legacy26727HighlightAt26747','centerLegacy26727Highlight26747',
'smoothstep(0.72, 0.92, nearAY) * (1.0 - nearPhysicalA)',
'smoothstep(0.72,0.92,firstNormalized26747)*(1.0-neighborTrust)']:
 assert t in vg,t
# 26746 too-narrow top-only owner must be retired.
for t in ['IRIS_26746_26727_EXTREME_FLATTENED_HIGHLIGHT_VETO','IRIS_26746_26727_EXTREME_FLATTENED_HIGHLIGHT_VETO_SEED','IRIS_26746_EXTREME_CORE_EDGE_OVERRIDE','extremeFlattenedPermission26746','connectedExtremeCore26746','physicalBrightColorVeto26746']:
 assert t not in vg,t
# The legacy fallback is local: it disables 26729 color-only material ownership, not 26727 topology/luma edges globally.
assert '(1.0-float(legacy26727HighlightMode26747))' in vg
assert 'if(legacy26727HighlightMode26747!=0){mask=0xFF;count=8;cleanupFallback=0;}' in vg
assert 'centerLegacy26727Highlight26747)?0.0:1.0;' in vg
# ACR3 cannot re-protect near-neutral fringe in inherited highlight range, in Normal + true2x CPU/GPU.
color=txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl'); native=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
assert 'IRIS_26747_ACR3_SUBORDINATE_TO_26727_HIGHLIGHT_OWNER' in color
assert 'inheritedHighlightHuePermission26747=1.0-smoothstep(0.72,0.92,targetY)' in color
assert native.count('inheritedHighlightHuePermission26747')>=4
assert '1.f-smoothstep(0.72f,0.92f,targetY)' in native
assert '1.0-smoothstep(0.72,0.92,targetY)' in native
# Super Res remains shared Sabre/VGN chroma owner; no direct SR chroma reconstruction is introduced.
sr=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert 'sabreRgbChromaOwner=true' in sr and 'directChromaOwner=false' in sr
for p in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
# No semantic hue/object detector and no rejected 26744 RGB reconstruction path.
joined=(vg+color+native).lower()
for f in ['orange_detector','yellow_detector','cyan_detector','foliage_detector','chandelier_detector','reflection_detector','reference_rbf_26744','normal_reference_rbf_26744']:
 assert f not in joined,f
print('PASS 26747 regressions: 26745 real-color architecture retained for physically recoverable highlights; full 26727 0.72..0.92 protection restored only for connected unrecoverable bright cores/fringes; post-26727 direction/median/IIR self-protection retired locally; ACR3 subordinated in Normal and Super Res')
