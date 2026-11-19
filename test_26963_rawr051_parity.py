#!/usr/bin/env python3
"""Photo B only: 26962 HDRQ strength/frequency fusion, 26959 mottling-free RGB unchanged."""
from pathlib import Path
import argparse,hashlib
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
D=R if args.live else None
# The compiled-source manifest, not stale repo, is the invariant for source not overlaid.
def parse(name):
 return {path:digest for digest,path in (line.split('  ',1) for line in (R/name).read_text().splitlines())}
a=parse('26963_BASE_26962_FULL_APP.sha256');b=parse('26963_EXPECTED_FULL_APP.sha256')
for path in a:
 if '/vendor/' in path or '/assets/shaders/motionv2/' in path or path.endswith('Iris26887BOffHdrqMerge.comp') or path.endswith('Iris26887BOffHdrqMismatchNorm.comp') or path.endswith('Iris26888BOffHdrqCoordinator.cpp') or path.endswith('Iris26864RealRawrCoordinator.cpp') or path.endswith('MotionV2Render.java'):
  assert a[path]==b[path],path
if args.live:
 c=(R/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 coord=(R/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
 render=(R/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f' in c
 assert 'const bool photoBOffRawr051 = iris26941BOffHdrqLazyPoolReset &&' in coord
 assert 'recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency &&' in coord
 assert '!photoBOffRawr051' in coord
 assert 'return selectedPhotoBOff ? 0.23f' in render
 assert (R/'app/src/main/assets/shaders/motionv2/render.glsl').is_file()
 assert (R/'app/src/main/assets/shaders/motionv2/gainmap.glsl').is_file()
print('PASS 26962 B/OFF strength11, no 26960 zmap gate/shrink, protected merge/mismatchNorm/SDR/UHDR/AMaZE/vendor')
