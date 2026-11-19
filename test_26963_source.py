#!/usr/bin/env python3
"""26963 exact 26962 successful compiled 2,055-file source; strict 4-file native B scope."""
from pathlib import Path
import argparse,hashlib,re,json
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 out={}
 for line in (R/name).read_text().splitlines():
  h,p=line.split('  ',1)
  assert re.fullmatch(r'[0-9a-f]{64}',h) and p.startswith('app/') and '..' not in Path(p).parts and p not in out
  out[p]=h
 return out
ALLOWED={
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
 'app/version.properties'}
def check(live=False):
 a=manifest('26963_BASE_26962_FULL_APP.sha256');b=manifest('26963_EXPECTED_FULL_APP.sha256')
 allowed=set((R/'26963_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 assert allowed==ALLOWED and len(a)==len(b)==2055 and set(a)==set(b)
 assert {p for p in a if a[p]!=b[p]}==ALLOWED
 assert manifest('26963_PROTECTED_SOURCE.sha256')=={p:v for p,v in a.items() if p not in allowed}
 assert len(a)-len(allowed)==2051
 assert not (R/'26963_ADDED_RUNTIME_PATHS.txt').read_text().strip()
 assert not (R/'26963_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 pay=R/'handoff_payload_26963'
 assert {p.relative_to(pay).as_posix() for p in pay.rglob('*') if p.is_file()}==ALLOWED
 assert all(sha(pay/p)==b[p] for p in allowed)
 sc=json.loads((R/'26963_BASELINE_AND_SCOPE.json').read_text())
 assert (sc['run_id'],sc['artifact_id'],sc['protected_count'],sc['changed_count'])==(44456230335,14498242333,2051,4)
 assert sc['compiled_tar_sha256']=='ff686d9e259ca6e61fcc6f143d30101b0d492d91c3146c26c2020e7067be32ee'
 assert set(sc['changed_files'])==allowed
 protected=(
  'app/src/main/assets/shaders/motionv2/render.glsl',
  'app/src/main/assets/shaders/motionv2/gainmap.glsl',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
  'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
  'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
  'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
  'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
  'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp',
  'app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp',
  'app/src/main/cpp/iris26856/amaze/shaders/amaze_export.comp')
 for path in protected: assert path in a and path not in allowed and a[path]==b[path],path
 assert not any('/vendor/' in path or 'Spektra' in path or '/dng/' in path for path in allowed)
 assert b['app/build.gradle']==a['app/build.gradle']
 v=(pay/'app/version.properties').read_text()
 assert v.endswith('VERSION_NAME=0.9726963\nVERSION_BUILD=26963\n')
 # Critical user-approved 26962 tone and HDRQ strength remain protected, unchanged.
 assert a['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']==b['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']
 if live:
  files=[*(R/'app/src').rglob('*'),R/'app/build.gradle',R/'app/version.properties']
  got={p.relative_to(R).as_posix():sha(p) for p in files if p.is_file()}
  assert got==b,('live changed files mismatch',list(x for x in b if got.get(x)!=b[x])[:9])
 print('PASS 26963 exact 26962 compiled runtime: 2055 files, 4 changed, 2051 protected, all color/SDR/UHDR/vendor unchanged')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args();check(args.live)
