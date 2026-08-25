#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXPECTED=[x.strip() for x in (HERE/'26537_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]

def h(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def app_manifest(root:Path):
    d={}
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file(): d[str(p.relative_to(root))]=h(p)
    return d

def need(text:str, token:str, name:str):
    if token not in text: raise SystemExit(f'26537 contract missing {name}: {token}')
def forbid(text:str, token:str, name:str):
    if token in text: raise SystemExit(f'26537 forbidden {name}: {token}')

def validate(base:Path,cand:Path):
    mb,mc=app_manifest(base),app_manifest(cand)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    if changed!=EXPECTED: raise SystemExit('26537 changed-file allowlist mismatch: '+repr(changed))

    saver=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
    night=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
    render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    jin=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java').read_text()
    bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    contracts=(cand/'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt').read_text()
    stacker=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()

    # Night production remains shared MGC Spatial-RGB, with no legacy Photon Night graph.
    need(night,'PhotonMotionMgc1271Bridge.reconstruct(','shared MGC Spatial-RGB production')
    need(night,'IRIS_26537_NIGHT_DNG_RELEASED_BEFORE_JIN','DNG release before Jin')
    need(night,'IRIS_26537_NIGHT_DNG_SAVE_FAILED_CONTINUE_JPEG','DNG failure isolation from JPEG')
    need(night,'dngFailureDoesNotBlockJpeg=true','DNG failure cannot suppress Night JPEG')
    need(night,'IRIS_26537_NIGHT_RGB_CARRIER_RELEASED_BEFORE_JIN','RGB carrier release before Jin')
    need(night,'img=IrisNightNeuralEnhancer.enhanceInPlace(img);','Jin after resource release')
    need(night,'IRIS_26537_NIGHT_PUBLICATION_FALLBACK','encoding-only publication fallback')
    need(night,'sameCompletedMgcOrJinBitmap=true processingFallback=false','same-image publication guarantee')
    need(night,'saveBitmapAsJPGIrisNightPlain','Night-specific plain-JPEG publication fallback')
    marker='public static boolean saveBitmapAsJPGIrisNightPlain'
    start=saver.index(marker); end=saver.index('/** IRIS_26432_MOTION_V2_DIRECT_GAINMAP_JPEG */',start)
    plain=saver[start:end]
    need(plain,'Bitmap.CompressFormat.JPEG','plain Android JPEG encoder')
    forbid(plain,'UltraHdrSaver','synthetic Photon UltraHDR in Night fallback')
    need(post,'if(mParameters.irisNightActive){','dedicated Night post graph')
    block=post[post.index('if(mParameters.irisNightActive){'):post.index('/* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */')]
    for token in ('ExposureFusion','ESD3D','AutoExposure','new Initial(','Pyramid','DemosaicQUAD','Demosaic3','MotionV2ViewfinderExposureMatcher'):
        forbid(block,token,'legacy/incorrect Night post node')
    for token in ('MotionV2CfaInput','MotionV2MgcSourceExposure','MotionV2ColorTransform','MotionV2DisplayExposure','MotionV2Render'):
        need(block,token,'Iris Night shared primitive')

    # No pre-Jin Night UltraHDR; Motion retains its own gainmap condition.
    need(render,'IRIS_26537_NIGHT_ULTRAHDR_DEFERRED','Night UHDR deferral')
    need(render,'if (basePipeline.mParameters.motionV2Active','Motion-only gainmap creation')
    need(post,'26537 Night pre-Jin UltraHDR gain map is forbidden','pre-Jin UHDR hard guard')
    need(night,'26537 Night bitmap carried pre-Jin UltraHDR gain map','Night bitmap gainmap hard guard')

    # Jin: pinned LOL model, CPU-only, path-backed, no giant Java model byte array/NNAPI.
    need(jin,'MODEL_BYTES=42571162L','pinned model byte size')
    need(jin,'iris_night_jin_lol_512_bb7f911a.onnx','versioned model filename')
    need(jin,'env.createSession(model.getAbsolutePath(),opts)','path-backed ORT session')
    need(jin,'opts.setMemoryPatternOptimization(false)','ORT memory-pattern disable')
    need(jin,'opts.setCPUArenaAllocator(false)','ORT CPU arena disable')
    need(jin,'IRIS_26537_JIN_ENTRY','pre-session telemetry')
    forbid(jin,'opts.addNnapi(','NNAPI execution')
    forbid(jin,'import java.io.ByteArrayOutputStream;','whole-model Java byte-stream import')
    forbid(jin,'new ByteArrayOutputStream','whole-model Java byte-stream construction')
    forbid(jin,'modelBytes','whole-model Java byte array')
    forbid(jin,'createSession(modelBytes','byte-array ORT session')

    # Luma activation uses pre-merge source evidence; denoiser tuning remains propagated output SNR.
    need(contracts,'val mgcReferenceSnr: Float? = null','reference-SNR contract')
    need(stacker,'mgcReferenceSnr = bayerKernelTuning.referenceSnr','reference-SNR producer')
    need(stacker,'mgcDenoiseTuningSnr = finishRawDenoiseSnr','propagated denoise-SNR producer')
    need(bridge,'val referenceSnr = stacked.mgcReferenceSnr','reference-SNR consumer')
    need(bridge,'val noiseEquivalentSupport = stacked.normalStackedDngNoiseEquivalentSupport','effective-support consumer')
    need(bridge,'val lumaSnrRisk = ((24f - referenceSnr!!) / 20f)','source-SNR activation')
    need(bridge,'val lumaSupportRisk = ((7f - noiseEquivalentSupport) / 5f)','support activation')
    need(bridge,'tuningSnr = tuningSnr!!','propagated denoise tuning retained')
    need(bridge,'textureClassifier=false','no flat-area classifier')
    need(bridge,'propagatedDenoiseTuningSnr=$tuningSnr','domain telemetry')

    # Existing no-fallback invariants remain explicit in Night/Jin telemetry.
    for token in ('photonFallback=false','adrcFallback=false','singleFrameFallback=false'):
        need(jin,token,'no old Photon/ADRC/single-frame fallback')

    print('PASS: 26537 architecture contracts: dedicated Night lifecycle + file-backed CPU Jin + source-SNR/effective-support luma')
    print('PASS: 26537 no old Photon Night / ADRC / single-frame reconstruction fallback')
    print('PASS: 26537 exact changed files='+str(len(changed)))

def self_test():
    assert len(EXPECTED)==8 and EXPECTED==sorted(EXPECTED), EXPECTED
    assert len(set(EXPECTED))==len(EXPECTED)
    print('PASS: 26537 validator self-test inventory and contracts loaded')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base')
    ap.add_argument('--candidate')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test: self_test(); return
    if not args.base or not args.candidate: ap.error('--base and --candidate required')
    validate(Path(args.base).resolve(),Path(args.candidate).resolve())
if __name__=='__main__': main()
