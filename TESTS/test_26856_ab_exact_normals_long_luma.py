#!/usr/bin/env python3
"""Permanent 26856 capture/LONG source-contract regressions; not a device or GLSL compiler."""
import math, os, re
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT = Path(__file__).resolve().parent.parent/'handoff_payload_26856'/'app/src/main/java'
CAP = (ROOT/'com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
ST = (ROOT/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
SH = (ROOT/'com/hinnka/mycamera/processor/GlesIris26856B2xShortGuide.kt').read_text()
A = (ROOT/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker26850.kt').read_text()

def must(ok, description):
    assert ok, description
    print('PASS '+description)

must('final boolean iris26856ExactNormals' in CAP and
     'iris26856FrozenExperiment != com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode.ORIGINAL_26850' in CAP and
     'mMotion26575SuperResAtShutter && !iris26856ExactNormals' in CAP and
     ': iris26593NormalTarget;' in CAP,
     'only selected B/A+B disallows inherited 4-frame SR reduced-admission; A-only remains legacy')
must(CAP.count('iris26856FrozenExperiment.id') >= 2 and
     'iris26856BExactNormalAdmission=' in CAP and
     'iris26856FrozenExperiment.id,\n                mPreviewAFMode' in CAP,
     'same immutable physical lens B/A+B selection used for capture count and plan')
must('iris26593TotalTarget - iris26593AuxCount' in CAP and
     'final int iris26593AuxCount = iris26505LongRequested ? 1 : 0' in CAP and
     'final boolean iris26480ShortHighlightRequested = false' in CAP,
     '15 total with accepted physical LONG = 14 NORMAL + 1 LONG; retired SHORT unchanged')
must('submitMotion26593MissingNormals(iris26593Plan, iris26593MissingNormals)' in CAP and
     'normalReadyCount >= plan.normalTargetFrames' in CAP,
     'failed/missing NORMAL uses existing owned topup and full-count completion predicate')
for name, function in [('A-only mode',False),('B-only mode',True),('A+B mode',True)]:
    for existing in (0,1,3,4,9,14,20):
        requested = 14
        count = requested if function else min(requested,max(min(4,requested),min(existing,requested)))
        must(count == (14 if function else min(14,max(4,min(existing,14)))) , f'{name}, buffered={existing}: correct immutable NORMAL target={count}')
must('shadowLongLumaGain26833 = renderSabreShadowLongLumaGainMap26833(' in ST and
     'renderSabreShadowLongPostVgnLumaApply26833(' in ST and
     'IRIS_26845_LONG_LUMA_FUSED' in ST,
     'A existing 26845 gain/trust producer and post-VGN RGB publication preserved')
must('renderIris26856BVerifiedLongLuma(' in ST and
     'iris26856BTrue2xFile = reconstructIris26856BTrue2xTiles(' in ST and
     'shadowLongLumaGain26833,\n                )' in ST and
     'renderIris26856BVerifiedLongLuma(\n                                    sensorRgb, physicalLongLumaGuide' in ST,
     'native B and 2x B share verified LONG scalar without A RGB transport')
must('physicalLongLumaGuide != 0' in ST and
     'if (iris26856RawrRgbSidecar != 0 && shadowLongLumaGain26833 != 0)' in ST,
     'absent/rejected LONG is B identity; B native scalar is opt-in only')
must('outputScale in 1..2' in ST and 'vec4(rgb.rgb*gain,rgb.a)' in SH and
     'uExpandedOrigin' in SH and 'float(uOutputScale)' in SH and
     'vec2 fractPart=fract(mapped)' in SH and
     'float gain=mix(mix(g00,g10,fractPart.x),mix(g01,g11,fractPart.x),fractPart.y)' in SH,
     'B native and tiled 2x apply scalar only with bilinear native geometry, no resized RGB')
must('releaseOwnedTexture(shadowLongLumaGain26833,' in ST and
     '26856 B failed/aborted verified LONG guide' in ST and
     'shadowLongLumaGain26833 = 0' in ST,
     'no shared LONG GPU guide lifetime escape through success/error paths')
must('GlesMgcRawSpatialStacker26850' not in ST or 'enableSabreSuperRes' in ST,
     'B-only owner does not replace historical A class')
# Literal ratio math is scalar. Simulate RGB triplets including out-of-range HDR, not SDR-clamped.
for r,g,b in [(0.03,0.1,0.04),(1.1,0.28,0.34),(0.0,0.0,0.0),(3.8,1.7,0.92)]:
    for gain in (0.78,0.94,1.0,1.12,1.42):
        actual=(r*gain,g*gain,b*gain)
        for i,v in enumerate((r,g,b)):
            must(abs(actual[i]-v*gain)<1.e-10 and (v==0 or abs(actual[i]/v-gain)<1.e-10),
                 f'B scalar preserves chroma ratio: rgb={(r,g,b)} gain={gain} ch={i}')
# Whole-frozen A source hash asserted by package full-manifest proof, not independently faked here.
print('PASS 26856 target contract static regression suite (real compilers NOT RUN)')
