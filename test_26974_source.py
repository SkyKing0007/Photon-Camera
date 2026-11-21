#!/usr/bin/env python3
"""Exact C-only 26974 physical, ownership, preview, callback and host fence checks."""
from pathlib import Path
import hashlib,subprocess,tempfile,sys
from importlib.machinery import SourceFileLoader
R=Path(__file__).resolve().parent
b=SourceFileLoader('build26974',str(R/'build_26974_incremental.py')).load_module()
changed,a,expected=b.scope()
assert len(changed)==4 and len(a)==len(expected)==2132
P=R/'handoff_payload_26974' if '--payload' in sys.argv or '--live' not in sys.argv else R
if '--live' in sys.argv: b.exact(R,'26974_EXPECTED_FULL_APP.sha256','26974 current live original compiled-source overlay equality')
assert all(b.sha(P/p)==expected[p] for p in changed)

def get(p):return (P/p).read_text()
ctl=get('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
k=get('app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt')
f=get('app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CSequenceFence.java')
version=get('app/version.properties')
assert 'VERSION_BUILD=26974' in version and 'VERSION_NAME=0.9726974' in version
assert 'IRIS_26974_C_TRUE_INDEPENDENT_MOTION_SHUTTER_ENTRY' in ctl
start=ctl.index('IRIS_26974_C_TRUE_INDEPENDENT_MOTION_SHUTTER_ENTRY')
end=ctl.index('IRIS_26679_SCENE_INDEPENDENT_SHUTTER_ADMISSION',start)
assert 'iris26972CStartIndependentCamera2(false);' in ctl[start:end]
assert 'mIris26972CShutterSession != null' in ctl[start:end]
assert 'iris26679RejectShutter("IRIS_26974_C_INDEPENDENT_BUSY"' in ctl[start:end]
assert 'iris26974CResumePreviewOnly(' in ctl
preview=ctl[ctl.index('private boolean iris26974CResumePreviewOnly('):ctl.index('/* IRIS_26972_C_INDEPENDENT_SHUTTER_SUBMISSION')]
for part in ('mCaptureSession != ownedSession','mIris26972CShutterSession == null','builder.removeTarget(rawSurface)','setRepeatingRequest(onlyPreview','builder.addTarget(rawSurface)','!onlyPreview.getTargets().contains(surface)'):
 assert part in preview,part
c=ctl[ctl.index('private void iris26972CStartIndependentCamera2('):ctl.index('private void triggerZslCapture()',ctl.index('private void iris26972CStartIndependentCamera2('))]
for part in ('cSequenceFence.markCameraSequenceEnded();','cSequenceFence.isTerminalDelivered()','cReleaseAfterSequence.run();','cReader.setOnImageAvailableListener(', 'mIris26974CRawCallbackThread = cRawThread','mBackgroundHandler == captureHandler','cRawMoved[0]','onCaptureSequenceAborted','owner.onCaptureFailed','cWatchdog.setDaemon(true)','cWatchdog.start()','cameraEventsListener.onFrameCountSet(frames)','IRIS_26974_C_CAMERA2_SEQUENCE_COMPLETED','IRIS_26974_C_RAW_IO_SEPARATED','IRIS_26974_C_INDEPENDENT_ACQUISITION_DEADLINE','IRIS_26974_C_PREVIEW_STOP_FOR_BURST'):
 assert part in c,part
# Verify a separate RAW callback HandlerThread, never the old camera callback Handler.
assert c.count('new android.os.HandlerThread("Iris26974-C-RAW-IO")')==1
assert c.count('captureSession.captureBurst(requests, onlyC, captureHandler);')==1
assert 'captureHandler.postDelayed(owner::timeout' not in c
# Original C no-fallback and physical route.
for part in ('C_PHYSICAL_RAW_OUTPUT_NOT_PROVEN','C_FROZEN_MANUAL_EXPOSURE_MISSING','C_PHYSICAL_LENS_SHADING_UNAVAILABLE','Iris26972CFrameTag(owner, i)','Iris26972CContract.MAX_NORMAL_FRAMES'):
 assert part in c,part
# Explicit Java fence plus Kotlin RAW I/O stage proof.
assert 'public synchronized boolean isTerminalDelivered()' in f
assert 'if (!sequenceEnded || !terminalDelivered || released) return false;' in f
for part in ('val sourceTimestamp = image.timestamp','checkNotNull(spool).offerRaw(image)','IRIS_26974_C_RAW_STAGED','IRIS_26974_C_FULL_BURST_PROCESSING_START','IRIS_26974_C_GPU_FINISH','IRIS_26974_C_TERMINAL_FAILURE'):
 assert part in k,part
# No changes whatsoever to GLSL, A/B, Night, DNG, C native/vendor.
assert {name for name in changed if name.startswith('app/src/main/assets/') or name.startswith('app/src/main/cpp/') or name.startswith('app/src/main/jniLibs/') or name.endswith('.glsl') or name.endswith('.comp')}==set()
print('PASS 26974 independent C-only shutter, Camera2 preview-only and RAW worker/sequence ownership source contracts; 2128 protected')
if '--host-java' in sys.argv:
 source=P/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CSequenceFence.java'
 with tempfile.TemporaryDirectory(prefix='p26974_fence_') as td:
  tmp=Path(td)
  dest=tmp/'com/particlesdevs/photoncamera/processing/experimentc/Iris26972CSequenceFence.java';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
  (tmp/'Check.java').write_text('''import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CSequenceFence;
public class Check {
 public static void main(String[] args) {
  Iris26972CSequenceFence a=new Iris26972CSequenceFence();
  if(a.takeReleasePermit()||a.isTerminalDelivered()||a.isSequenceEnded())throw new AssertionError("empty fence");
  a.markTerminalDelivered(); if(a.takeReleasePermit()||!a.isTerminalDelivered())throw new AssertionError("terminal-first");
  a.markCameraSequenceEnded(); if(!a.takeReleasePermit()||a.takeReleasePermit())throw new AssertionError("exact-once terminal-first");
  Iris26972CSequenceFence b=new Iris26972CSequenceFence();
  b.markCameraSequenceEnded();if(b.takeReleasePermit()||b.isTerminalDelivered())throw new AssertionError("sequence-first");
  b.markTerminalDelivered();if(!b.takeReleasePermit()||b.takeReleasePermit())throw new AssertionError("exact-once sequence-first");
  Iris26972CSequenceFence c=new Iris26972CSequenceFence();c.markNeverSubmitted();
  if(c.takeReleasePermit())throw new AssertionError("never-submitted needs terminal");
  c.markTerminalDelivered();if(!c.takeReleasePermit())throw new AssertionError("never-submitted release");
  System.out.println("PASS 26974 Java sequence fence, release exactly once, both orderings, never-submitted");
 }
}''')
  subprocess.run(['javac','-d',str(tmp/'out'),str(dest),str(tmp/'Check.java')],check=True)
  subprocess.run(['java','-cp',str(tmp/'out'),'Check'],check=True)
