#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib

RUNTIME = [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt',
]
PROTECTED = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdDemosaic.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionRcdShortChromaOverlay.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java',
'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl',
]

def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(root, rel): return (root/rel).read_text(encoding='utf-8')
def manifest(root):
    d={}
    for top in ('app/src/main','app/version.properties','app/build.gradle'):
        p=root/top
        if p.is_file(): d[top]=sha(p)
        else:
            for f in p.rglob('*'):
                if not f.is_file(): continue
                rel=str(f.relative_to(root))
                if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
                if rel.startswith('app/src/main/cpp/deps/') and rel != 'app/src/main/cpp/deps/.gitignore': continue
                d[rel]=sha(f)
    return d

def ordered(s, seq, label):
    pos=-1
    for n in seq:
        p=s.find(n,pos+1)
        req(p>=0, f'{label}: missing {n}')
        req(p>pos, f'{label}: order error {n}')
        pos=p

def validate(base,cand):
    req(base.is_dir() and cand.is_dir(),'base/candidate missing')
    mb,mc=manifest(base),manifest(cand)
    req(len(mb)==962 and len(mc)==962, f'audited file count drift base={len(mb)} candidate={len(mc)}')
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    allowed=sorted(RUNTIME + ([] if mb.get('app/version.properties')==mc.get('app/version.properties') else ['app/version.properties']))
    req(changed==allowed, f'changed-file allowlist mismatch: {changed}')
    for rel in PROTECTED:
        req((base/rel).is_file() and (cand/rel).is_file(), 'protected path missing '+rel)
        req(sha(base/rel)==sha(cand/rel), 'protected owner drift '+rel)
    req(sha(base/'app/build.gradle')==sha(cand/'app/build.gradle'),'app/build.gradle drift')
    vp=txt(cand,'app/version.properties')
    version_pre='VERSION_NAME=0.9726533' in vp and 'VERSION_BUILD=26533' in vp
    version_build='VERSION_NAME=0.9726534' in vp and 'VERSION_BUILD=26534' in vp
    req(version_pre or version_build,'unexpected version/build marker')

    hp=txt(cand,RUNTIME[2])
    pp=txt(cand,RUNTIME[1])
    nb=txt(cand,RUNTIME[3])
    cc=txt(cand,RUNTIME[0])

    # Motion production must be the already-denoised MGC Spatial-RGB carrier.
    req('IRIS_26534_MOTION_SPATIAL_RGB_PRODUCTION_AUTHORITY' in hp,'Motion Spatial-RGB authority marker missing')
    req('output = iris26409V2.raw;' in hp,'Motion JPEG carrier not sourced from MGC Result.raw')
    req('iris26480DeferredDng = iris26409V2.stackedDngRaw16;' in hp,'Motion DNG sidecar export owner drift')
    req('img=pipeline.RunMotionV2FloatCfa(output,motionV2HighlightProvenance,processingParameters);' in hp,
        'Motion production does not enter direct-RGB post route')
    req('pipeline.RunMotionV2FusedBayerRcd(' not in hp,'Motion still calls forbidden fused/DNG Bayer RCD route')
    req('output == iris26480DeferredDng' in hp,'Motion RGB/DNG anti-alias invariant missing')
    req('jpegCarrier=MGC_SPATIAL_RGB_RGBA32F' in hp and 'dngCarrier=normalized16_sidecar_separate' in hp,
        'Motion carrier telemetry contract missing')
    req('rcdBypassed=true demosaicBypassed=true' in hp,'Motion direct-RGB no-redemosaic contract missing')

    # The old RCD entry remains only as a loud architecture tripwire.
    req('IRIS_26534_FORBID_MOTION_DNG_BAYER_PRODUCTION' in pp,'Motion forbidden-RCD method guard missing')
    req('Motion JPEG cannot consume fused/DNG Bayer through RCD' in pp,'Motion fused-Bayer guard does not hard fail')
    req('IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN' in pp,'Motion post-graph detour guard missing')
    req('Motion post graph attempted forbidden Bayer/RCD detour' in pp,'Motion post detour does not hard fail')
    motion=pp[pp.find('/* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */'):]
    ordered(motion,[
        'add(new MotionV2CfaInput())',
        'add(new MotionV2MgcSourceExposure())',
        'add(new MotionV2ColorTransform())',
        'add(new MotionV2ViewfinderExposureMatcher())',
        'add(new MotionV2DisplayExposure())',
        'add(new MotionV2Render())',
        'add(new RotateWatermark(getRotation()))'], 'Motion protected Spatial-RGB presentation graph')
    req('standard Bayer Motion reached post graph without direct RGB carrier' in motion,
        'Motion standard-Bayer direct-RGB hard invariant missing')

    # Night producer and consumer must agree on true Spatial Bayer.
    for n in ('outputMode = MgcSpatialOutputMode.BAYER','mergeMethod = MgcMergeMethod.SPATIAL_BAYER',
              'exportGpuLinearRgbSource = false','stacked.bufferLayout == RawStackBufferLayout.CFA',
              'stacked.gpuLinearRgbSource == null','stacked.gpuBayerSource',
              'val output = readBayer16(resultTexture, size.x, size.y)'):
        req(n in nb,'Night Spatial-Bayer contract missing '+n)
    for bad in ('RawStackBufferLayout.LINEAR_RGB','readRgba16f(','forceOpaqueHalfAlpha(','convertHalfRgbaToFloatRgba(',
                'MgcFullResolutionDenoise','GpuLinearRgbStorage'):
        req(bad not in nb,'stale Night RGB authority survived: '+bad)
    req('IRIS_26534_NIGHT_SPATIAL_BAYER_PARITY_VALID' in nb,'Night Bayer parity marker missing')
    req('dngSidecarAsProduction=false' in nb,'Night DNG-vs-production isolation marker missing')
    req('closeAction = { if (!preserveInputFrames) frame.close() }' in nb,'Night SR input preservation contract missing')
    req('if (!preserveInputFrames || !spatialBayerHandoffSucceeded)' in nb,
        'Night failure/success input ownership guard missing')

    # Night Hdrx must always build JPEG from r.raw Bayer -> RCD -> Jin.
    req(hp.count('IrisNightMgc1271Bridge.reconstruct(')==1,'Night Bayer owner call count drift')
    req('ByteBuffer bayer=r.raw; bayer.position(0);' in hp,'Night JPEG base is not MGC Bayer Result.raw')
    req('Bitmap img=pipeline.RunIrisNightBayer(bayer,p);' in hp,'Night Bayer not handed to RCD graph')
    req('img=IrisNightNeuralEnhancer.enhanceInPlace(img);' in hp,'Night Jin stage bypassed')
    ordered(hp,[
        'IrisNightMgc1271Bridge.reconstruct(',
        'ByteBuffer bayer=r.raw; bayer.position(0);',
        'Bitmap img=pipeline.RunIrisNightBayer(bayer,p);',
        'img=IrisNightNeuralEnhancer.enhanceInPlace(img);',
        'saveBitmapAsJPGMotionV2'], 'Night production order')
    req('IRIS_26534_NIGHT_SPATIAL_BAYER_PRODUCTION_AUTHORITY' in hp,'Night production authority telemetry missing')

    # Night Super Res is secondary evidence only and cannot replace Bayer/RCD/Jin base.
    req('IRIS_26534_NIGHT_SR_SECONDARY_EVIDENCE_PASS' in hp,'Night SR secondary-pass marker missing')
    req('baseCarrierRemainsSpatialBayer=true productionRgbReplacement=false' in hp,
        'Night SR base-isolation telemetry missing')
    req('iris26534NightSrEvidence=PhotonMotionMgc1271Bridge.reconstruct(' in hp,'Night SR proven Spatial-RGB evidence pass missing')
    req('Allocator.free(iris26534NightSrEvidence.raw)' in hp,'Night SR secondary RGB carrier not explicitly freed')
    req('Allocator.free(iris26534NightSrEvidence.stackedDngRaw16)' in hp,'Night SR secondary normal DNG sidecar not explicitly freed')
    req('RunMotionV2FloatCfa(iris26534NightSrEvidence' not in hp and 'RunIrisNightBayer(iris26534NightSrEvidence' not in hp,
        'Night SR evidence incorrectly used as production JPEG carrier')
    req('IrisMotionSuperResDngWriter.write(' in hp,'Night SR DNG evidence writer missing')

    # Night post graph: RCD reconstruction is isolated; Jin is explicitly Hdrx-owned afterward.
    night_line='if(mParameters.irisNightActive){add(new IrisRcdBayerInput());add(new StageTelemetry("IRIS_NIGHT_FUSED_BAYER_INPUT"));add(new IrisRcdDemosaic());'
    req(night_line in pp,'Night post graph does not begin Bayer input -> RCD')
    req('public Bitmap RunIrisNightBayer(ByteBuffer fusedBayer, Parameters parameters)' in pp,'Night Bayer entry missing')

    # V1.6 exact metadata ownership must survive and successful session reconfiguration heals UI state.
    for n in ('IRIS_26533_V16_NIGHT_TIMESTAMP_METADATA_OWNER','prepareIrisNight26533ExactMetadata(finalFrameCount)',
              'mIrisNight26533Results.get(imageTs)','populateMotion26480FrameMetadata(frame, exact, false)'):
        req(n in cc,'V1.6 Night metadata authority lost '+n)
    req('IRIS_26534_SESSION_STATE_RECOVERY_OWNER' in cc and 'mState = STATE_PREVIEW;' in cc,
        'post-Night session/UI state recovery invariant missing')
    session=cc.find('mCaptureSession = cameraCaptureSession;')
    state=cc.find('mState = STATE_PREVIEW;',session)
    req(session>=0 and state>session and state-session<1000,'STATE_PREVIEW not reasserted at successful session configuration')

    # No new architectural bypass aliases in changed source.
    joined='\n'.join((hp,pp,nb,cc))
    for bad in ('ADRC fallback','single-frame fallback','single frame fallback'):
        req(joined.lower().count(bad.lower()) <= '\n'.join(txt(base,r) for r in RUNTIME).lower().count(bad.lower()),
            'new forbidden fallback marker '+bad)

    print('PASS: 26534 exact V1.6 lineage + 4-file routing delta')
    print('PASS: Motion=MGC Spatial-RGB production; DNG Bayer=export only; RCD re-demosaic forbidden')
    print('PASS: Night=MGC Spatial-Bayer -> RCD -> Jin; SR=secondary evidence only; CFA/RGB mismatch forbidden')
    print('PASS: Night exact metadata preserved + session state recovery installed')

def self_test():
    req(len(RUNTIME)==4 and len(set(RUNTIME))==4,'runtime allowlist must remain exactly 4')
    req(len(PROTECTED)==len(set(PROTECTED)),'protected list duplicate')
    print('PASS: 26534 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        req(a.base and a.candidate,'--base and --candidate required')
        validate(Path(a.base),Path(a.candidate))
