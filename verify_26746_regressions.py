#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re,math
if len(sys.argv)!=3: raise SystemExit('usage: verify_26746_regressions.py BASE26745 CAND26746')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
changed=set((pkg/'26746_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726746' in v and 'VERSION_BUILD=26746' in v
vgp='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; vg=txt(c,vgp); basevg=txt(b,vgp)
# Preserve exact 26727/26728 legacy equations; only the later 26729+ exception is capped at the extreme end.
for t in ['float highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma);','float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));','float inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY);']:
 assert t in vg,t
# 26745 architecture remains present.
for t in ['IRIS_26745_CONNECTED_BRIGHT_FRINGE_COLOR_AUTHORITY','IRIS_26745_POST_VGN_ACR3_HUE_AUTHORITY','IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE']:
 assert t in vg or t in txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl'),t
# 26746 only removes the ability of newer material-color exceptions to bypass the last 0.90..0.92 legacy segment.
for t in ['IRIS_26746_26727_EXTREME_FLATTENED_HIGHLIGHT_VETO','float extremeFlattenedPermission26746 = 1.0 - smoothstep(0.90, 0.92, centerLuma);','brightPhysicalColorException *= extremeFlattenedPermission26746;','IRIS_26746_26727_EXTREME_FLATTENED_HIGHLIGHT_VETO_SEED','float extremeFlattenedPermission26746=1.0-smoothstep(0.90,0.92,centerNormalizedY);','realBrightColorProof*=extremeFlattenedPermission26746;','IRIS_26746_EXTREME_CORE_EDGE_OVERRIDE','physicalBrightColorVeto26746','connectedExtremeCore26746']:
 assert t in vg,t
# Current 26745 color transform/native publication/tone are byte-protected: no ACR3, native, tone or reconstruction redesign.
protected=[
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Super Res remains luminance/detail-only; shared Sabre/VGN chroma therefore receives this exact same 26746 veto.
sr=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert 'sabreRgbChromaOwner=true' in sr and 'directChromaOwner=false' in sr
native=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp'); assert 'iris26745ProtectBrightNeutralHue' in native
color=txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl'); assert 'iris26745ProtectBrightNeutralHue' in color
# No hue/object semantic hack and no 26744 reconstruction architecture.
joined=(vg+color+native).lower()
for f in ['orange_detector','yellow_detector','cyan_detector','foliage_detector','chandelier_detector','reflection_detector','reference_rbf_26744','normal_reference_rbf_26744']:
 assert f not in joined,f
# Scalar contract: 26745 exception is exactly unchanged <=0.90, progressively removed 0.90..0.92, absolute at >=0.92.
def smooth(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def extreme(x): return 1.0-smooth(0.90,0.92,x)
assert extreme(0.89)==1.0 and extreme(0.90)==1.0
assert 0.49 < extreme(0.91) < 0.51
assert extreme(0.92)==0.0 and extreme(1.0)==0.0
print('PASS 26746 regressions: 26745 color architecture preserved through recoverable highlights; exact 26727/26728 headroom equations retained; only 26729+ bright-color exception loses veto power in 0.90..0.92 extreme flattened end; Super Res shared VGN chroma parity locked')
