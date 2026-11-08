#!/usr/bin/env python3
"""Actual 26911 Java regression, production parse and strict source overlay scope.
This does NOT replace Actions full NDK/Kotlin/Java/assembly or device preview tests.
"""
from pathlib import Path
import hashlib,re,subprocess,tempfile
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in p.read_text().splitlines():
  h,name=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and name.startswith('app/') and '..' not in Path(name).parts and name not in d
  d[name]=h
 return d

def run():
 base=manifest(R/'26911_BASE_26910_FULL_APP.sha256');after=manifest(R/'26911_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26911_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 assert len(base)==2033 and len(after)==2034 and len(changed)==4 and len(set(changed))==4
 assert len(added)==1 and len(set(added))==1 and set(added).issubset(changed)
 assert set(after)-set(base)==set(added) and not (set(base)-set(after))
 assert {p for p in base if base[p]!=after[p]}==set(changed)-set(added)
 assert len(base)-(len(changed)-len(added))==2030
 for p in base:
  if p.startswith(('app/src/main/assets/','app/src/main/cpp/','app/src/main/jniLibs/')):assert after[p]==base[p],p
 for p in changed:assert sha(R/'handoff_payload_26911'/p)==after[p],p
 java=R/'handoff_payload_26911/app/src/main/java/com/particlesdevs/photoncamera'
 capture=(java/'capture/CaptureController.java').read_text()
 renderer=(java/'ui/camera/views/viewfinder/MainRenderer.java').read_text()
 helper=java/'capture/Iris26911Continuity.java'
 # Exact sensor state + physical RAW provenance, reject energy-equivalent old HAL samples.
 assert 'iris26911ExactBManualFrame(iris26593NormalReference)' in capture
 assert 'if (iris26909OwnsManualPreview() && !iris26911ExactBManualFrame(result))' in capture
 assert 'if (iris26911DeferBShutterForPhysicalPair()) return;' in capture
 assert 'mIris26909ManualSeen >= 3 && verifiedRing >= 2' in capture
 assert '"B_MANUAL_EXPOSURE_NOT_SETTLED"' in capture
 assert '"B_MANUAL_SETTLE_NO_HANDLER"' in capture
 assert 'mIris26909ManualUnavailable' in capture
 assert 'getIris26911' not in capture # no stray nonexisting getters
 assert 'mIris26911LastLoggedActualExposureNs' not in capture # prevent accidentally renaming the proven 26909 field
 assert 'mIris26909LastLoggedActualExposureNs = 0L;' in capture
 assert 'Iris26911Continuity.significantSceneChange(' in capture
 assert 'Iris26911Continuity.navigationRequiresRemeter(' in capture
 assert 'iris26909ReleaseBManualToHal("raw_highlight_full_well_guard", true);' in capture
 assert 'mIris26909ManualViolations >= 4' in capture
 assert 'if (!iris26909OwnsManualPreview() && motion26712NavigationConfirmed())' in capture
 assert 'iris26911PreviewStage(long timestampNs)' in capture
 assert 'mIris26911PreviewStageTimestamps' in capture
 assert 'mIris26911ManualReleaseEpoch++' in capture
 assert 'iris26911DarkPreviewEvidence()' in capture
 assert 'mIris26911Preview.sample(mIris26872ProbeReadback, timestampNs)' in renderer
 assert 'iris26872Controller::iris26911PreviewStage' in renderer
 assert 'mIris26911Preview.liftEv()' in renderer
 assert 'IRIS_26911_B_PREVIEW_MEASURED_GAIN' in renderer
 assert 'mIris26910' not in renderer
 # A and Night behavior unaffected, existing 26910 focus and timeout must remain.
 assert 'iris26910GuardPreviewExposure();' in capture
 assert 'Iris26910CaptureSafety.completionTimeoutMs(' in capture
 assert 'Iris26910CaptureSafety.targetEnergy(' in capture
 assert 'Iris26910CaptureSafety.lowLightPreviewLiftEv(' in capture
 assert 'iris26871BExposureSelected()' in capture
 assert 'IRIS_26908_SHUTTER_FIRST_CONTINUOUS_ZSL' in capture
 assert (R/'26911_PRECOMPILE_EXPECTED_FULL_APP.sha256').is_file()
 # Actual production helper compiled (not stubbed); real production Java files grammar-parsed.
 with tempfile.TemporaryDirectory(prefix='26911_java_') as d:
  root=R/'tests_26911'
  subprocess.run(['javac','--release','17','-d',d,str(helper),str(root/'Photon26911ContinuityRegression.java')],check=True)
  subprocess.run(['java','-cp',d,'Photon26911ContinuityRegression'],check=True)
  subprocess.run(['javac','--release','17','-d',d,str(root/'JavaParseOnly.java')],check=True)
  subprocess.run(['java','-cp',d,'JavaParseOnly',str(java/'capture/CaptureController.java'),
    str(helper),str(java/'ui/camera/views/viewfinder/MainRenderer.java')],check=True)
 print('PASS Photon 26911: 4-file allowlist, 2030 protected, real Java manual/preview policies, exact-result RAW admission, real scene-navigation and focus/capture regressions preserved')
if __name__=='__main__':run()
