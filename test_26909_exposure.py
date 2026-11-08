#!/usr/bin/env python3
"""Real 26909 Java logic and Night selector compile with protected source checks.
The entire Android Kotlin/Java/NDK/APK still MUST compile in Actions; this gate
checks the new logic without pretending a local Android build occurred.
"""
from pathlib import Path
import hashlib,re,subprocess,tempfile
R=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(path):
 m={}
 for ln in path.read_text().splitlines():
  h,p=ln.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',h) and p not in m
  m[p]=h
 return m

def run(*a):subprocess.run(a,check=True)
def main():
 base=parse(R/'26909_BASE_26908_FULL_APP.sha256');now=parse(R/'26909_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26909_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26909_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 assert len(base)==2031 and len(now)==2032 and len(changed)==4 and len(added)==1
 assert set(now)-set(base)==added and not set(base)-set(now)
 assert {p for p in base if base[p]!=now[p]}==changed-added
 assert len(base)-len(changed-added)==2028
 for p in changed:assert digest(R/'handoff_payload_26909'/p)==now[p],p
 for p in base:
  if p.startswith(('app/src/main/cpp/','app/src/main/jniLibs/','app/src/main/assets/')):
   assert now[p]==base[p],p
 # Experiment B source-only scope; Experiment A, 26908 render shaders/tone,
 # 26907 hue, 26906 cache/native, Spektra and every protected source identical.
 c=R/'handoff_payload_26909/app/src/main/java/com/particlesdevs/photoncamera/capture'
 ctrl=c/'CaptureController.java';math=c/'Iris26909ShutterIsoMath.java'
 night=R/'handoff_payload_26909/app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java'
 src=ctrl.read_text();n=night.read_text();h=math.read_text()
 assert src.count('iris26909ObserveBContinuousShutterFirst(request, result);')==1
 assert src.count('iris26908ObserveContinuousZslShutterPriority(result);')==1
 assert 'if (iris26871BExposureSelected())' in src and 'if (!iris26909OwnsManualPreview())' in src
 assert 'mIris26909ManualGeneration == mIris26548CameraHealthGeneration' in src
 assert 'motion26713ManualSensorAvailable()' in src and 'mMotion26713RecipeReady' in src
 assert 'mMotion26713ObservationPending' in src and 'mMotion26713RecipeGeneration != generation' in src
 assert 'iris26909ReleaseBManualToHal("semantic_navigation", false);' in src
 assert 'iris26909ReleaseBManualToHal("hal_did_not_honor_manual_pair", true);' in src
 assert 'iris26909ReleaseBManualToHal("raw_highlight_full_well_guard", true);' in src
 assert 'mPreviewRequestBuilder.set(CaptureRequest.SENSOR_FRAME_DURATION, plan.frameDurationNs);' in src
 assert 'mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, null);' in src
 assert 'mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_MODE,\n                    CaptureRequest.CONTROL_AE_MODE_OFF);' in src
 assert 'IRIS_26909_RETAIN_STABLE_B_RECIPE_AFTER_CAPTURE' in src
 assert 'iris26909PutBManualOnBuilder();' in src
 assert 'iris26909UserManualExposure()' in src
 assert 'mMotion26713RecipeReady' in src and 'iris26905BOffNormalOnly' in src
 assert 'mMotion26710ManualReferenceActive' in src and 'updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant' in src
 assert 'mMotion26710ManualReferenceActive = true' not in src
 assert 'Iris26909ShutterIsoMath.solve(' in src and 'MAX_AUTO_SHUTTER_NS = 100_000_000L' in h
 assert 'IRIS_26909_B_NIGHT_SHUTTER_OVER_MOTION' in n
 assert 'long shortCap = experimentB' in n and ': shortMotionCap(tripod, safeShakiness, exposureHigh);' in n
 assert 'boolean requireLongExposure' in n and 'if (requireLongExposure)' in n
 assert 'experimentB ? Math.max(1, isoLow) : Math.max(100, isoLow)' in n
 assert 'if (experimentB && requireLongExposure)' in n
 assert n.count('applyShortPlan(')>=1 and n.count('applyLongPlan(')>=1
 # A Night short/long helpers are byte-for-byte same as successful 26908.
 a=n[n.index('    private static long shortMotionCap('):n.index('    private static long antiFlicker(')]
 assert hashlib.sha256(a.encode()).hexdigest()=='1ec43bb120ca333ef5991f9df2d9c967285abf39a766a090f06f0bf9ae729ca0','Night A shutter helpers changed'
 with tempfile.TemporaryDirectory(prefix='26909_live_java_') as d:
  t=R/'tests_26909'
  run('javac','-source','17','-target','17','-d',d,str(math),str(t/'Photon26909ShutterFirstRegression.java'))
  run('java','-cp',d,'Photon26909ShutterFirstRegression')
  run('javac','-source','17','-target','17','-d',d,*map(str,(t/'nightstubs').rglob('*.java')),str(night),str(t/'Photon26909NightRegression.java'))
  run('java','-cp',d,'Photon26909NightRegression')
  run('javac','-source','17','-target','17','-d',d,str(t/'JavaParseOnly.java'))
  run('java','-cp',d,'JavaParseOnly',str(ctrl),str(math),str(night))
 print('PASS 26909 4-path exact scope, 2028 protected, actual Java shutter and Night selector, source parsing, 26908/26907/26906/26904 immutable')
if __name__=='__main__':main()
