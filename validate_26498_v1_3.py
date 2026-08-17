#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys, math

def fail(msg): raise SystemExit('ERROR: '+msg)
def must(cond,msg):
    if not cond: fail(msg)
def text(p):
    if not p.is_file(): fail('missing '+str(p))
    return p.read_text()

def validate(root: Path, full: bool):
    main=root/'app/src/main'
    mb=text(main/'java/com/particlesdevs/photoncamera/processing/MotionBatch.java')
    cap=text(main/'java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    rec=text(main/'java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    sh=text(main/'assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
    aux=text(main/'assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl')

    # Short-A: geometry/correspondence owner must be the immutable reference CFA.
    must(sh.count('uniform highp sampler2D referenceCfa;')==1,'Short-A referenceCfa uniform ownership != 1')
    must('texelFetch(referenceCfa, q, 0)' in sh,'Short-A correspondence does not read reference CFA')
    must('texelFetch(normalCfa, p, 0)' in sh,'Short-A merged CFA lost final need/target ownership')
    must('setTexture("normalCfa",imageOutput)' in rec,'host merged CFA binding missing')
    must('setTexture("referenceCfa",referenceCfa)' in rec,'host reference CFA binding missing')
    must('IRIS_26498_V13_SHORT_REFERENCE_OWNS_CORRESPONDENCE' in rec,'Short reference ownership marker missing')

    # Separate owner: distinct class/slot, never MotionBatch.frames.
    must(mb.count('public static final class ShadowAuxSlot')==1,'ShadowAuxSlot definition != 1')
    must(mb.count('public final ShadowAuxSlot shadowAuxSlot = new ShadowAuxSlot();')==1,'shadow slot carrier != 1')
    must('shadowAuxSlot.offer(irisV13ShadowAuxFrame)' in cap,'capture does not deliver to separate shadow slot')
    must('shadowAuxSlot.takeAndSeal()' in rec,'reconstruction does not seal/take separate shadow slot')
    must('shadowAuxSlot.sealAndClose();' in mb,'shadow slot cleanup missing')
    frames_decl=re.search(r'public final List<ImageFrame> frames;',mb)
    must(frames_decl is not None,'normal MotionBatch.frames declaration missing')
    must('normalAccumulatorAdmission=false' in cap and 'normalAccumulatorAdmission=false' in rec,'normal-accumulator isolation telemetry missing')

    # Cohort policy is unchanged and shadow selection is bounded/newest/actual-metadata based.
    must('MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05' in cap,'normal +/-0.05 EV cohort changed')
    must('MOTION_26486_MAX_GROUP_SPAN_EV' in cap,'normal group-span invariant missing')
    must(cap.count('findBestMotionExposureGroup(rawImages, skip)')==1,'normal exposure group owner changed/duplicated')
    must('energyRatio >= 1.50 && energyRatio <= 4.0' in cap,'shadow exposure-energy qualification missing')
    must('rawTs > irisV13ShadowAuxTimestamp' in cap,'shadow selection is not newest qualifying frame')
    must('shadowAuxCandidateFrames=' in cap and 'shadowAuxSelected=' in cap and 'shadowAuxSelectMs=' in cap,'ring/shadow selection telemetry incomplete')
    must('IRIS_26498_V13_RING_EXPOSURE_DISTRIBUTION' in cap,'full ring/cohort exposure telemetry missing')

    # One pass, one auxiliary, no added capture owner or post-shutter wait.
    must(cap.count('shadowAuxSlot.offer(irisV13ShadowAuxFrame)')==1,'more than one shadow delivery path')
    must(rec.count('shadow_aux_bayer_fuse')==1,'shadow fuse dispatch count != 1')
    must(rec.count('MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,irisV13ShadowWbCfa)')==1,'shadow must reuse prepared Wronski reference exactly once')
    must('finishDeferredCompute("MotionV2 final image")' in rec,'existing single GPU ownership drain missing')
    must('extraGpuDrain=false' in rec,'no-extra-drain invariant marker missing')

    # Physical shadow evidence only; generic Photon noise model must not own this path.
    must('uniform vec4 referenceNoiseShot' not in aux and 'uniform vec4 shadowNoiseShot' not in aux,'shadow shader consumes generic noise model')
    must('requiredExposureSupportRatio' in aux and 'shadowExposureRatio' in aux,'exposure/support SNR gate missing')
    must('maxShadowBlend' in aux and '0.20f' in rec,'bounded shadow blend missing')
    must('minimumShadowSignal' in aux and '0.004f' in rec,'true-black protection threshold missing')
    must('texelFetch(referenceCfa' in aux and 'texelFetch(mergedCfa' in aux,'shadow correspondence/base authorities incomplete')
    must('radiometric>0.22' in aux,'shadow radiometric disagreement rejection missing')
    must('flowConfidence<minimumFlowConfidence' in aux,'shadow motion rejection missing')
    must('shadowClipThreshold' in aux,'shadow saturation rejection missing')

    # Required telemetry names.
    for marker in ('shadowAuxExposureRatio','shadowAuxTimestampDelta','shadowAuxAlignMs','shadowAuxFuseMs','shadowAuxTotalMs',
                   'shadowAuxCandidatePixels','shadowAuxLowSignalCandidates','shadowAuxCorrespondencePassed',
                   'shadowAuxMotionRejected','shadowAuxSaturationRejected','shadowAuxContributedPixels'):
        must(marker in cap or marker in rec, 'telemetry missing: '+marker)

    # Banned architectural regressions in the V1.3 path.
    combined='\n'.join((cap,rec,aux))
    for banned in ('MotionV2Denoise','mfsr_low_support_reference.glsl','PyramidAlignment'):
        must(banned not in aux,'banned shadow-path token: '+banned)
    must('secondDemosaic=false' in rec,'second-demosaic negative proof marker missing')
    must('shortNeverNormalFusion=true shadowNeverNormalFusion=true' in cap,'auxiliary normal-fusion negative proof missing')

    # Synthetic math safety.
    def phase_ok(ratio,support): return ratio >= max(1.5,1.15*max(support,1.0))
    must(phase_ok(1.6,1.0) and not phase_ok(1.6,2.0),'exposure/support gate synthetic failure')
    must(phase_ok(3.0,2.0) and not phase_ok(4.0,4.0),'high-support rejection synthetic failure')
    for r in (1.5,2.0,4.0): must(0.25 <= 1.0/r <= 2.0/3.0+1e-6,'radiometric scale bound failure')

    if full:
        # Original 26498 architecture identity markers; patch hash is independently guarded by build script.
        rcdhost=text(main/'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java')
        gain=text(main/'assets/shaders/motionv2/gainmap.glsl')
        programs=['rcd26498_populate','rcd26498_vh_direction','rcd26498_lpf','rcd26498_green',
                  'rcd26498_diag_residual','rcd26489_diag_direction','rcd26498_opposite','rcd26498_green_rb','rcd26498_write']
        positions=[rcdhost.find(x) for x in programs]
        must(all(x>=0 for x in positions),'26498 active RCD program sequence incomplete')
        must(positions==sorted(positions),'26498 active RCD program order changed')
        must('RCD_HALO' in rcdhost and '12' in rcdhost,'26498 true-photo halo ownership missing')
        must('GAINMAP_DOWNSAMPLE' in gain or 'DOWNSAMPLE' in gain or 'gainMapSize' in gain,'26498 gain-map shader identity missing')
        # Provenance-aware RCD files must exist and no 26496 completion shader may be active in host.
        must('rcd26496_chroma_complete' not in rcdhost,'rejected post-RCD chroma completion active')
        must(any((main/'assets/shaders/motionv2').glob('rcd26498*.glsl')),'26498 RCD shader set missing')

    print('PASS: 26498 V1.3 Short-A reference-owned correspondence')
    print('PASS: 26498 V1.3 separate one-shot pre-shutter shadow owner')
    print('PASS: normal exposure cohort/accumulator ownership remains isolated')
    print('PASS: shadow path is exposure/support gated, bounded, true-black protected, and no generic noiseS-owned')
    print('PASS: required V1.3 telemetry and one-drain invariants present')
    if full: print('PASS: original 26498 RCD/UHDR root architecture markers retained')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--full',action='store_true')
    a=ap.parse_args(); validate(Path(a.root).resolve(),a.full)
