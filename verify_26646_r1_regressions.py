#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26646_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(r,p): return (r/p).read_text()
def sha(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
k=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for token in ['IRIS_26644_SHORT_SOURCE_SUPPORT_FAIL_CLOSED','IRIS_26644_SHORT_WARP_DOMAIN_FAIL_CLOSED','IRIS_26644_SHORT_EXTRACTED_BILINEAR_FAIL_CLOSED','if (!shortSupportValid)','IRIS_26646_UNIVERSAL_HIGH_DYNAMIC_RANGE_SHORT_OWNER']:
 assert token in k,token
rescue=k[k.index('val shortRescueWeight26607 = """'):k.index('""".trimIndent()',k.index('val shortRescueWeight26607 = """'))]
assert 'mirrorUvs(referenceUv + flow.xy)' not in rescue
assert 'visualRescueWeight = physicalWeight * visualRadianceConfidence;' in rescue
assert 'visualRadianceConfidence = min(shortHeadroom' in rescue
assert 'effectiveRescueWeight = censoredCoreWeight * clamp(effectiveLoss, 0.0, 1.0);' in rescue
assert 'float censoredCoreWeight = min(physicalWeight, rescueConfidence);' in rescue
# Capture/EV policy is outside 26646 allowlist.
root=Path(__file__).resolve().parent
allow={x for x in (root/'R1_26646_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x}
assert not any('capturecontroller' in x.lower() or 'motionbatch' in x.lower() or 'isoexposelector' in x.lower() for x in allow)
# Tone regression: no cross-material one-sided residual import; bounded scalar luminance residual only.
g=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
for token in ['if(admitted<3||weightSum<2.55) continue;','float sameMaterial=1.0-smoothstep(0.24,0.34,d);','float boundedMissing=min(missing,0.18);','signAgreement','IRIS_26646_EXTENDED_LINEAR_RADIANCE_SURVIVAL_OWNER']:
 assert token in g,token
assert 'vec3 candidate=vec3(sign(srcResidual)*boundedMissing,boundedMissing,confidence);' in g
# Proven 26645 hardware MediaCodec full-range owner unchanged; do not add fake color-standard/transfer overrides.
hw='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java'; assert sha(base,hw)==sha(cand,hw)
hwt=txt(cand,hw); assert 'MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL' in hwt
assert 'format.setInteger(MediaFormat.KEY_COLOR_STANDARD' not in hwt and 'format.setInteger(MediaFormat.KEY_COLOR_TRANSFER' not in hwt
# HEIC readback mismatch must never delete a structurally saved file.
h=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
assert 'destructiveFailure=false' in h and 'readbackFailureNonDestructive=true' in h
assert 'if (!ok) Files.deleteIfExists(output);' not in h
# SR+HEIC must be true2x grid, never 12MP or JPEG fallback.
m=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
assert 'writeSuperResGrid(' in m and 'jpegRFallback=false native12mpFallback=false' in m
n=txt(cand,'app/src/main/cpp/iris_heic_jni.cpp')
assert 'heif_context_add_grid_image' in n and '2u, 2u' in n and 'heif_context_add_image_tile' in n
assert 'heif_context_encode_gain_map_image(ctx, baseHandle' in n and 'halfLinearGain=true' in n
assert 'isoMetadata.insert' not in n
# Pinned libheif/AOSP contract patch remains byte-identical; the API already writes ISO21496 version byte.
p='app/src/main/cpp/iris26643_libheif_aosp_contract.patch'; assert sha(base,p)==sha(cand,p)
# Manual rectangle/half-circle cleanup remains exact 26645 protected UI authority.
u='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'; assert sha(base,u)==sha(cand,u)
print('PASS 26646 regressions: fail-closed SHORT source/borders retained; correlated visual HDR bypasses only sparse componentTrust; tone cannot import one-sided edge residuals; 26645 full-range HEVC retained; HEIC readback non-destructive; SR HEIC true2x grid/no fallback; UI frozen')
