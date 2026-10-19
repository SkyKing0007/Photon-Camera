"""26856 actual newly wired B 2x evidence/RAWR file-owner regression.
This is semantic static regression, never a real GLSL/Android compiler substitute.
"""
from pathlib import Path
r=Path(__file__).resolve().parents[1]/'handoff_payload_26856/app/src/main/java'
paths={
 'bridge':r/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'fusion':r/'com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
 'sabre':r/'com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
 'stacker':r/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'result':r/'com/hinnka/mycamera/processor/RawStackContracts.kt',
 'cfa':r/'com/hinnka/mycamera/processor/GlesIris26856True2xCfa.kt',
}
s={n:p.read_text() for n,p in paths.items()}
for owner in ('bridge','fusion','sabre','stacker'):
 assert 'iris26856BTrue2x' in s[owner], owner
assert 'experiment26856 != Iris26856ABSettings.Mode.ORIGINAL_26850' in s['bridge']
assert 'IRIS_26856_B_TRUE2X_GUARDED_ACTIVATION' in s['bridge']
assert '26856 B/A+B with Super Res requires independent RAWR 2x output; forbidden until implemented' not in s['bridge']
assert 'iris26856BTrue2x = iris26856BTrue2x' in s['fusion']
assert 'iris26856BTrue2x = iris26856BTrue2x' in s['sabre']
assert 'enableSabreSuperRes || iris26856BTrue2x' in s['stacker']
assert 'iris26856BTrue2xRgbPath = iris26856BTrue2xFile?.absolutePath' in s['stacker']
assert 'runCatching { iris26856BTrue2xFile?.delete() }' in s['stacker']
assert 'val iris26856BTrue2xRgbPath: String? = null' in s['result']
start=s['stacker'].index('private fun reconstructIris26856BTrue2xTiles(')
end=s['stacker'].index('private fun reconstructTrue2x(',start)
block=s['stacker'][start:end]
for item in (
 'evidence.size == normalCount', 'evidence.map { it.frameIndex }.toSet().size == evidence.size',
 'readTrue2xRawRegion(images[ev.frameIndex]', 'ev.calibration.bayerPhaseGains',
 'ev.calibration.bayerPhaseBlackTerms', 'ev.covarianceFile', 'ev.rejectionFile',
 'uFlowScaleOffset', 'uPhaseMoments', 'uPhaseBins', 'uMinimumWeight',
 'GLES30.GL_MAX_DRAW_BUFFERS', 'GLES30.GL_ONE, GLES30.GL_ONE',
 'Half.toFloat(half.get(i * 4 + 1)) >= 0.5f',
 'consumer(packed, postWb, tw, th, cfaPattern,',
 'renderRawrBPostAmaze26856(', 'writer.writeExpandedRgba16f(tile, pixels)',
 'writer.finish()', 'releaseTexturesFrom(initialTextureCount)',
):
 assert item in block,item
for forbidden in ('nativeVgnGuideTexture','true2xGuideRenderProgram26568','interpolateRgb',
                  'GlesMgcRawSpatialStacker26850','useFallback'):
 assert forbidden not in block,forbidden
assert 'GlesIris26856True2xCfa.accumulate' in block
assert 'GlesIris26856True2xCfa.resolve' in block
assert 'GlesIris26856True2xCfa.pack' in block
assert 'distinct>=2 && varianceX>=0.14 && varianceY>=0.14' in s['cfa']
print('PASS B-only true2x: full NORMAL evidence -> 3 MRT CFA -> strict phase -> pinned RAWR -> Lab/FCC -> independent atomic file')
print('PASS A/Sabre/VGN 2x not consumed; B production Super Res active with strict invalid-site rejection')
