#!/usr/bin/env python3
"""26962 SHA-exact 26961 published compiled source, two-file delta, 2053 protected."""
from pathlib import Path
import argparse,hashlib,re,json
R=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  x,p=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',x) and p.startswith('app/') and '..' not in Path(p).parts and p not in d
  d[p]=x
 return d
def check(live=False):
 a=manifest('26962_BASE_26961_FULL_APP.sha256');b=manifest('26962_EXPECTED_FULL_APP.sha256')
 allowed=set((R/'26962_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 assert allowed=={'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties'}
 assert len(a)==len(b)==2055 and set(a)==set(b)
 assert {p for p in a if a[p]!=b[p]}==allowed
 assert manifest('26962_PROTECTED_SOURCE.sha256')=={p:v for p,v in a.items() if p not in allowed}
 assert len(a)-len(allowed)==2053
 assert not (R/'26962_ADDED_RUNTIME_PATHS.txt').read_text().strip()
 assert not (R/'26962_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 pay=R/'handoff_payload_26962'
 assert {p.relative_to(pay).as_posix() for p in pay.rglob('*') if p.is_file()}==allowed
 for x in allowed:assert sha(pay/x)==b[x]
 scope=json.loads((R/'26962_BASELINE_AND_SCOPE.json').read_text())
 assert (scope['run_id'],scope['artifact_id'],scope['protected_count'])==(44435488877,14489008111,2053)
 assert scope['compiled_tar_sha256']=='50436b56e19cb02d8157196239dfaf364498296564ea6cc7b4551a78f286bb69'
 assert set(scope['changed_files'])==allowed
 # Source provenance proves all shaders and processing other than final tone are identical.
 for protected in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp'):
  assert protected in a and protected not in allowed and a[protected]==b[protected],protected
 assert not any('vendor' in p.lower() or '/dng/' in p or 'spektra' in p.lower() for p in allowed)
 j=(pay/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 assert j.count('private float iris26962EffectiveSdrBodyContrast()')==1
 assert j.count('glProg.setVar("iris26792SdrBodyContrast", iris26962EffectiveSdrBodyContrast());')==1
 assert j.count('iris26653SetFinalToneUniforms();')==5
 assert 'final float iris26792BodyContrast = iris26962EffectiveSdrBodyContrast();' in j
 assert 'return selectedPhotoBOff ? 0.23f' in j
 assert '&& p.iris26906ExperimentBSelected' in j and '!p.motionV2SuperResOutputEnabled' in j
 assert '!p.irisNightActive' in j and '!p.iris26903NightB' in j
 assert not re.search(r'iris26962EffectiveSdrBodyContrast\([^)]*zoom',j,re.I)
 assert (pay/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726962\nVERSION_BUILD=26962\n')
 if live:
  files=[*(R/'app/src').rglob('*'),R/'app/build.gradle',R/'app/version.properties']
  have={p.relative_to(R).as_posix():sha(p) for p in files if p.is_file()}
  assert have==b,({p for p in b if have.get(p)!=b[p]})
 print('PASS 26962 exact 26961 compiled authority, 2055 source, 2 changed, 2053 protected; no native/RAW/shader modifications')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();check(a.live)
