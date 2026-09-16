#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26650_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r; b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
# Critical 26648 owners untouched.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java','app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert same(r),r
# Permanent 26649 failure: never graft shoulder onto Iris final-guide map; never inherit 26649 runtime tokens.
alltxt='\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main').rglob('*') if p.is_file() and p.suffix in {'.java','.kt','.glsl','.xml'})
assert 'IRIS_26649_PHOTON_HIGHLIGHT_COMPRESSION_OWNER' not in alltxt
assert 'iris26649PhotonSoftShoulder' not in alltxt
assert 'iris26649PhotonHighlightKnee' not in alltxt
# New owner uses Motion Camera2 noise only.
j=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_text()
assert 'motionV2WronskiNoiseS' in j and 'motionV2WronskiNoiseO' in j
assert 'basePipeline.noiseS' not in j and 'basePipeline.noiseO' not in j
# SHORT remains upstream authority and excluded from temporal/SR/DNG as in 26648.
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); sh=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for t in ['if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']: assert t in st
for t in ['IRIS_26648_UNIVERSAL_NORMAL_SHORT_RADIOMETRIC_FUSION_OWNER','vec3 fused = mix(normalMean.rgb, shortRgb, authority)','oFusedExtendedLinear = vec4(fused, normalMean.a)']: assert t in sh
# OFF-local path tokens retained, ON gating explicit.
rm=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
assert '1.0-pow(max(1.0-baseLinear,0.0),1.12)' in rm and 'mix(1.0,0.78,upperGate)' in rm
assert 'iris26650HighlightCompressionEnabled' in rm
# Infrastructure regression is inspected by infrastructure verifier: shader compiler must consume expanded variants only.
print('PASS 26650 permanent regressions: 26648 SHORT/fusion/HEIC/DNG protected; no 26649 shoulder graft; Motion noise authority; OFF 26648 local path retained with ON-only neutralization')
