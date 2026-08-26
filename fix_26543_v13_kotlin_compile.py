#!/usr/bin/env python3
from pathlib import Path
import argparse, tempfile, shutil

REL = Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')

def once(s, old, new, label):
    n=s.count(old)
    if n != 1:
        raise RuntimeError(f'{label}: expected exactly 1 anchor, found {n}')
    return s.replace(old,new,1)

def apply(root: Path):
    p=root/REL
    s=p.read_text()
    s=once(s,
'''        val averageShot = calibration.bayerPhaseShotNoise.average().coerceAtLeast(1.0e-8f)
        val averageRead = calibration.bayerPhaseReadNoise.average().coerceAtLeast(0.0f)
        uniform2f(covarianceProgram, "uFigure7Noise", averageShot, averageRead)
''',
'''        val averageShot = calibration.bayerPhaseShotNoise.average().coerceAtLeast(1.0e-8).toFloat()
        val averageRead = calibration.bayerPhaseReadNoise.average().coerceAtLeast(0.0).toFloat()
        uniform2f(covarianceProgram, "uFigure7Noise", averageShot, averageRead)
''','Figure-7 FloatArray.average Kotlin types')
    s=once(s,
'''                    renderRgbMerge(
                        frames = resolveRgbFlowBounds(rgbMergeFrames),
                        images = images,
                        outputExposureScale = outputExposure.normalizationScale,
                        diagnosticCapture = readyStrengthCapture,
                    )
''',
'''                    renderRgbMerge(
                        frames = resolveRgbFlowBounds(rgbMergeFrames),
                        images = images,
                        outputExposureScale = outputExposure.normalizationScale,
                        diagnosticCapture = readyStrengthCapture,
                        kernelTuning = bayerKernelTuning,
                    )
''','renderRgbMerge caller tuning')
    s=once(s,
'''    private fun renderRgbMerge(
        frames: List<RgbMergeFrame>,
        images: List<SafeImage>,
        outputExposureScale: Float,
        diagnosticCapture: StrengthCapture?,
    ): RgbMergeOutput {
''',
'''    private fun renderRgbMerge(
        frames: List<RgbMergeFrame>,
        images: List<SafeImage>,
        outputExposureScale: Float,
        diagnosticCapture: StrengthCapture?,
        kernelTuning: BayerKernelTuning,
    ): RgbMergeOutput {
''','renderRgbMerge parameter tuning')
    s=once(s,
'''                                kernelTuning = bayerKernelTuning,
                                covarianceRegion = frameRegion.covarianceRegion,
''',
'''                                kernelTuning = kernelTuning,
                                covarianceRegion = frameRegion.covarianceRegion,
''','banded covariance tuning scope')
    p.write_text(s)
    print('PASS: 26543 V1.3 Kotlin compiler correction applied')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        # Self-test validates replacement engine on a minimal synthetic copy of the four anchors.
        sample='''        val averageShot = calibration.bayerPhaseShotNoise.average().coerceAtLeast(1.0e-8f)\n        val averageRead = calibration.bayerPhaseReadNoise.average().coerceAtLeast(0.0f)\n        uniform2f(covarianceProgram, "uFigure7Noise", averageShot, averageRead)\n                    renderRgbMerge(\n                        frames = resolveRgbFlowBounds(rgbMergeFrames),\n                        images = images,\n                        outputExposureScale = outputExposure.normalizationScale,\n                        diagnosticCapture = readyStrengthCapture,\n                    )\n    private fun renderRgbMerge(\n        frames: List<RgbMergeFrame>,\n        images: List<SafeImage>,\n        outputExposureScale: Float,\n        diagnosticCapture: StrengthCapture?,\n    ): RgbMergeOutput {\n                                kernelTuning = bayerKernelTuning,\n                                covarianceRegion = frameRegion.covarianceRegion,\n'''
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/REL; p.parent.mkdir(parents=True); p.write_text(sample); apply(Path(td)); out=p.read_text()
            assert 'coerceAtLeast(1.0e-8).toFloat()' in out
            assert 'coerceAtLeast(0.0).toFloat()' in out
            assert 'kernelTuning = bayerKernelTuning' in out
            assert 'kernelTuning: BayerKernelTuning' in out
            assert 'kernelTuning = kernelTuning' in out
        print('PASS: 26543 V1.3 Kotlin compiler correction self-test')
        return
    if not a.root: ap.error('--root required')
    apply(Path(a.root).resolve())
if __name__=='__main__': main()
