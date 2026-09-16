#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26647_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r): return hashlib.sha256((base/r).read_bytes()).digest()==hashlib.sha256((cand/r).read_bytes()).digest()
# Protected architecture/native/DNG/tone owners from successful 26646 remain byte-identical.
for r in [
'app/src/main/cpp/CMakeLists.txt','app/src/main/cpp/iris_heic_jni.cpp',
'app/src/main/cpp/iris26642_libheif_android16_tmap.patch','app/src/main/cpp/iris26643_libheif_aosp_contract.patch',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java']:
 assert same(r),r
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
sh=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
# 26647 must not revive the rejected huge private SHORT accumulator or any post-VGN blend.
assert 'privateShortAccumulator=false' in st and 'postVgnBlend=false' in st
assert 'frameWeight = rescuedWeight' not in st
assert 'val appliedRescue = createTexture(width, height, GLES30.GL_R16F' in st
assert 'val output = createTexture(width, height, GLES30.GL_RGB10_A2' in st
assert 'renderSabreFinalShortFusion26647(' in st and st.index('renderSabreFinalShortFusion26647(')<st.index('chromaPostprocessor.process(')
assert 'oColorAndRWeight = vec4(shortMean, finalRescueAlpha)' in sh
assert 'fusedValidity = mix(priorValidity, vec3(1.0), rescue)' in sh
# Ordinary SHORT remains on common Sabre path, rescue is separate from temporal support.
assert 'weight = frameWeight,' in st and 'rescueAffectsTemporalSupport=false' in st
# Successful 26646 universal source support/effective-loss mechanics still present.
for token in ['IRIS_26644_SHORT_SOURCE_SUPPORT_FAIL_CLOSED','IRIS_26645_VISUAL_HIGH_RADIANCE_COMPONENT_OWNER','IRIS_26646_UNIVERSAL_HIGH_DYNAMIC_RANGE_SHORT_OWNER']:
 assert token in sh,token
# HEIC native writer/gainmap/tmap authority is untouched; Java hardware base gets explicit aspects only.
hw=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java').read_text()
assert 'if (!gainMap)' in hw and 'AOSP_COLOR_STANDARD_DISPLAY_P3' in hw and 'AOSP_COLOR_TRANSFER_SRGB' in hw
he=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java').read_text()
assert 'destructiveFailure=false' in he and 'IRIS_26647_BOUNDED_TRUE2X_BASE_PROOF' in he
print('PASS 26647 permanent regressions: 26646 native/ISO21496/tone/DNG owners frozen; no huge/private SHORT accumulator; no post-VGN rescue; ordinary temporal support retained; bounded HEIC proof')
