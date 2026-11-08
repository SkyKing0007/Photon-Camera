#!/usr/bin/env python3
"""Production-scope and real Java policy regressions for Photon 26910.

This does not replace real Android NDK/Kotlin/Java/assemble in successful Actions.
"""
from pathlib import Path
import hashlib,re,subprocess,tempfile
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(p):
 d={}
 for ln in p.read_text().splitlines():
  h,k=ln.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and k not in d and k.startswith('app/'),(h,k)
  d[k]=h
 return d

def main():
 before=parse(R/'26910_BASE_26909_FULL_APP.sha256')
 after=parse(R/'26910_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26910_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26910_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 assert len(before)==2032 and len(after)==2033 and len(changed)==6 and len(added)==1
 assert set(after)-set(before)==added and set(before)-set(after)==set()
 assert {p for p in before if before[p]!=after[p]}==changed-added
 assert len(before)-len(changed-added)==2027
 for p in changed:assert sha(R/'handoff_payload_26910'/p)==after[p],p
 for p in before:
  if p.startswith(('app/src/main/cpp/','app/src/main/jniLibs/','app/src/main/assets/')):
   assert before[p]==after[p],p
 root=R/'handoff_payload_26910/app/src/main/java/com/particlesdevs/photoncamera'
 c=(root/'capture/CaptureController.java').read_text()
 swipe=(root/'control/Swipe.java').read_text()
 focus=(root/'control/TouchFocus.java').read_text()
 renderer=(root/'ui/camera/views/viewfinder/MainRenderer.java').read_text()
 math=(root/'capture/Iris26910CaptureSafety.java')
 assert c.count('iris26910GuardPreviewExposure();')==2
 assert 'session.setRepeatingRequest(mPreviewInputRequest = builder.build()' in c
 assert 'session.capture(builder.build(), mCaptureCallback, handler)' in c
 assert c.index('iris26910GuardPreviewExposure();',c.index('public boolean rebuildPreviewBuilder()')) < c.index('session.setRepeatingRequest(mPreviewInputRequest = builder.build()')
 assert 'if (!captureController.iris26910PreserveBManualExposure())' in focus
 assert focus.count('if (!captureController.iris26910PreserveBManualExposure())')==2
 assert 'gestureDetector.onTouchEvent(cancel)' in swipe
 assert 'action == MotionEvent.ACTION_POINTER_DOWN' in swipe
 assert 'iris26910MultiTouchSequence' in swipe
 assert 'if (!iris26910MultiTouchSequence) startTouchFocusLock(e);' in swipe
 assert 'Iris26910CaptureSafety.targetEnergy(' in c
 assert 'mMotion26713RecipeOffsetEv' in c
 assert 'if (iris26871BExposureSelected()) {' in c
 assert 'Iris26910CaptureSafety.completionTimeoutMs(' in c
 assert 'ticket.captureStartedElapsedMs = android.os.SystemClock.elapsedRealtime();' in c
 assert 'if (progressMs <= 0L || !Iris26910CaptureSafety.attemptStalled(' in c
 assert 'Iris26910CaptureSafety.lowLightPreviewLiftEv' in c
 assert 'getMotion26663ReferencePreviewProtectionEv' in renderer
 assert 'iris26663Controller.iris26910PreserveBManualExposure()' in renderer
 assert 'mIris26663LastConfirmedProtectionEv +=' in renderer
 assert 'iris26909ObserveBContinuousShutterFirst(request, result);' in c
 assert 'iris26909ReleaseBManualToHal("raw_highlight_full_well_guard", true);' in c
 assert 'mMotion26710ManualReferenceActive = true' not in c
 assert 'if (mIris26909ManualViolations >= 4)' in c
 assert 'MOTION_26724_NORMAL_ATTEMPT_WATCHDOG_MS = 900L' in c # historical A retained
 assert 'IRIS_26841_SINGLE_TARGET_HAL_HDR_PREVIEW' in c
 assert 'IRIS_26908_SHUTTER_FIRST_CONTINUOUS_ZSL' in c
 assert 'mMotion26713RecipeReady' in c
 # Compile the *actual* added pure production source and grammar-parse all
 # five edited production Java sources. No stubbed producer logic.
 with tempfile.TemporaryDirectory(prefix='26910_java_policy_') as d:
  tests=R/'tests_26910'
  subprocess.run(['javac','-source','17','-target','17','-d',d,
                  str(math),str(tests/'Photon26910CaptureSafetyRegression.java')],check=True)
  subprocess.run(['java','-cp',d,'Photon26910CaptureSafetyRegression'],check=True)
  subprocess.run(['javac','-source','17','-target','17','-d',d,str(tests/'JavaParseOnly.java')],check=True)
  subprocess.run(['java','-cp',d,'JavaParseOnly',str(root/'capture/CaptureController.java'),
                  str(math),str(root/'control/Swipe.java'),str(root/'control/TouchFocus.java'),
                  str(root/'ui/camera/views/viewfinder/MainRenderer.java')],check=True)
 print('PASS six exact 26910 source paths, 2027 protected files, no native/vendor/shaders touched, photo/night/B preview and capture source gates')
if __name__=='__main__':main()
