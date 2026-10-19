#!/usr/bin/env python3
"""26856 B-only A/VGN failure isolation contracts; static source regression only.

Does NOT simulate an Android EGL context, validate a real JPEG, or compile Kotlin.
The actual bypass point must occur before post-CFA VGN and the explicit B branch
must exit without processing the post-branch A-only code.
"""
from pathlib import Path
R=Path(__file__).resolve().parent.parent/'handoff_payload_26856'/'app/src/main/java'
S=(R/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
F=(R/'com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
B=(R/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
H=(R/'com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
assert B.count('iris26856BOnlyIndependentPublication = !parameters.irisNightActive &&')==1
assert 'experiment26856 == Iris26856ABSettings.Mode.AMAZE_26855,' in B
assert F.count('iris26856BOnlyIndependentPublication = iris26856BOnlyIndependentPublication,')==1
assert S.count('private val iris26856BOnlyIndependentPublication: Boolean = false,')==1
assert F.count('private val iris26856BOnlyIndependentPublication: Boolean = false,')==1
assert B.count('enableHighZoomDetail = highZoomDetailEnabled,')==2
# An ordinary mode table catches A or A+B accidentally entering B-only publication.
for name,night in [('ORIGINAL_26850',False),('AMAZE_26855',False),('BOTH',False),('AMAZE_26855',True)]:
    isolate=(not night and name=='AMAZE_26855')
    assert isolate == (name=='AMAZE_26855' and not night)
# The completed B color payload is produced first, independent of A post CFA/VGN.
assert S.index('iris26856RawrRgbSidecar = renderRawrBPostAmaze26856(') < S.index('IRIS_26856_B_ONLY_POST_AMAZE_INDEPENDENT_PUBLICATION')
assert S.index('renderSabreShadowLongLumaGainMap26833(') < S.index('IRIS_26856_B_ONLY_POST_AMAZE_INDEPENDENT_PUBLICATION')
chunk=S.split('/* IRIS_26856_B_ONLY_POST_AMAZE_INDEPENDENT_PUBLICATION',1)[1].split('/* IRIS_26792_CFA_DOMAIN_NEUTRAL_OWNERSHIP',1)[0]
assert 'if (iris26856BOnlyIndependentPublication) {' in chunk
assert 'return isolatedBResult' in chunk and 'returned = true' in chunk
assert 'return isolatedBResult' in chunk.split('returned = true',1)[1]
assert 'renderIris26856BVerifiedLongLuma(' in chunk
assert 'reconstructHighZoomDetail26718(' in chunk
assert 'nativeVgnGuideTexture = iris26856RawrRgbSidecar' in chunk
assert 'reconstructIris26856BTrue2xTiles(' in chunk
assert 'shadowLongLumaGain26833,' in chunk
assert 'normalStackedDngRaw16 = normalStackedDngRaw16' in chunk
assert 'normalStackedDngFrameCount = if (exportNormalStackedDng) normalFrameCount else 0' in chunk
assert 'iris26856RawrRgbSidecar = GpuLinearRgbSource(' in chunk
assert 'gpuLinearRgbSource = GpuLinearRgbSource(' in chunk
assert 'exportedTexture = copyPersistentTexture(' in chunk
assert 'check(textures.remove(exportedTexture))' in chunk
assert 'check(textures.remove(bSidecar))' in chunk
assert 'iris26856RawrRgbSidecar = 0' in chunk
assert 'check(!highlightShortScheduled26607)' in chunk
assert 'postprocessedUi' not in chunk and 'sabreRgbChromaPostprocessor' not in chunk
# A's CFA adapter/Resolve/VGN remain after the explicit B-only branch exit.
assert S.index('IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER') < S.index('return isolatedBResult') # shared LONG input still needs this producer
assert S.index('return isolatedBResult') < S.index('MGC Sabre Resolve/VGN color noise')
assert S.index('return isolatedBResult') < S.index('val nativeHdrAuthority26601 = exportedTexture')
# A+B still deliberately runs separate historical 26850 and retains existing pair rollback.
assert 'val stacked = if (experiment26856 == Iris26856ABSettings.Mode.BOTH)' in B
assert 'exactHistorical26850 = true' in B
assert 'stackB26856.iris26856RawrRgbSidecar' in B
assert 'if (iris26856Both)' in H and 'rollback' in H.lower()
# Stop accidental "both tex aliases" cleanup regression; the B and legacy bridge texture IDs differ.
assert 'copyPersistentTexture(\n                    iris26856RawrRgbSidecar' in chunk
print('PASS isolated B-only B JPEG route returns before A Resolve/VGN after completed B AMaZE')
print('PASS distinct GL result owners, bounded LONG, zoom, true2x, NORMAL DNG, A+B and A-only isolation')
print('COMPILERS / NDK / ASSEMBLE / PHYSICAL JPEG: NOT RUN')
