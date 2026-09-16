#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_r1_1_26648_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r): return hashlib.sha256((base/r).read_bytes()).digest()==hashlib.sha256((cand/r).read_bytes()).digest()
# Successful-26646 unrelated architecture/DNG/tone/JPEG/native-build owners remain byte-identical.
for r in [
'app/src/main/cpp/CMakeLists.txt',
'app/src/main/cpp/iris26642_libheif_android16_tmap.patch','app/src/main/cpp/iris26643_libheif_aosp_contract.patch',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java']:
 assert same(r),r
# Native HEIF change is matrix-only: normalize the four intended matrix/comment/log edits back to 26646 exactly.
b=(base/'app/src/main/cpp/iris_heic_jni.cpp').read_text(); c=(cand/'app/src/main/cpp/iris_heic_jni.cpp').read_text()
n=c.replace('heif_matrix_coefficients_ITU_R_BT_601_6','heif_matrix_coefficients_unspecified')
n=n.replace('// BT.601 matrix, full range, and a single NCLX colr authority (no parallel ICC).','// unspecified matrix, full range, and a single NCLX colr authority (no parallel ICC).')
n=n.replace('// Display-P3/sRGB/BT.601-matrix/full-range color aspects and 8-bit PIXI.','// Display-P3/sRGB/unspecified-matrix/full-range color aspects and 8-bit PIXI.')
n=n.replace('baseP3SrgbBt601Matrix=true','baseP3SrgbMatrixUnspecified=true')
assert n==b,'iris_heic_jni.cpp changed beyond the four intended BT.601 NCLX matrix declarations/comments/log token'
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
sh=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
# SHORT must not become temporal/noise/DNG/high-frequency SR evidence.
assert 'if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)' in st
assert 'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)' in st
assert 'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)' in st
assert 'oFusedExtendedLinear = vec4(fused, normalMean.a)' in sh
assert 'frameWeight = rescuedWeight' not in st
# No old rescue/component/boundary owner is called from the active path.
for call in ['renderSabreShortComponentRecover26626(','renderSabreShortComponentRescueWeight26607(',
             'renderSabreShortBoundaryRecover26606(']:
 assert call not in st,call
# Old late/private restore functions may remain as dead provenance but their programs are hard-zero.
for token in ['sabreShortRestoreRgba16fProgram26587 = 0','sabreShortProtectedAccumulatorFuseProgram26602 = 0',
              'sabreShortBoundaryAnchorProgram26606 = 0','sabreShortComponentAnchorProgram26607 = 0']:
 assert token in st,token
# No blurred/dilated fusion authority: exact ordinary rejection blocker is retained before the generic frame mask is released.
assert 'retainedShortPhysicalReverseWeight26648 = shortPhysicalReverseWeight26610' in st
assert 'releaseOwnedTexture(frameWeight, "26648 retired ordinary SHORT photometric weight")' in st
fusion=sh.split('val universalNormalShortFusion26648 = """',1)[1].split('""".trimIndent()',1)[0]
assert 'uniform sampler2D uShortExtractedBayer;' in fusion
assert 'uExtractedBayer' not in fusion  # exact 26648 Actions failure regression: stale sampler name must never survive
assert 'texelFetch(uShortPhysicalReverseWeight' in fusion
assert 'texture(uShortPhysicalReverseWeight' not in fusion
# Same scalar authority owns RGB and validity; there is no per-channel exposure selection.
assert 'vec3 fused = mix(normalMean.rgb, shortRgb, authority)' in fusion
assert 'totalWeight * authority' in sh.split('val universalShortValidityAugment26648 = """',1)[1].split('""".trimIndent()',1)[0]
# HEIC gain-map and native tmap/ISO construction remain present; no arbitrary gain strengthening in Java publisher.
he=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java').read_text()
assert 'IRIS_26648_HEIC_NUMERICAL_HDR' in he and 'destructiveFailure=false' in he
assert 'expectedNeedsExpansion' in he and 'actualExpansion > 1.005' in he
# UI explicitly keeps transparent palette and no backing shape.
ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text()
assert 'manualMode.setBackgroundResource(android.R.color.transparent)' in ui
assert 'No chip/pill/scrim/background' in ui
assert 'IRIS_26648_CONTRAST_SAFE_KNOB_TEXT' in ui
assert 'getDeclaredField("m_KnobItems")' in ui and 'getDeclaredField("m_HasStroke")' in ui
assert 'setTextColor.invoke(drawable, android.graphics.Color.WHITE)' in ui
assert 'root.post(() -> iris26644StyleManualPalette(root))' in ui
print('PASS 26648 permanent regressions: 26646 tone/DNG/JPEG/libheif-build owners frozen; native HEIF matrix-only; no SHORT temporal/SR-detail leakage; no old rescue/dilation/per-channel authority; HEIC proof and complete transparent contrast-safe white manual UI retained')
