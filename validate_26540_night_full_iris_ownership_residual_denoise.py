#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNTIME=[x.strip() for x in (HERE/'26540_RUNTIME_FILES.txt').read_text().splitlines() if x.strip()]

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root:Path):
    d={}
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file(): d[str(p.relative_to(root))]=sha(p)
    return d

def need(s:str,*xs:str):
    for x in xs:
        if x not in s: raise SystemExit('missing required 26540 contract: '+x)
def forbid(s:str,*xs:str):
    for x in xs:
        if x in s: raise SystemExit('forbidden 26540 contract survived: '+x)

def strip_comments(s:str)->str:
    s=re.sub(r'/\*.*?\*/','',s,flags=re.S)
    s=re.sub(r'//.*','',s)
    return s

def validate(base:Path,cand:Path):
    mb,mc=manifest(base),manifest(cand)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    if changed!=sorted(RUNTIME): raise SystemExit('26540 changed-file allowlist mismatch: '+repr(changed))
    if len(changed)!=18: raise SystemExit('26540 V1.1 runtime count is not 18')
    if sum(k not in mb for k in changed)!=2: raise SystemExit('26540 expected exactly two new runtime files')
    vp=(cand/'app/version.properties').read_text()
    if 'VERSION_BUILD=26539' not in vp and 'VERSION_BUILD=26540' not in vp: raise SystemExit('candidate build pin unexpected')

    def read(rel): return (cand/rel).read_text(errors='strict')
    cap=read('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    batch=read('app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java')
    proc=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
    imageFrame=read('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java')
    cfa=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    hdr=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    pars=read('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
    post=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    node=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/nodes/Node.java')
    glbase=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLBasePipeline.java')
    settings=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java')
    bridge=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    stacker=read('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    legacyFrameSel=read('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java')
    frameSel=read('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
    expoSel=read('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java')

    need(batch,'IRIS_26540_NIGHT_IMMUTABLE_BATCH_OWNER','CameraCharacteristics characteristics','exact metadata missing timestamp')
    need(cap,'IRIS_26540_NIGHT_CAPTURE_OWNER','copyIrisNight26540Raw','tryDispatchIrisNight26540',
         'IrisNightProcessor.process(','IrisNightExposureSelector.freezePlan(','IrisNightFrameSelector.getFrames(',
         'if (iris26533CaptureMode != CameraMode.NIGHT) SaverImplementation.IMAGE_BUFFER.clear();',
         'if (iris26533CaptureMode != CameraMode.NIGHT) Camera2ApiAutoFix.applyEnergySaving();',
         'if (iris26533CaptureMode != CameraMode.NIGHT) Camera2ApiAutoFix.ApplyBurst();',
         'mImageSaver = null;','IRIS_26540_NIGHT_SEQUENCE_COMPLETE','legacySaverWait=false')
    # Night callback must intercept before generic saver callback.
    if cap.index('if (mIrisNight26540CaptureActive)') >= cap.index('mImageSaver.initProcess(reader)',cap.index('if (mIrisNight26540CaptureActive)')):
        raise SystemExit('Night RAW ownership does not precede generic saver')
    # Night sequence-complete block must return before legacy runRaw block.
    seq=cap.index('if (iris26533CaptureMode == CameraMode.NIGHT)',cap.index('onCaptureSequenceCompleted'))
    ret=cap.index('return;',seq); run=cap.index('mImageSaver.runRaw',seq)
    if ret>=run: raise SystemExit('Night does not return before legacy runRaw')

    need(proc,'IRIS_26540_NIGHT_PROCESSOR_SOLE_OWNER','FillIrisNightParameters(',
         'IRIS_26540_NIGHT_DIRECT_PROCESS_ENTRY','PhotonMotionMgc1271Bridge.reconstruct(',
         'IRIS_26540_NIGHT_RGBA16F_RELEASED_BEFORE_JIN','IRIS_26540_NIGHT_PUBLICATION_OWNERSHIP',
         'baseSurvivesJinFailure=true','autoLowLightLumaFloor=false')
    code=strip_comments(proc)
    for bad in ['GenerateExpoPair(','IsoExpoSelector.setExpo(','SaverImplementation.','DefaultSaver.','Camera2ApiAutoFix.',
                'FillDynamicParameters(','new NoiseModeler(','PyramidMerging(','ExposureFusion','AutoExposure','ESD3D2']:
        if bad in code: raise SystemExit('active legacy execution in IrisNightProcessor: '+bad)
    forbid(code,'IsoExpoSelector','ExpoPair')
    need(proc,'frame.pair = null;','frame.irisRelativeExposureMpy = 1.0f;')
    need(imageFrame,'IRIS_26540_NEUTRAL_RELATIVE_EXPOSURE_OWNER','irisRelativeExposureMpy','getRelativeExposureMpy()')
    need(cfa,'images.get(0).getRelativeExposureMpy()','frame.getRelativeExposureMpy()')

    need(hdr,'IRIS_26540_NIGHT_HDRX_ENTRY_FORBIDDEN')
    need(pars,'IRIS_26540_NIGHT_CAMERA2_PARAMETER_OWNER','FillIrisNightParameters(',
         'photonNoiseModeler=false tunableInjector=false','sensorSpecificOverrides=false customCct=false',
         'Byte ref2Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);',
         'int ref2 = ref2Obj == null ? ref1 : (ref2Obj & 0xff);')
    forbid(pars,'Integer ref2Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);')
    need(post,'IRIS_26540_NIGHT_POST_CONSTRUCTOR','IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION',
         'Log.i("PostPipeline", "IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION')
    need(node,'IRIS_26540_NIGHT_NO_NODE_TUNABLE_INJECTION')
    need(glbase,'IRIS_26540_NIGHT_NO_LEGACY_TUNING_FILE')
    need(settings,'IRIS_26540_NIGHT_EXACT_CAMERA2_NOISE_SNAPSHOT','exactCamera2NightSnapshot()')
    need(legacyFrameSel,'IRIS_26540_V11_NIGHT_FRAME_BUDGET_NOT_OWNED_HERE')
    forbid(strip_comments(legacyFrameSel),'IrisNightFrameSelector.getFrames()')
    need(frameSel,'IRIS_26540_NIGHT_FRAME_BUDGET_OWNER')
    forbid(strip_comments(frameSel),'iso','ISO','preview')
    need(expoSel,'IRIS_26540_NIGHT_EXPOSURE_SOLE_OWNER')
    forbid(strip_comments(expoSel),'GenerateExpoPair(','IsoExpoSelector.')

    need(stacker,'IRIS_26540_PECAN_PROFILE_SNR_AUTHORITY','mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr')
    need(bridge,'IRIS_26540_RESIDUAL_ONLY_DENOISE_AUTHORITY','automaticLowLightLuma=0.0',
         'profileSnrSource=referencePreMerge','residualMagnitude=propagatedReadShotCorrelationStrength',
         'isoStrengthAuthority=false darknessStrengthAuthority=false')
    forbid(bridge,'IRIS_26539_AUTOMATIC_PECAN_LUMA_FLOOR','val automaticLowLightLuma =','val lowLightDemand =')

    # Core inherited Motion ownership files are outside the changed allowlist.
    for rel in [
      'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Alignment.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java']:
        if mb.get(rel)!=mc.get(rel): raise SystemExit('protected Motion owner changed: '+rel)

    print('PASS: 26540 V1.1 exact 18-file scope + Iris Night ownership + residual-only denoise + compile-correction contracts')

def self_test():
    assert strip_comments('a/*x*/b//y\nc')=='ab\nc'
    assert len(RUNTIME)==18
    print('PASS: 26540 V1.1 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.base or not a.candidate: ap.error('--base and --candidate required')
        validate(Path(a.base).resolve(),Path(a.candidate).resolve())
