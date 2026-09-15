#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26645_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(r,p): return (r/p).read_text()
def sha(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
k=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
# Permanent 26644 border regression remains exact.
for token in ['IRIS_26644_SHORT_SOURCE_SUPPORT_FAIL_CLOSED','IRIS_26644_SHORT_WARP_DOMAIN_FAIL_CLOSED','IRIS_26644_SHORT_EXTRACTED_BILINEAR_FAIL_CLOSED','if (!shortSupportValid)']:
 assert token in k,token
# 26645: visual owner cannot self-seed from uncorrelated SHORT noise and cannot use old loss gate as its amplitude.
assert 'patternProof = smoothstep(0.70, 0.92, corr);' in k
anchor=k[k.index('val shortComponentAnchor26607 = """'):k.index('""".trimIndent()',k.index('val shortComponentAnchor26607 = """'))]
rescue=k[k.index('val shortRescueWeight26607 = \"\"\"'):k.index('\"\"\".trimIndent()',k.index('val shortRescueWeight26607 = \"\"\"'))]
assert 'mirrorUvs(referenceUv + flow.xy)' not in rescue
assert 'flattenedNormal' not in anchor and 'max(correlation, flattenedNormal)' not in rescue
assert 'visualRescueWeight = censoredCoreWeight * clamp(visualHighRadiance, 0.0, 1.0);' in rescue
assert 'effectiveRescueWeight = censoredCoreWeight * clamp(effectiveLoss, 0.0, 1.0);' in rescue
# Existing -2.5EV policy/capture owners are outside exact allowlist and therefore byte-identical; no capture files changed.
root=Path(__file__).resolve().parent
allow={x for x in (root/'R1_26645_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x}
assert not any('capture' in x.lower() or 'motionbatch' in x.lower() for x in allow)
# Tone must not repeat 26644's structure-insensitive shoulder/clamp behavior.
g=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
assert 'structureShoulderScale=1.0-0.72*sourceStructureGate;' in g
assert 'protectedBase=max(shadowBase-sourceStructureGate*positiveOvershoot' in g
# HEIC 26644 full-range hardware transport remains byte-identical; 26645 must delete a file failing platform Ultra-HDR readback.
hw='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java'; assert sha(base,hw)==sha(cand,hw)
h=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
assert 'if (ok) ok = iris26645VerifyPlatformReadback(output, gm);' in h and 'if (!ok) Files.deleteIfExists(output);' in h
assert 'decoded.hasGainmap()' in h and 'ColorSpace.Named.DISPLAY_P3' in h
# Never fake public BT709/SDR-video aspects to stand in for AOSP P3/sRGB HEIC colorimetry.
hwt=txt(cand,hw); assert 'format.setInteger(MediaFormat.KEY_COLOR_STANDARD' not in hwt and 'format.setInteger(MediaFormat.KEY_COLOR_TRANSFER' not in hwt
# Native/libheif/ISO21496/gain-map ownership is frozen.
for p in ['app/src/main/cpp/iris_heic_jni.cpp','app/src/main/cpp/iris26643_libheif_aosp_contract.patch','app/src/main/cpp/CMakeLists.txt']:
 assert sha(base,p)==sha(cand,p),p
# Manual knob module is not introduced into the app authority; only its private background paint is neutralized from app UI.
u=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
assert 'getDeclaredField("m_BackgroundPaint")' in u and 'android.graphics.Color.TRANSPARENT' in u
print('PASS 26645 regressions: 26644 border/full-range fixes retained; visual SHORT requires correlated structure; structured tone reserves headroom; bad HEIC fails closed; native/gain-map/capture domains frozen; knob half-circle isolated')
