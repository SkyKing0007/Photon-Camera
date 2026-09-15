#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26645_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(root,r): return (root/r).read_text()
def sha(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
allow={
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/version.properties'}
a,b=H(base),H(cand); assert len(a)==len(b)==1720
changed={r for r in a if a[r]!=b[r]}; assert changed==allow,(changed,allow)
ver=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726645' in ver and 'VERSION_BUILD=26645' in ver
# SHORT: preserve physical -2.5EV/capture policy and old loss owner, add a separate visual high-radiance authority.
k0=txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); k=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for token in ['smoothstep(0.72, 0.92, predicted)','smoothstep(0.05, 0.12, relativeLoss)','smoothstep(0.94, 0.98, reference)','smoothstep(0.12, 0.22, relativeLoss)']:
 assert k.count(token)==k0.count(token) and k.count(token)>=2,token
for m in ['IRIS_26644_SHORT_SOURCE_SUPPORT_FAIL_CLOSED','IRIS_26644_SHORT_WARP_DOMAIN_FAIL_CLOSED','IRIS_26644_SHORT_EXTRACTED_BILINEAR_FAIL_CLOSED','IRIS_26645_VISUAL_HIGH_RADIANCE_COMPONENT_EVIDENCE','IRIS_26645_VISUAL_HIGH_RADIANCE_COMPONENT_OWNER','IRIS_26645_VISUAL_STRUCTURE_GEOMETRY_SEED','IRIS_26645_PER_PIXEL_VISUAL_RADIANCE_PROOF','IRIS_26645_VISUAL_HIGH_RADIANCE_WEIGHT_OWNER']:
 assert k.count(m)==1,m
assert 'visualStructureComponentConfidence' in k and 'visualRadianceEvidence(referenceUv, warpedUv)' in k
assert 'visualRescueWeight = censoredCoreWeight * clamp(visualHighRadiance, 0.0, 1.0);' in k
assert 'max(max(literalFinalWeight, effectiveRescueWeight), visualRescueWeight)' in k
assert 'patternProof = smoothstep(0.70, 0.92, corr);' in k
assert 'flattenedNormal' not in k[k.index('val shortComponentAnchor26607 = """'):k.index('""".trimIndent()',k.index('val shortComponentAnchor26607 = """'))]
assert 'max(correlation, flattenedNormal)' not in k
# Tone: texture-sensitive structured fields reduce shoulder lift and reserve ceiling headroom for residual detail.
g=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
for m in ['IRIS_26645_VISUAL_TEXTURE_ENERGY_OWNER','IRIS_26645_STRUCTURE_AWARE_HIGHLIGHT_BASE','IRIS_26645_STRUCTURAL_HEADROOM_RESERVATION']:
 assert g.count(m)==1,m
assert 'structureShoulderScale=1.0-0.72*sourceStructureGate;' in g
assert 'positiveOvershoot=max(candidateLinear-0.997,0.0);' in g
assert 'protectedBase=max(shadowBase-sourceStructureGate*positiveOvershoot' in g
# HEIC: successful 26644 full-range transport/native container remain; exact saved HEIC must platform-decode as matching P3 Ultra HDR.
h=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
assert h.count('IRIS_26645_ANDROID_HEIC_ULTRAHDR_READBACK_CONTRACT')==1
for token in ['BitmapFactory.decodeFile','decoded.hasGainmap()','ColorSpace.Named.DISPLAY_P3','expected.getRatioMin()','actual.getRatioMin()','expected.getRatioMax()','actual.getRatioMax()','expected.getGamma()','actual.getGamma()','expected.getEpsilonSdr()','actual.getEpsilonSdr()','expected.getEpsilonHdr()','actual.getEpsilonHdr()','expected.getMinDisplayRatioForHdrTransition()','actual.getMinDisplayRatioForHdrTransition()','expected.getDisplayRatioForFullHdr()','actual.getDisplayRatioForFullHdr()','expectedContents.getWidth() == actualContents.getWidth()','if (!ok) Files.deleteIfExists(output);']:
 assert token in h,token
hw='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java'
assert sha(base,hw)==sha(cand,hw)
hwt=txt(cand,hw); assert 'MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL' in hwt and 'outRange != MediaFormat.COLOR_RANGE_FULL' in hwt
native='app/src/main/cpp/iris_heic_jni.cpp'; assert sha(base,native)==sha(cand,native)
# UI: app-side only, circularbarlib remains outside candidate authority and untouched.
u=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
assert u.count('IRIS_26645_MANUAL_KNOB_HALF_CIRCLE_REMOVED')==1
for token in ['getDeclaredField("m_BackgroundPaint")','android.graphics.Color.TRANSPARENT','knob.invalidate()']:
 assert token in u,token
# Capture/gain-map/native owners outside allowlist remain byte-identical by complete allowlist equality.
print('PASS 26645 semantics: correlated high-radiance SHORT authority + structured-highlight headroom + fail-closed Android HEIC Ultra-HDR readback + manual half-circle removal; -2.5EV/native/gain-map/26644 range owners retained')
