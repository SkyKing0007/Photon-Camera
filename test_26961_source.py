#!/usr/bin/env python3
"""Exact successful 26959 compiled 2055-source universe; protected 2050; B/OFF tone-only scoped delta."""
import argparse,hashlib,pathlib,re,json
R=pathlib.Path(__file__).resolve().parent
A=(R/'26961_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(A)==5 and A==sorted(A)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scan(name):
 d={}
 for line in (R/name).read_text().splitlines():
  digest,p=line.split('  ',1)
  assert p.startswith('app/') and re.fullmatch('[0-9a-f]{64}',digest) and p not in d
  d[p]=digest
 return d
def check(live=False):
 base=scan('26961_BASE_26959_FULL_APP.sha256');out=scan('26961_EXPECTED_FULL_APP.sha256')
 assert len(base)==len(out)==2055 and set(base)==set(out)
 assert {k for k in base if base[k]!=out[k]}==set(A)
 assert scan('26961_PROTECTED_SOURCE.sha256')=={k:v for k,v in base.items() if k not in A}
 assert len(base)-len(A)==2050
 assert not (R/'26961_ADDED_RUNTIME_PATHS.txt').read_text().strip()
 assert not (R/'26961_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 expected={
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
 'app/version.properties'}
 assert set(A)==expected
 payload=R/'handoff_payload_26961'
 assert {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}==set(A)
 assert all(h(payload/k)==out[k] for k in A)
 scope=json.loads((R/'26961_BASELINE_AND_SCOPE.json').read_text())
 assert scope['run_id']==44372238333 and scope['artifact_id']==14460861326
 assert scope['compiled_tar_sha256']=='2fb326a334f68fe0fd2b1b3c36926c85ea2d35e6dc2001d0ee10ad003258a204'
 assert scope['changed_files']==A and scope['protected_count']==2050
 # Real successfully compiled non-mottled 26959 RAW/noise, spatial alignment,
 # motion bypass, AMaZE, FCC, sharpness and native protected without touching.
 mustProtect=(
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqPrivateHeader.hpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp',
 'app/src/main/cpp/iris26856/amaze/shaders/amaze_export.comp',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
 for k in mustProtect:assert k in base and k not in A and out[k]==base[k],k
 assert not any('/vendor/' in k or '/jniLibs/' in k or '/dng/' in k or 'Spektra' in k for k in A)
 for fn in ('render','gainmap'):
  sh=(payload/f'app/src/main/assets/shaders/motionv2/{fn}.glsl').read_text()
  assert sh.count('float iris26961BOffWarmHighlightGuide(')==1
  assert sh.count('uniform int iris26961BOffNeutralIndoor;')==1
  assert sh.count('uniform int iris26961BOffColorSpacingEnabled;')==1
  assert 'iris26954BOffNight26940Sdr' in sh
  assert sh.count('void main()')==1
  # Qualifiers coherent/flat valid only as GLSL qualifiers; reject local identifier usage.
  code=re.sub(r'/\*.*?\*/|//[^\n]*',' ',sh,flags=re.S)
  assert not re.search(r'\b(?:float|int|uint|vec[234]|mat[234]|bool|const)\s+(?:coherent|flat|in|out|varying|attribute|uniform|buffer|precision|shared|layout|sample|switch|class|atomic_uint)\s*[=;,\[]',code),fn
 if live:
  for k,digest in out.items():
   fp=R/k;assert fp.is_file() and h(fp)==digest,k
 print('PASS 26961 actual 26959 complete 2055-source universe; 5 tone-only changes, 2050 protected including RAW/HDRQ/AMaZE/FCC/sky/NDK')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--payload',action='store_true');parser.add_argument('--live',action='store_true');args=parser.parse_args();check(args.live)
