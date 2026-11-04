#!/usr/bin/env python3
"""Photon 26900 exact three-stage source/trigger+runner sealed real-byte gate."""
from pathlib import Path
import hashlib,re,sys,subprocess
R=Path(__file__).resolve().parent
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def man(n):
 d={}
 for x in (R/n).read_text().splitlines():
  h,sep,p=x.partition('  ');assert sep=='  ' and re.fullmatch(r'[0-9a-f]{64}',h) and p and p not in d
  d[p]=h
 return d
old=man('26900_BASE_FULL_APP.sha256');new=man('26900_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=man('26900_UNCHANGED_PROTECTED.sha256')
mod=sorted(k for k in old.keys()&new.keys() if old[k]!=new[k]);add=sorted(new.keys()-old.keys());delete=sorted(old.keys()-new.keys())
assert len(old)==len(new)==2026 and len(pro)==2022
assert len(mod)==4 and not add and not delete
assert mod==(R/'26900_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert not (R/'26900_ADDITIONS.txt').read_bytes() and not (R/'26900_DELETIONS.txt').read_bytes()
assert set(pro)==set(old)-set(mod)
assert all(pro[k]==old[k]==new[k] for k in pro)
pay=R/'handoff_payload_26900'
assert {p.relative_to(pay).as_posix() for p in pay.rglob('*') if p.is_file()}=={p[4:] for p in mod}
assert all(H(pay/p[4:])==new[p] for p in mod)
assert 'VERSION_BUILD=26900' in (pay/'version.properties').read_text()
wf=R/'.github/workflows/build-26900-iris-rawr.yml'
if not wf.is_file():wf=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26900-iris-rawr.yml'
assert wf.is_file()
s=wf.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26900.txt'\n"
assert s.count('      - name: ')==6
steps=('Replay exact successful 26899 V2 parent runner','Derive SHA-sealed 26900 successor guarded runner','Run inherited 17-stage 26900 build','Prove single intended 26900 APK','Seal exact EXECUTED 26900 runner','Upload authoritative 26900 proof and APK')
assert all(s.count('      - name: '+x)==1 for x in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
assert s.count('python3 -S generate_26899_build.py .')==2
assert s.count('python3 -S generate_26900_build.py .')==2
assert s.count('bash build_26900_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26900')==1
assert 'build_26900_iris_rawr_outputs/' in s and 'IrisCamera-0.9726900-26900-iris-rawr-debug.apk' in s
assert 'a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7' not in s or 'generate_26899_build.py' in s
rsha=(R/'26900_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[0-9a-f]{64}',rsha) and rsha in s
tr=R/'TRIGGER_26900.txt'
if not tr.is_file():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26900.txt'
assert tr.read_bytes()==b'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V1\n'
assert not any(x.suffix=='.apk' for x in R.rglob('*') if x.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26900 DRAFT exact compiled parent, 4 changed shaders/Java/version, 2022 protected, one trigger');sys.exit(0)
assert sys.argv[1:]==[]
seal=man('26900_HANDOFF_HASHES.sha256')
def resolve(p):
 f=R/p
 if f.is_file():return f
 if p.startswith('.github/workflows/'):
  return R.parent/'STAGE_2_WORKFLOW'/p
 if p=='TRIGGER_26900.txt':return R.parent/'STAGE_3_UPLOAD_LAST'/p
 return f
assert all(resolve(k).is_file() and H(resolve(k))==sha for k,sha in seal.items()),'26900 sealed stage files not byte exact'
allow=(R/'26900_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert allow==sorted(set(allow)) and set(allow)==set(seal)|{'26900_HANDOFF_HASHES.sha256'}
assert '26900_REPOSITORY_UPLOAD_ALLOWLIST.txt' in seal
paths=[(R/f'26900_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert all(p==sorted(set(p)) for p in paths)
assert set(paths[0]).isdisjoint(paths[1]+paths[2])
assert set(paths[1]).isdisjoint(paths[2])
assert sorted(paths[0]+paths[1]+paths[2])==allow
assert paths[1]==['.github/workflows/build-26900-iris-rawr.yml']
assert paths[2]==['TRIGGER_26900.txt']
assert not any('build_26900_iris_rawr.sh' in p or 'build_26899_iris_rawr.sh' in p for p in allow)
assert not any('__pycache__' in p or p.endswith('.pyc') for p in allow)
assert any(p=='generate_26900_build.py' for p in paths[0])
print('PASS exact 26900 frozen manifests, all stage hashes and paths, protected 2022, unique trigger, original six-step V2 handoff + 17 runner')
