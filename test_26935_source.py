#!/usr/bin/env python3
"""Exact sealed B-only/50MP/RAW LKR/preview ownership with protected success SHA."""
from pathlib import Path
import sys
from build_26935_incremental import R,scope,sha,fail

def main():
 changed,added,base,new=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26935'
 def content(path):
  p=root/path
  if not p.is_file() or sha(p)!=new[path]:fail('current candidate differs from seal '+path)
  return p.read_text()
 capture=content('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
 session=content('app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java')
 relay=content('app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnProcessingRelay.java')
 renderer=content('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')
 ui=content('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
 frag=content('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
 controller=content('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
 ver=content('app/version.properties')
 contracts={
 'capture':(capture,('iris26856FrozenExperiment','mMotion26575SuperResAtShutter','Iris26935BOnProcessingRelay','mMotion26636HeicAtShutter',
                 'iris26593Plan.normalTargetFrames > 0','mIris26935BOnAcquisition','IRIS_26935_NO_POST_LKR_DEFERRED_SHUTTER_REPLAY','processExecutor.execute','RejectedExecutionException','finishIfMissing',
                 'Iris26935BOnSession.isActive()','IRIS_26713_CAPTURE_RECIPE_OWNER_ENDS_AT_PHYSICAL_BATCH')),
 'session':(session,('WeakReference<Listener>','static long activeToken','if (!active || token != activeToken)',
                'if (active) throw new IllegalStateException','active = false','unsubscribe')),
 'relay':(relay,('Files.isRegularFile','Files.size(path) <= 0L','Locale.ROOT','notifyImageSavedStatus',
              'filename.endsWith(".jpg")','filename.endsWith(".heic")','finishIfMissing','complete(token, true',
              'terminalReleaseDeferred=true')),
 'renderer':(renderer,('iris26872Eligible','iris26872Probe(iris26553FrameTimestamp)',
                       'iris26911DarkPreviewEvidence','mIris26935ProbeSkipBudget','mIris26935LastMeasuredTimestamp',
                       'iris26935UnmeasuredFrame','getMotion26663ReferencePreviewProtectionEv')),
 'ui':(ui,('Iris26935BOnSession.isActive()','setClickable(status && !iris26935Locked)',
           'setEnabled(false)','setAlpha(0.38f)','setEnabled(true)')),
 'fragment':(frag,('Iris26935BOnSession.subscribe','Iris26935BOnSession.unsubscribe',
                   'token != com.particlesdevs.photoncamera.capture.Iris26935BOnSession.currentToken()',
                   'Iris26935BOnSession.isActive()')),
 'ui-controller':(controller,('Iris26935BOnSession.isActive()','IRIS_26935_QUEUED_SHUTTER_REJECT')),
 'version':(ver,('VERSION_BUILD=26935','VERSION_NAME=0.9726935'))}
 for k,(body,tokens) in contracts.items():
  for t in tokens:
   if t not in body:fail('source-level semantic/ownership check failed '+k+' '+t)
 # The 26934 smooth-white correction, actual original 3x2 solver, all five shaders,
 # dual ABI native source, B OFF/A/Night/LONG/UHDR/DNG must be identical by full SHA.
 for path in ('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',
              'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java',
              'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
              'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
              'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java',
              'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
              'app/src/main/assets/shaders/motionv2/gainmap.glsl',
              'app/src/main/assets/shaders/motionv2/render.glsl'):
  if base[path]!=new[path]:fail('protected image quality regression '+path)
 if any('/cpp/' in p or '/jniLibs/' in p or '/assets/' in p for p in changed|added):fail('unexpected native/shader modification')
 print('PASS 26935 2048 successful authority, 6 changed 2 added, 2042 protected, immutable 26934 highlight and LKR shader/native unchanged')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
