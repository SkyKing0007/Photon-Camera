#!/usr/bin/env python3
"""Exact 26963 compiled authority; four controlled source changes, 2051 hash-protected."""
from pathlib import Path
import argparse,hashlib,re,json
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
def scan(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,path=line.split('  ',1);assert path.startswith('app/') and re.fullmatch('[0-9a-f]{64}',h) and path not in d;d[path]=h
 return d
a=scan('26964_BASE_26963_FULL_APP.sha256');b=scan('26964_EXPECTED_FULL_APP.sha256')
expected={
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java',
 'app/version.properties'}
assert len(a)==len(b)==2055 and set(a)==set(b)
assert {x for x in a if a[x]!=b[x]}==expected
assert set((R/'26964_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())==expected
assert scan('26964_PROTECTED_SOURCE.sha256')=={x:a[x] for x in a if x not in expected}
assert len(a)-len(expected)==2051
assert not (R/'26964_ADDED_RUNTIME_PATHS.txt').read_text().strip()
assert not (R/'26964_DELETED_RUNTIME_PATHS.txt').read_text().strip()
D=R if args.live else R/'handoff_payload_26964'
assert {x.relative_to(R/'handoff_payload_26964').as_posix() for x in (R/'handoff_payload_26964').rglob('*') if x.is_file()}==expected
for rel in expected:
 f=D/rel;assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==b[rel],rel
j=(D/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
m=(D/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java').read_text()
s=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
assert j.count('Iris26909ShutterIsoMath.solveSceneLensAware(')==1
assert 'mIris26909ManualActive' in j and 'iris26909UserManualExposure()' in j
assert 'mMotion26380RawHighlightFraction > 0.015f' in j
assert 'mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_MODE,' in j
assert 'mIris26909ManualShutterNs = plan.shutterNs;' in j
assert 'mIris26909ManualIso = plan.iso;' in j
assert 'originalShutterNs=' in j and 'originalIso=' in j
assert 'SENSOR_MAX_ANALOG_SENSITIVITY' in j and 'SENSOR_INFO_PHYSICAL_SIZE' in j
assert 'LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION' in j and 'motion26712NavigationConfirmed()' in j
assert 'mMotion26380RawMeanSignal' in j and 'mMotion26380RawHighlightFraction' in j
assert 'analogIsoMax' in m and 'qualityIsoCeiling' in m
assert s.count('IRIS_26964_B_OFF_MOTION_RESIDUAL_AFTER_SUBPIXEL_EXPLANATION')==1
assert 'int useSpatialScreen;' in s and 'int useMotionGate;' in s
assert 'const float WIN16[16]' in s and s.count('layout(local_size_x = 16, local_size_y = 4) in;')==1
assert 'smoothstep(2.2, 3.8, ratio)' in s and 'smoothstep(4.5, 9.0, aliasRisk)' in s
assert 'vec2(-0.5), vec2(0.5)' in s
assert 'imageStore(zmap,g,vec4(p.useMotionGate!=0 ? acc/16.0 : 0.0));' in s
assert (D/'app/version.properties').read_text().endswith('VERSION_BUILD=26964\n')
protected_must=(
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for item in protected_must:assert item in a and a[item]==b[item],item
if args.live:
 for path,digest in b.items():
  assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest,path
 c=(R/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 r=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f' in c
 assert 'return selectedPhotoBOff ? 0.23f' in r
print('PASS 26964 exact successful 26963 2055-source scope, 4 intended source changes, 2051 protected, no shader/SDR/NDK/vendor deviations')
