#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re

EXPECTED={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/version.properties',
}
PROTECTED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
]
BASE_MANIFEST_SHA='2a9f76220aaf6a1b1f863d1e693d6575d1abde6cfbb4a5d2a524d7053f3316ae'
CAND_MANIFEST_SHA='93157b96250eecca785695ba21de71ab3d52e0434b16c5f22bddc2afb8714325'
VENDOR_SHA='7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'
GLSL_SHA={
'directionalSmooth.comp':'1c15b1416634e1bdbf240d517da21755a48eef478ef6faa00659c79b0cd5196f',
'iirRgb.comp':'21e50a29703019bdd90b30423308b7778b77576e2e7b3d2b4c634a56fff375d1',
}

def must(c,m):
    if not c: raise SystemExit('FAIL: '+m)
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def changed(a,b):
    paths={p.relative_to(a) for p in a.rglob('*') if p.is_file()}|{p.relative_to(b) for p in b.rglob('*') if p.is_file()}
    return {str(r) for r in paths if not (a/r).exists() or not (b/r).exists() or (a/r).read_bytes()!=(b/r).read_bytes()}
def between(t,a,b):
    i=t.index(a); j=t.index(b,i); return t[i:j+len(b)]

def delivered_ok(req_s,req_l,act_s,act_l):
    return req_s>=2 and req_l>=0 and act_s>=2 and act_l>=0 and act_s<=req_s and act_l<=req_l

def self_test():
    must(delivered_ok(40,10,39,0),'Tundra 50->39 exact-short degradation must be accepted')
    must(delivered_ok(26,6,25,0),'Tundra 32->25 exact-short degradation must be accepted')
    must(delivered_ok(12,3,11,2),'arbitrary partial short/long set must be accepted')
    must(not delivered_ok(12,3,1,3),'single-short fallback must be rejected')
    must(not delivered_ok(12,3,13,0),'fabricated/excess short roles must be rejected')
    must(not delivered_ok(12,3,12,4),'fabricated/excess long roles must be rejected')
    print('PASS validator self-test: exact Tundra 39/50 and 25/32 regressions')

def validate(base,cand,base_manifest=None,cand_manifest=None,vendor_manifest=None,glsl_dir=None):
    delta=changed(base,cand)
    must(delta==EXPECTED,'exact five-file scope mismatch '+repr(sorted(delta^EXPECTED)))
    print('PASS exact 5-file runtime scope')
    for r in PROTECTED:
        must((base/r).read_bytes()==(cand/r).read_bytes(),'protected byte drift '+r)
    print('PASS protected exposure/frame/Sabre/VGN/Jin-implementation/UHDR bytes unchanged')

    cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    bcc=(base/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    for x in ['IRIS_26554_NIGHT_HAL_QUEUE_DRAIN_OWNER','drainIrisNight26554AvailableRawImages(reader, "image-callback")',
              'drainIrisNight26554AvailableRawImages(mImageReaderRaw, "sequence-grace")',
              'while (mIrisNight26540CaptureActive && generation == mIrisNight26544CaptureGeneration)',
              'reader.acquireNextImage()','IRIS_26554_NIGHT_SEQUENCE_DRAIN_GRACE',
              'Math.min(5000L, 750L + exposureMs)','IRIS_26554_NIGHT_ACTUAL_DELIVERED_SET']:
        must(x in cc,'RAW recovery contract '+x)
    # Exact request routing, tags and exposure policy stay byte-identical: no device-specific Long-target patch.
    a='if (iris26533CaptureMode != CameraMode.NIGHT) Camera2ApiAutoFix.applyEnergySaving();'
    b='PhotonCamera.getGyro().PrepareGyroBurst(times, BurstShakiness);'
    must(between(cc,a,b)==between(bcc,a,b),'Night Short/Long request/exposure/RAW-target construction changed')
    drain_body=between(cc,'private int drainIrisNight26554AvailableRawImages','private long irisNight26554SequenceDrainGraceMs')
    must('Build.MANUFACTURER' not in drain_body and 'Build.BRAND' not in drain_body and 'Build.MODEL' not in drain_body,
         'device-specific Night drain gate introduced')
    print('PASS universal HAL queue drain; Night request/exposure routing byte-identical')

    nb=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java').read_text()
    must('public final boolean degradedBracket;' in nb,'degraded bracket provenance')
    must('shortCount > requestedShortFrames || longCount > requestedLongFrames' in nb,'actual roles bounded by request')
    must('shortCount + longCount != frameBudget' in nb,'actual role total contract')
    must('shortCount != requestedShortFrames || longCount != requestedLongFrames' not in nb[nb.index('if (shortCount < 2'):nb.index('final double referenceEnergy')],
         'old exact-request role equality survived')
    must('shortCount < 2' in nb,'minimum two exact Shorts lost')
    print('PASS requested-vs-actual immutable Night role ownership; no fabricated/single-frame fallback')

    np=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text()
    must('IrisNightNeuralEnhancer.enhanceInPlace' not in np,'active Jin RGB-grid call survived')
    must('IRIS_26554_NIGHT_JIN_RGB_GRID_BYPASS' in np,'universal Jin bypass marker')
    base_block=between(np,'NIGHT_BASE_JPEG_BEGIN','NIGHT_JIN_RGB_GRID_BYPASS')
    must('notifyImageSavedStatus' not in base_block,'base checkpoint still publishes thumbnail')
    final_block=between(np,'NIGHT_FINAL_JPEG_BEGIN','NIGHT_PROCESS_FINISHED_NOTIFY_BEGIN')
    must(final_block.count('listener.notifyImageSavedStatus(imageSaved, imageFile);')==1,'final image publication must occur exactly once')
    for x in ['IRIS_26554_NIGHT_BASE_JPEG_CHECKPOINT_ONLY','IRIS_26554_NIGHT_SINGLE_PUBLICATION_OWNER',
              'finalSdrAuthority=postPipelineJinBypassed','jinRgbGridApplied=false','degradedBracket=']:
        must(x in np,'Night publication/Jin contract '+x)
    must('IrisNightUltraHdr.attachPostJin(' in np,'UHDR final attachment removed')
    print('PASS Jin square/pink source bypass; Sabre/VGN/PostPipeline/UHDR retained; base thumbnail not premature')

    ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text()
    sw=between(ui,'private void switchToMode(CameraMode cameraMode)','iris26551AdvanceProgressUiGeneration')
    must('CaptureController.isProcessing' in sw,'processing guard missing')
    must('mModePicker.collapseToIndex(indexOfMode(previousMode));' in sw,'picker rollback missing')
    must('Please wait until processing is completed.' in sw,'wait message missing')
    must(sw.index('CaptureController.isProcessing') < sw.index('displayedMode = cameraMode;'),'guard occurs after mode ownership mutation')
    print('PASS processing-mode transition guard before ownership mutation')

    vp=(cand/'app/version.properties').read_text()
    must('VERSION_NAME=0.9726554' in vp and 'VERSION_BUILD=26554' in vp,'target version/build')
    if base_manifest:
        must(sum(1 for _ in open(base_manifest))==970 and h(base_manifest)==BASE_MANIFEST_SHA,'base 970 manifest')
    if cand_manifest:
        must(sum(1 for _ in open(cand_manifest))==970 and h(cand_manifest)==CAND_MANIFEST_SHA,'candidate 970 manifest')
    if vendor_manifest:
        must(sum(1 for _ in open(vendor_manifest))==778 and h(vendor_manifest)==VENDOR_SHA,'vendor 778 manifest')
    if glsl_dir:
        for f,sha in GLSL_SHA.items(): must(h(Path(glsl_dir)/f)==sha,'protected runtime GLSL '+f)
    print('PASS version/manifests/protected runtime GLSL pins')
    print('PASS 26554 focused high-risk Night ownership validation')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true')
    ap.add_argument('base',nargs='?',type=Path); ap.add_argument('candidate',nargs='?',type=Path)
    ap.add_argument('--base-manifest'); ap.add_argument('--candidate-manifest'); ap.add_argument('--vendor-manifest'); ap.add_argument('--glsl-dir')
    a=ap.parse_args()
    if a.self_test: self_test(); return
    must(a.base and a.candidate,'base/candidate required')
    validate(a.base,a.candidate,a.base_manifest,a.candidate_manifest,a.vendor_manifest,a.glsl_dir)
if __name__=='__main__': main()
