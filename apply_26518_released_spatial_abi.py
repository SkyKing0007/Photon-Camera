#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib
from pathlib import Path

STACKER = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
CHANGED = {STACKER}
MARKER = 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE'
ANCHOR = r'''                mgcSpatialStrengthMap = spatialNoiseModel?.strengthMap?.let(
                    ::mapSpatialStrengthToOutputCoordinates,
                ),
                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
'''
REPLACEMENT = r'''                mgcSpatialStrengthMap = spatialNoiseModel?.strengthMap?.let(
                    ::mapSpatialStrengthToOutputCoordinates,
                ),
                /* IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE
                 * Released c4ff already computes bayerKernelTuning.referenceSnr and uses it for
                 * its Spatial kernel selection. Its historical RawStackResult predates the later
                 * process-local tuning-SNR fields. Export that same c4ff value into the newer ABI
                 * only; do not import post-Sabre Spatial tuning or Sabre TET attenuation math.
                 */
                mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,
                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
'''

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def expected_text(text: str) -> str:
    s=text.replace('\r\n','\n').replace('\r','\n')
    if MARKER in s:
        raise AssertionError('26518 ABI bridge already present')
    for token in (
        'internal class GlesMgc1271ReleasedSpatialStacker(',
        'private val guideWidth = max(1, width / 4)',
        'bayerKernelTuning.referenceSnr',
        'mgcDenoiseReadNoise = outputReadNoise',
        'mgcDenoiseShotNoise = outputShotNoise',
        'mgcSpatialReferenceOnlyDiagnostic = referenceOnly',
    ):
        if token not in s: raise AssertionError('released-c4ff owner anchor missing: '+token)
    for forbidden in (
        'MgcRawProcessorPipeline',
        'MgcSpatialMergeTuning',
        'MgcSabreResolveTuning',
        'mgcDenoiseTuningSnr =',
        'mgcSharpenTuningSnr =',
        'mgcSharpenAttenuationScale =',
    ):
        if forbidden in s: raise AssertionError('26517 released owner unexpectedly contains '+forbidden)
    if s.count(ANCHOR) != 1:
        raise AssertionError(f'c4ff result ABI anchor count={s.count(ANCHOR)}')
    out=s.replace(ANCHOR,REPLACEMENT,1)
    if out.count('mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr') != 1:
        raise AssertionError('denoise tuning-SNR export cardinality')
    if out.count('mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr') != 1:
        raise AssertionError('sharpen tuning-SNR export cardinality')
    if 'mgcSharpenAttenuationScale =' in out:
        raise AssertionError('forbidden synthesized sharpen attenuation')
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--patch-out',required=True,type=Path)
    ap.add_argument('--patch-sha-out',required=True,type=Path)
    ns=ap.parse_args(); base=ns.root.resolve(); p=base/STACKER
    if not p.is_file(): raise AssertionError('missing released 26517 stacker')
    old=p.read_text(); new=expected_text(old)
    diff=''.join(difflib.unified_diff(old.replace('\r\n','\n').splitlines(True),new.splitlines(True),fromfile='a/'+STACKER,tofile='b/'+STACKER))
    if not diff: raise AssertionError('empty 26518 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True)
    ns.patch_out.write_text(diff)
    digest=sha_bytes(ns.patch_out.read_bytes())
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    # Patch exists before the runtime write.
    p.write_text(new)
    print('PASS: 26518 ABI adapter exports exact c4ff referenceSnr into newer result fields only')

if __name__=='__main__': main()
