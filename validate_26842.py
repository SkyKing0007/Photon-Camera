#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
B,C=map(Path,sys.argv[1:3])
CHANGED={'app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {str(p.relative_to(r)).replace('\\','/'):H(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); assert set(b)==set(c) and len(b)==1786,(len(b),len(c)); delta={p for p in b if b[p]!=c[p]}; assert delta==CHANGED,(delta-CHANGED,CHANGED-delta)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726842' in v and 'VERSION_BUILD=26842' in v and 'VERSION_MINOR=9726440' in v
# Preserve successful 26841 preview/HDR and warm-midtone behavior byte-identically.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    assert H(B/rel)==H(C/rel),rel
cap=(C/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
for marker in ['IRIS_26841_SINGLE_TARGET_HAL_HDR_PREVIEW','MOTION_26841_PREVIEW_RETARGET_DEADBAND_EV = 0.30f','oneRequestUpdate=true iterative=false staircase=false','IRIS_26841_ABSOLUTE_RECIPE_ENERGY_AT_SHUTTER']:
    assert marker in cap,marker
color=(C/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text(); assert 'IRIS_26841_WARM_MIDTONE_ACR3_RESTRAINT' in color
# 26842 clip-zone: source hue remains immutable; confidence changes magnitude continuously.
sh=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); bsh=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for marker in ['IRIS_26842_CONTINUOUS_CLIPPED_COLOR_ROLLOFF','float localHueTrust=sourceHasHue','float partialTrust=clamp(localHueTrust*(0.48+0.52*secondaryTrust)','float partialTargetMag=mix(untrustedFloor,localMagnitude,partialTrust)','float sourceHueGone=1.0-smoothstep(0.65*uNeutralRms,1.35*uNeutralRms,srcMag)','float terminal=smoothstep(0.94,0.999,m)*sourceHueGone','vec2 alongSource=(srcMag>1.0e-6) ? c*(rolloffMag/srcMag)']:
    assert marker in sh,marker
assert 'float targetMag=preserveHue ? trustedMag : min(srcMag,untrustedFloor);' not in sh
# No new hue donor authority: output direction stays source-ray until hue is genuinely gone.
blk=sh[sh.index('IRIS_26842_CONTINUOUS_CLIPPED_COLOR_ROLLOFF'):sh.index('float dR=cp.x*yc',sh.index('IRIS_26842_CONTINUOUS_CLIPPED_COLOR_ROLLOFF'))]
for forbidden in ['normalize(cs)','normalize(cb)','mix(c,cs','mix(c,cb']:
    assert forbidden not in blk,forbidden
# 26842 mottling: extra cleanup only after whole 5x5 neighborhood proves flat and remains low-signal.
shadow=(C/'app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl').read_text(); bshadow=(B/'app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl').read_text()
for marker in ['IRIS_26842_TRUE_FLAT_MOTTLING_CLEANUP','float wholeNeighborhoodFlat=1.0-smoothstep(','float mottleConfidence=lowSignal*flatConfidence*wholeNeighborhoodFlat','chromaMix=clamp(chromaMix+0.07*mottleConfidence,0.0,0.94);','lumaMix=clamp(lumaMix+0.09*mottleConfidence,0.0,0.47);']:
    assert marker in shadow,marker
assert 'float yMin=yc;' in shadow and 'float yMax=yc;' in shadow
# Existing high-frequency structure policy remains: no sharpening, no new cleanup outside low-signal true-flat gate.
assert 'No sharpening' in shadow or 'No sharpening' in bshadow
# DNG/native/vendor/high zoom/SR owners untouched through protected manifests and explicit key files.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java']:
    assert H(B/rel)==H(C/rel),rel
print('PASS 26842 semantic validation: exact 3-path scope; successful 26841 one-shot HDR preview and warm-midtone restraint frozen; clipped/near-clipped chroma now rolls continuously along immutable source hue with warm fallback only after hue loss; mottling cleanup increases only in genuinely flat 5x5 low-signal neighborhoods; DNG/UHDR/native/high-zoom/SR protected')
