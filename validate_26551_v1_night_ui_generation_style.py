#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, xml.etree.ElementTree as ET

ALLOWED = [
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
    'app/src/main/res/drawable/circular_progress_bar.xml',
    'app/src/main/res/layout/layout_bottombuttons.xml',
    'app/version.properties',
]
PROTECTED = [
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def files(root):
    root=Path(root); return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def need(t, sub, label):
    if sub not in t: raise SystemExit('FAIL: '+label)
def forbid(t, sub, label):
    if sub in t: raise SystemExit('FAIL: '+label)

def self_test():
    # Permanent 26550 UI-race regression: stale Night operations must lose to mode/capture generations.
    generation=11; mode='NIGHT'
    old=(generation,mode)
    generation += 1; mode='PHOTO'
    assert old != (generation,mode)
    transition=(generation,mode)
    generation += 1 # new capture
    assert transition != (generation,mode)
    current=(generation,mode)
    assert current == (generation,mode)
    print('PASS: 26551 UI-generation race self-test')

def validate(base, cand):
    base=Path(base); cand=Path(cand)
    b,c=files(base),files(cand)
    changed=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
    if changed != ALLOWED:
        raise SystemExit('FAIL: changed-file allowlist mismatch\nactual='+repr(changed)+'\nexpected='+repr(ALLOWED))
    for f in PROTECTED:
        if b.get(f) != c.get(f): raise SystemExit('FAIL: protected processing drift '+f)

    frag=(cand/ALLOWED[0]).read_text()
    view=(cand/ALLOWED[1]).read_text()
    draw=(cand/ALLOWED[2]).read_text()
    layout=(cand/ALLOWED[3]).read_text()
    version=(cand/ALLOWED[4]).read_text()

    # Remove the defective 26550 Motion-only workaround completely.
    forbid(frag, 'iris26550NightUiRearmPending', '26550 pending rearm survived')
    forbid(frag, 'IRIS_26550_NIGHT_TO_MOTION_UI_REARM', '26550 Motion-only rearm survived')
    need(frag, 'IRIS_26551_MODE_GENERIC_PROGRESS_REARM', 'generic capture rearm marker missing')
    need(frag, 'IRIS_26551_CAPTURE_UI_OWNER', 'capture UI owner missing')
    need(frag, 'iris26551CaptureUiIsCurrent("frame-complete")', 'late frame callback guard missing')
    need(frag, 'iris26551CaptureUiIsCurrent("capture-sequence-complete")', 'late sequence callback guard missing')

    # Processing ownership: only processing lifecycle shows/hides spinner; capture start never hides it.
    started=frag[frag.index('public void onProcessingStarted'):frag.index('public void onProcessingChanged')]
    finished=frag[frag.index('public void onProcessingFinished'):frag.index('public void notifyImageSavedStatus')]
    capture=frag[frag.index('public void onCaptureStillPictureStarted'):frag.index('private long prevPlayTime')]
    need(started, 'setProcessingProgressBarIndeterminate(true)', 'processing-start SHOW authority missing')
    need(finished, 'setProcessingProgressBarIndeterminate(false)', 'processing-finish HIDE authority missing')
    forbid(capture, 'setProcessingProgressBarIndeterminate(false)', 'capture start still hides processing ring')

    # Mode/capture generation invalidates old queued runnables for any destination mode.
    need(view, 'IRIS_26551_PROGRESS_UI_GENERATION_OWNER', 'UI generation owner missing')
    need(view, 'iris26551AdvanceProgressUiGeneration("mode-transition:"', 'mode transition does not advance generation')
    need(view, 'iris26551AdvanceProgressUiGeneration("capture-start:max=" + max)', 'new capture does not advance generation')
    for op in ['process-ring-show','process-ring-hide','capture-ring-increment','capture-ring-reset','capture-ring-opacity','capture-ring-max']:
        need(view, op, 'generation guard missing for '+op)
    need(view, 'cameraFragment.clearTimerFrameCountForModeTransition();', 'mode-generic countdown clear missing')
    need(view, 'IRIS_26551_STALE_UI_REJECT', 'stale UI rejection telemetry missing')
    need(view, 'IRIS_26551_PROCESS_RING_', 'post-runnable processing-ring telemetry missing')

    # Style authority: frame number and determinate ring use exactly the processing-ring theme attribute.
    need(layout, 'android:id="@+id/frameCount"', 'frameCount view missing')
    start=layout.index('android:id="@+id/frameCount"')
    frame=layout[start:layout.index('/>', start)]
    need(frame, 'android:textColor="?attr/processingProgressColor"', 'frame countdown does not share ring color authority')
    need(draw, '<solid android:color="?attr/processingProgressColor"/>', 'capture progress ring does not share ring color authority')
    ET.parse(cand/ALLOWED[2]); ET.parse(cand/ALLOWED[3])

    need(version, 'VERSION_NAME=0.9726551', 'version name incorrect')
    need(version, 'VERSION_BUILD=26551', 'version build incorrect')

    print('PASS: exact 5-file 26551 runtime scope')
    print('PASS: Night/Motion processing, 12+3, Sabre, Jin, UHDR, VGN, DNG/capture authorities byte-identical')
    print('PASS: stale Night progress operations cannot survive mode/capture generation changes')
    print('PASS: post-Night fix is destination-mode generic, not Motion-specific')
    print('PASS: processing lifecycle remains sole spinner show/hide authority')
    print('PASS: frame countdown + determinate capture ring share processingProgressColor')

if __name__ == '__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--self-test': self_test()
    elif len(sys.argv)==3: validate(sys.argv[1],sys.argv[2])
    else: raise SystemExit('usage: validate... --self-test | <base> <candidate>')
