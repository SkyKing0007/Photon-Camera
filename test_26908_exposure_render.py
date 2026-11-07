#!/usr/bin/env python3
"""Photon 26908 strict new six-path scope and actual Java shutter math, source/shader contracts."""
from pathlib import Path
import subprocess, tempfile, hashlib,re
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(path):
 d={}
 for ln in path.read_text().splitlines():
  h,p=ln.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and p not in d
  d[p]=h
 return d

def main():
 base=parse(R/'26908_BASE_26907_FULL_APP.sha256'); now=parse(R/'26908_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26908_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26908_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 assert len(base)==2030 and len(now)==2031 and len(changed)==6 and len(added)==1
 assert len(base)-len(changed-added)==2025 and set(now)-set(base)==added and set(base)-set(now)==set()
 assert {p for p in base if base[p]!=now[p]}==changed-added
 for p in changed: assert sha(R/'handoff_payload_26908'/p)==now[p],p
 c=R/'handoff_payload_26908/app/src/main/java/com/particlesdevs/photoncamera/capture'
 capture=(c/'CaptureController.java').read_text(); helper=(c/'Iris26908ShutterFirst.java').read_text()
 night=(R/'handoff_payload_26908/app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java').read_text()
 render=(R/'handoff_payload_26908/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 shader=(R/'handoff_payload_26908/app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 assert capture.count('iris26908ObserveContinuousZslShutterPriority(result);')==1
 assert 'Build.VERSION.SDK_INT < 36' in capture and 'CONTROL_AE_AVAILABLE_PRIORITY_MODES' in capture
 assert 'CONTROL_AE_PRIORITY_MODE_SENSOR_EXPOSURE_TIME_PRIORITY' in capture
 assert 'mPreviewRequestBuilder.set(CaptureRequest.SENSOR_SENSITIVITY, null);' in capture
 assert 'getSelectedFpsRange()' in capture and 'iris26381MotionOpportunityCeilingNs(result)' in capture
 assert 'mMotion26713ObservationPending' in capture and 'mMotion26713RecipeReady' in capture
 assert 'mMotion26710ManualReferenceActive' in capture
 assert 'isZslMode()' in capture and 'CameraMode.MOTION' in capture
 assert 'IRIS_26908_AUTO_SHUTTER_CEILING_NS = 100_000_000L' in night
 assert 'LONG_TARGET_MULTIPLIER' in night and 'requireLongExposure' in night
 assert 'IRIS_26824_MOTION_SATURATION_SCALE = 1.07f' in render and 'IRIS_26824_MOTION_SATURATION_SCALE = 1.14f' not in render
 assert 'iris26908NightPresentationLiftEnabled' in render
 assert 'irisNightActive' in render and 'iris26903NightB' in render
 assert shader.count('linearSrgb=iris26908NightPresentationLift(linearSrgb);')==1
 assert 'float ev=0.75*shadowGate*highlightGate;' in shader
 assert 'if(iris26908NightPresentationLiftEnabled==0) return rgb;' in shader
 assert 'if(guide<=0.003 || guide>=0.70) return rgb;' in shader
 assert 'float iris26906BVisualTone(float y)' in shader
 assert 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java' in base
 assert now['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java']==base['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java']
 assert all(now[p]==base[p] for p in base if p.startswith('app/src/main/cpp/'))
 with tempfile.TemporaryDirectory(prefix='photon26908_java_') as d:
  subprocess.run(['javac','-source','17','-target','17','-d',d,str(c/'Iris26908ShutterFirst.java'),str(R/'tests_26908/Photon26908ShutterRegression.java')],check=True)
  subprocess.run(['java','-cp',d,'Photon26908ShutterRegression'],check=True)
 print('PASS 26908 six-path strict source, 2025 protected, actual javac, Night A/B cap+tone, Motion saturation, original 26907 hue protected')
if __name__=='__main__':main()
