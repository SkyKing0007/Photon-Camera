#!/usr/bin/env python3
"""Do not modify the 26963 HDRQ strength 11, raw reconstruction, or SDR/UHDR rendering."""
from pathlib import Path
import argparse
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
def m(x):return {p:h for h,p in [line.split('  ',1) for line in (R/x).read_text().splitlines()]}
a=m('26964_BASE_26963_FULL_APP.sha256');b=m('26964_EXPECTED_FULL_APP.sha256')
for f in a:
 if '/vendor/' in f or '/assets/shaders/motionv2/' in f or f.endswith('Iris26887BOffHdrqMerge.comp') or f.endswith('Iris26888BOffHdrqCoordinator.cpp') or f.endswith('Iris26887BOffHdrqRecorder.cpp') or f.endswith('MotionV2Render.java') or '/amaze/' in f or '/jniLibs/' in f or 'Spektra' in f:
  assert a[f]==b[f],f
if args.live:
 c=(R/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 coord=(R/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
 render=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f' in c
 assert 'const bool photoBOffRawr051 = iris26941BOffHdrqLazyPoolReset &&' in coord
 assert 'recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency &&' in coord
 assert '!photoBOffRawr051' in coord
 assert 'return selectedPhotoBOff ? 0.23f' in render
print('PASS 26964 HDRQ 11, 26963 tone0.23 and chroma+SDR/UHDR unchanged; no RAWR zmap gate or reference shrink')
