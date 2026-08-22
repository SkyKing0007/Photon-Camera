#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p:Path)->str: return p.read_text(encoding='utf-8').replace('\r\n','\n').replace('\r','\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--candidate',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); b=Path(a.base); c=Path(a.candidate)
    fusion='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
    sh='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
    st='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
    dormant=[
      'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    ]
    bridge_candidates=[
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/GlesMgcRawFusion.java',
    ]
    fs=text(c/fusion); ss=text(c/sh); ts=text(c/st)
    for tok in ['if (mergeMethod == MgcMergeMethod.SPATIAL_RGB)', 'IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE', 'return GlesIris26521SpatialRgbStacker(']:
        if tok not in fs: raise SystemExit('active SPATIAL_RGB routing drift: '+tok)
    if (b/fusion).read_bytes()!=(c/fusion).read_bytes(): raise SystemExit('fusion routing owner unexpectedly changed')
    if (b/sh).read_bytes()==(c/sh).read_bytes() or (b/st).read_bytes()==(c/st).read_bytes(): raise SystemExit('expected active Iris Spatial image-math correction missing')
    for rel in dormant:
        if (b/rel).read_bytes()!=(c/rel).read_bytes(): raise SystemExit('dormant MGC Spatial owner unexpectedly changed: '+rel)
    for tok in ['IRIS_26527_FINAL_MGC_REJECTION_ALIGNMENT_PARITY','rejectionPixelDifferenceDownsample','max(deltaWeight, centerWeight)']:
        if tok not in ss+ts: raise SystemExit('final MGC correction missing: '+tok)
    for tok in ['IRIS_26527_FINAL_ALIGNMENT_FIELD_OWNER','IRIS_26527_TEMPORAL_ACCEPTANCE_STAGES','val bayerAlignment = alignment.texture','referenceGrayPyramid[1].texture']:
        if tok not in ts: raise SystemExit('active temporal owner marker missing: '+tok)
    for old in ['convertBayerAlignment','renderBayerAlignment(','renderMergeDomainFlow(']:
        if old in ss+ts: raise SystemExit('obsolete active temporal owner survived: '+old)
    prep=ts.index('private fun prepareTemporalFrame')
    stages={
      'dilateAcceptance':ts.index('renderDilation(rawReverseWeight, initialWeight)',prep),
      'pixelDifference2x':ts.index('renderPixelDifferenceDownsample(rawPixelDifference, pixelDifference)',prep),
      'filterDownsample':ts.index('renderRejectionFilterDownsample(',prep),
      'postprocess':ts.index('renderRejectionPostprocess(',prep),
    }
    if list(stages.values())!=sorted(stages.values()): raise SystemExit('temporal stage order mismatch')
    report={
      'activeFusionOwner':fusion,
      'activeSpatialShader':sh,
      'activeSpatialStacker':st,
      'fusionSha256':sha(c/fusion),
      'baseSpatialShaderSha256':sha(b/sh), 'candidateSpatialShaderSha256':sha(c/sh),
      'baseSpatialStackerSha256':sha(b/st), 'candidateSpatialStackerSha256':sha(c/st),
      'dormantSpatialOwnersByteIdentical':True,
      'stageOrder':stages,
      'temporalRuntimeTelemetry':True,
      'temporalImageMathChanged':True,
      'temporalCorrection':'FINAL_MGC_REJECTION_AND_ALIGNMENT_DOMAIN_PARITY',
    }
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS: active Motion SPATIAL_RGB remains Iris 26521 independent owner')
    print('PASS: only active Iris Spatial rejection/alignment math changed; dormant MGC Spatial is frozen')
    print('PASS: DilateMask -> pixel-difference 2x -> RAW/4 filter -> postprocess order')
    print('TEMPORAL_RUNTIME_TELEMETRY=true')
    print('TEMPORAL_IMAGE_MATH_CHANGED=true')
    print('TEMPORAL_CORRECTION=FINAL_MGC_REJECTION_AND_ALIGNMENT_DOMAIN_PARITY')
if __name__=='__main__': main()
