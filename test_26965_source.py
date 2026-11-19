#!/usr/bin/env python3
"""26965 exact four-file changed-source gate; original 26964 compile source protected."""
from pathlib import Path
import argparse,hashlib,re,json
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
def load(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,path=line.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',h) and path.startswith('app/') and path not in d;d[path]=h
 return d
a=load('26965_BASE_26964_FULL_APP.sha256');b=load('26965_EXPECTED_FULL_APP.sha256')
changed={'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp','app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp','app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp','app/version.properties'}
assert len(a)==len(b)==2055 and set(a)==set(b)
assert {x for x in a if a[x]!=b[x]}==changed
assert set((R/'26965_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())==changed
assert load('26965_PROTECTED_SOURCE.sha256')=={p:a[p] for p in a if p not in changed}
assert len(a)-len(changed)==2051
assert not (R/'26965_ADDED_RUNTIME_PATHS.txt').read_text().strip()
assert not (R/'26965_DELETED_RUNTIME_PATHS.txt').read_text().strip()
assert {x.relative_to(R/'handoff_payload_26965').as_posix() for x in (R/'handoff_payload_26965').rglob('*') if x.is_file()}==changed
D=R if args.live else R/'handoff_payload_26965'
for rel in changed:
 f=D/rel;assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==b[rel],rel
co=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
assert co.count('IRIS_26965_B_OFF_RAWR_B6C05A0_HDRQ_MOTION_OWNERSHIP')==1
assert 'const bool photoBOffLatestRawr = iris26941BOffHdrqLazyPoolReset &&' in co
assert co.count('recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency);')==1
assert 'photoBOffRawr051' not in co
assert co.count('iris26957HdrqEffectiveFrames = hdrqEffectiveFrames;')==1
re=(D/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp').read_text()
ms=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
assert 'if (uniformExposure_ && iris26941BOffHdrqLazyPoolReset && !gated)' in re
assert 'const bool gated=uniformExposure_ && motionGateEnabled_;' in re
assert 'fftInput26963' not in re and 'spatialScreen26963' not in re
assert 'ib(0, alignedRgba), ib(1, arena_.image("hdrq_aligned_ft"))' in re
assert '0 /* no pre-FFT screen */' in re
assert 'IRIS_26964_B_OFF_MOTION_RESIDUAL_AFTER_SUBPIXEL_EXPLANATION' not in ms
assert 'imageStore(temporalAligned' not in ms
assert 'if (p.useSpatialScreen != 0)' not in ms
assert 'imageStore(zmap,g,vec4(p.useMotionGate!=0 ? acc/16.0 : 0.0));' in ms

assert 'if (pass == 3u && algorithm_ == MergeAlgorithm::HdrPlusFrequency) {' in co
assert 'if (pass == 3u && algorithm_ == MergeAlgorithm::HdrPlusFrequency &&' not in co
assert 'if (algorithm_ == MergeAlgorithm::HdrPlusBracketed)' in co
assert 'if (pass == 0u && i == order.front()' in co
assert 'B_OFF_RAWR_HDRQ active=1 gate=1 preFFTSpatialScreen=0' in co
assert (D/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726965\nVERSION_BUILD=26965\n')
if args.live:
 d={}
 for p in [*(R/'app/src').rglob('*'),R/'app/build.gradle',R/'app/version.properties']:
  if p.is_symlink():raise ValueError('symlink in runtime')
  if p.is_file():d[p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert d==b,[(k,d.get(k),b.get(k)) for k in b if d.get(k)!=b.get(k)][:3]
 owner=(R/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 tone=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f' in owner
 assert 'return selectedPhotoBOff ? 0.23f' in tone
 assert a['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']==b['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']
 assert a['app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java']==b['app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java']
print('PASS 26965 exact 26964 runtime authority, four changes, 2051 protected; B OFF RAWr HDRQ motion gate + effective support; capture/color untouched')
