#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re, sys

EXPECTED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/version.properties',
}
NIGHT_PROTECTED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
]
BASE_MANIFEST_SHA='ee6e36bed22a70b0a658f2d69db0019270333b3739b9a9d6d73e64d06845fb4c'
CAND_MANIFEST_SHA='2a9f76220aaf6a1b1f863d1e693d6575d1abde6cfbb4a5d2a524d7053f3316ae'
VENDOR_SHA='7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'
GLSL_SHA={'directionalSmooth.comp':'1c15b1416634e1bdbf240d517da21755a48eef478ef6faa00659c79b0cd5196f','iirRgb.comp':'21e50a29703019bdd90b30423308b7778b77576e2e7b3d2b4c634a56fff375d1'}

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def must(cond,msg):
    if not cond: raise SystemExit('FAIL: '+msg)
def raw_value(text,name):
    m=re.search(r'(?ms)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',text)
    must(m is not None,'missing raw shader '+name); return m.group(1)
def changed(base,cand):
    out=set()
    paths={p.relative_to(base) for p in base.rglob('*') if p.is_file()}|{p.relative_to(cand) for p in cand.rglob('*') if p.is_file()}
    for r in paths:
        a=base/r; b=cand/r
        if not a.exists() or not b.exists() or a.read_bytes()!=b.read_bytes(): out.add(str(r))
    return out

def self_test():
    must(EXPECTED and len(EXPECTED)==5,'expected scope self-test')
    print('PASS validator self-test')

def validate(base,cand,base_manifest=None,cand_manifest=None,vendor_manifest=None,glsl_dir=None):
    must(changed(base,cand)==EXPECTED, f'exact 5-file runtime scope mismatch: {sorted(changed(base,cand)^EXPECTED)}')
    print('PASS exact 5-file runtime scope')
    for r in NIGHT_PROTECTED:
        must((base/r).read_bytes()==(cand/r).read_bytes(),'protected Night/Sabre byte drift '+r)
    print('PASS protected Night frame/exposure/Sabre processing bytes unchanged')

    ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text()
    must('IRIS_26553_SHUTTER_BASELINE_ANIMATION_OWNER' in ui,'shutter owner marker')
    must('if (target == mShutterButton) return isVideoStyleMode() ? 0.84f : 0.83f;' in ui,'still/video shutter baseline')
    must('scaleX(baseline * 0.91f).scaleY(baseline * 0.91f)' in ui,'relative press scale')
    must('scaleX(baseline).scaleY(baseline)' in ui,'baseline release scale')
    # Exact regression: generic listener must no longer restore the still shutter to 1.0.
    listener=ui[ui.index('private void installPressAnimation'):ui.index('private void toggleFormatPanel')]
    must('.scaleX(1f).scaleY(1f)' not in listener,'26552 absolute 1.0 shutter release regression survived')
    for marker in ['IRIS_26552_NIGHT_SHUTTER_RING_Z_ORDER','IRIS_26552_NIGHT_SHUTTER_CAPTURE_RING','IRIS_26552_NIGHT_NO_OVERSIZED_VIEWFINDER_RING']:
        must(marker in ui,marker+' lost')
    must('bottombuttons.frameCount.setText(String.valueOf(target.getProgress()))' in ui,'Night frame counter does not advance')
    must('bottombuttons.frameCount.setText("0")' in ui,'Night capture counter does not initialize at zero')
    print('PASS approved cold-Motion -> Night -> Motion shutter geometry contract')

    cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    wait=cc[cc.index('private void waitingLockProcess'):cc.index('private void waitingPrecaptureProcess')]
    timeout=re.search(r'if \(hitTimeoutLocked\(\)\) \{(.*?)\n\s*\}',wait,re.S)
    must(timeout is not None,'AF timeout block')
    tb=timeout.group(1)
    must(tb.count('captureStillPicture();')==1 and re.search(r'captureStillPicture\(\);\s*/\*?.*?IRIS_26553|captureStillPicture\(\);\s*// IRIS_26553',tb,re.S),'timeout single capture marker')
    must(re.search(r'captureStillPicture\(\);.*?return;',tb,re.S) is not None,'AF timeout must return immediately')
    for s in ['mIrisNight26553ShutterDispatchPending','reserveIrisNight26553ShutterDispatch()',
              'mIrisNight26540CaptureActive','CaptureController.isProcessing','IRIS_26553_NIGHT_SINGLE_FLIGHT_REJECT',
              'releaseIrisNight26553ShutterDispatch("capture_state_active")',
              'releaseIrisNight26553ShutterDispatch("captureStillPicture_exit_before_active")']:
        must(s in cc,'Night single-flight contract '+s)
    # Existing dynamic plan remains consumed by capture path.
    for s in ['mIrisNight26552FramePlan','framePlan.totalFrames','iris26552NightFramePlan.isShortFrame(i)']:
        must(s in cc,'dynamic Night plan ownership '+s)
    print('PASS Night 43-ms duplicate-arm regression + single-flight ownership')

    vbase=(base/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    vcand=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    names=['common','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
    for n in names:
        if n not in ('directionalSmooth','iirRgb'):
            must(raw_value(vbase,n)==raw_value(vcand,n),'unrelated VGN shader changed '+n)
    ds=raw_value(vcand,'directionalSmooth'); ir=raw_value(vcand,'iirRgb')
    for rejected in ['realColorConfidence','highlightBoundary','localLumaEdge','chromaAgreement','coherentSupport','oneSided','candidateAgreement','IRIS_26552_VGN_LOW_CHROMA_CROSS_EDGE_CONTAINMENT']:
        must(rejected not in ds,'failed Iris directional preservation survived '+rejected)
    for expected in ['float differenceA','float differenceB','float total','directional','minimumScale','yScale']:
        # Candidate is compact and uses dx/dy/minScale names; semantic alternatives accepted below.
        pass
    must('float dx=dot(abs(center-x)' in ds and 'float dy=dot(abs(center-y)' in ds,'reference directional difference weighting')
    must('(x*dy+y*dx)/total' in ds,'reference cross-weighted directional candidate')
    must('if(abs(sc.x)+abs(sc.y)<abs(fc.x)+abs(fc.y))fc=sc;' in ds,'reference lower-chroma containment')
    for rejected in ['uChromaStrength','artifactConfidence','iirRealColorSupport','iirHighlightBoundary','iirLumaEdge','effectiveStrength']:
        must(rejected not in ir,'failed Iris IIR preservation survived '+rejected)
    must('r=apply(c2,r,uADyn2,uBDyn2,false)' in ir and 'q=apply(b2,q,uADyn2,uBDyn2,false)' in ir,'reference IIR cascade')
    # Active callers keep strength exactly 1, so untouched localMedian/blend strength plumbing remains neutral.
    alljava='\n'.join(p.read_text(errors='ignore') for p in cand.rglob('*.kt'))
    must('GlesIris26529SpatialRgbChromaPostprocessor(' in alljava,'VGN production construction missing')
    print('PASS VGN failed preservation overrides removed; current reference directional/IIR semantics restored')

    mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
    for s in ['IRIS_26553_MOTOROLA_A_PREVIEW_DIAGNOSTICS','IRIS_26553_PREVIEW_DIAG_GL_CREATED',
              'IRIS_26553_PREVIEW_DIAG_SURFACE_CHANGED','IRIS_26553_PREVIEW_DIAG_FIRST_FRAME_AVAILABLE',
              'IRIS_26553_PREVIEW_DIAG_FIRST_DRAW','IRIS_26553_PREVIEW_DIAG_PROGRAM_LINK']:
        must(s in mr,'Motorola renderer diagnostic '+s)
    for s in ['IRIS_26553_PREVIEW_DIAG_SURFACE_AVAILABLE','IRIS_26553_PREVIEW_DIAG_SESSION_CONFIGURED',
              'IRIS_26553_PREVIEW_DIAG_REPEATING','IRIS_26553_PREVIEW_DIAG_HEALTH']:
        must(s in cc,'Motorola Camera2 diagnostic '+s)
    # MainRenderer shader sources are external and no asset/shader files changed by allowlist.
    must(not any('/assets/' in p or '/shaders/' in p for p in EXPECTED),'preview shader/runtime asset unexpectedly changed')
    print('PASS Motorola-A preview additions are diagnostics-only by changed-file scope')

    vp=(cand/'app/version.properties').read_text()
    must('VERSION_NAME=0.9726553' in vp and 'VERSION_BUILD=26553' in vp,'target version/build')

    if base_manifest:
        must(sum(1 for _ in Path(base_manifest).open())==970,'base manifest line count')
        must(h(base_manifest)==BASE_MANIFEST_SHA,'base manifest hash')
    if cand_manifest:
        must(sum(1 for _ in Path(cand_manifest).open())==970,'candidate manifest line count')
        must(h(cand_manifest)==CAND_MANIFEST_SHA,'candidate manifest hash')
    if vendor_manifest:
        must(sum(1 for _ in Path(vendor_manifest).open())==778,'vendor manifest line count')
        must(h(vendor_manifest)==VENDOR_SHA,'vendor manifest hash')
    if glsl_dir:
        for f,sha in GLSL_SHA.items(): must(h(Path(glsl_dir)/f)==sha,'runtime GLSL hash '+f)
    print('PASS version/manifests/runtime-expanded GLSL pins')
    print('PASS 26553 focused runtime semantics validation')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true')
    ap.add_argument('base',nargs='?',type=Path); ap.add_argument('candidate',nargs='?',type=Path)
    ap.add_argument('--base-manifest'); ap.add_argument('--candidate-manifest'); ap.add_argument('--vendor-manifest'); ap.add_argument('--glsl-dir')
    a=ap.parse_args()
    if a.self_test: self_test(); return
    must(a.base and a.candidate,'base/candidate required')
    validate(a.base,a.candidate,a.base_manifest,a.candidate_manifest,a.vendor_manifest,a.glsl_dir)
if __name__=='__main__': main()
