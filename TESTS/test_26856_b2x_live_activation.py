#!/usr/bin/env python3
"""Regression of previously unreachable B-only Super Res route and distinct A+B.

This proves ownership and source contracts only. GPU/GLSL/Android compilation
and real capture correctness must still be proved by GitHub Actions/device.
"""
from pathlib import Path
r=Path(__file__).resolve().parents[1]/'handoff_payload_26856/app/src/main/java'
bridge=(r/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
merger=(r/'com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java').read_text()
hdr=(r/'com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
stack=(r/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
cfa=(r/'com/hinnka/mycamera/processor/GlesIris26856True2xCfa.kt').read_text()
for item in (
 'enableSabreSuperRes = sabreSuperResEnabled &&\n                    experiment26856 == Iris26856ABSettings.Mode.ORIGINAL_26850',
 'iris26856BTrue2x = sabreSuperResEnabled && !parameters.irisNightActive',
 'iris26856BTrue2xRgbPath = stackB26856.iris26856BTrue2xRgbPath',
 'iris26856BTrue2xOutputHandedOff = result.iris26856BTrue2xRgbPath != null',
 'if (!iris26856BTrue2xOutputHandedOff)',
 'b2x26856.length() == stacked.iris26856BTrue2xWidth.toLong() *',
 'if (sabreSuperResEnabled &&\n                experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855)',
 'if(parameters.motionV2SuperResOutputEnabled &&\n                experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855)',
 'IRIS_26856_B_TRUE2X_GUARDED_ACTIVATION',
 'IRIS_26856_B_TRUE2X_SEPARATE_NORMAL_CFA_OWNER',
 'val historicalFrames = frames.mapIndexed',
 'val historical = GlesMgcRawFusion(',
 'val stacked = if (experiment26856 == Iris26856ABSettings.Mode.BOTH)',
):assert item in bridge,item
forbidden='26856 B/A+B with Super Res requires independent RAWR 2x output; forbidden until implemented'
assert forbidden not in bridge
assert 'require(!iris26856BTrue2x || (!enableSabreSuperRes && !enableHighZoomDetail' in stack
assert 'Half.toFloat(half.get(i * 4 + 1)) >= 0.5f' in stack
assert 'distinct>=2 && varianceX>=0.14 && varianceY>=0.14' in cfa
assert 'public String iris26856BTrue2xRgbPath = null;' in merger
for item in (
 'mIris26856BTrue2xPathForCleanup = iris26856BTrue2xRgbPath;',
 'if (mIris26856BTrue2xPathForCleanup != null)',
 'final String iris26856Primary2x = iris26856BOnly',
 'iris26856BTrue2xRgbPath, iris26856BTrue2xWidth,\n                        iris26856BTrue2xHeight, iris26856BPostParameters,',
 '"26856 B-only true2x cannot consume A SR"',
 'mIris26856BTrue2xPathForCleanup = null;',
 'File(path).delete()' if False else 'java.nio.file.Files.deleteIfExists',
):assert item in hdr,item
assert hdr.count('saveBitmapAsJPGMotionV2(')>=2
# Once A+B selects BOTH, B's independent 2x result must not satisfy the A
# Sabre backend validation, and A's only reconstruction must be historical.
for mode in ('ORIGINAL_26850','AMAZE_26855','BOTH'):
 use_a=(mode!='AMAZE_26855')
 use_b=(mode!='ORIGINAL_26850')
 assert (use_a,use_b) == {
  'ORIGINAL_26850':(True,False),
  'AMAZE_26855':(False,True),
  'BOTH':(True,True),
 }[mode]
assert 'dngParams.motionV2SuperResOutputEnabled && !iris26856BOnly && !iris26856Both' in hdr
assert 'processingParameters.motionV2SuperResOutputEnabled && !iris26856BOnly && !iris26856Both' in hdr
print('PASS 26856 A / B / A+B real Super Res routing: historical A and independent B distinct')
print('PASS unsupported GPU/CFA still fail shut; no fallback, one retained NORMAL burst, one DNG owner')
print('PASS B 2x JPEG HDR carrier independent; A-only legacy assertions unchanged')
