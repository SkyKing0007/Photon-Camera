#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_r1_2_26648_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'app').rglob('*')) if p.is_file()}
assert H(base)==H(cand) and len(H(base))==1720, 'R1.2 packaging repair changed runtime bytes'
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); sh=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
assert 'if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)' in st
assert 'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)' in st
assert 'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)' in st
assert 'oFusedExtendedLinear = vec4(fused, normalMean.a)' in sh
assert 'frameWeight = rescuedWeight' not in st
fusion=sh.split('val universalNormalShortFusion26648 = """',1)[1].split('""".trimIndent()',1)[0]
assert 'uniform sampler2D uShortExtractedBayer;' in fusion and 'uExtractedBayer' not in fusion
assert 'texelFetch(uShortPhysicalReverseWeight' in fusion and 'texture(uShortPhysicalReverseWeight' not in fusion
assert 'vec3 fused = mix(normalMean.rgb, shortRgb, authority)' in fusion
he=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java').read_text(); assert 'IRIS_26648_HEIC_NUMERICAL_HDR' in he and 'destructiveFailure=false' in he
ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text(); assert 'IRIS_26648_CONTRAST_SAFE_KNOB_TEXT' in ui and 'manualMode.setBackgroundResource(android.R.color.transparent)' in ui
print('PASS 26648 R1.2 permanent regressions: runtime byte-identical to successful R1.1; sampler fix, universal fusion, HEIC proof, and transparent contrast-safe UI retained')
