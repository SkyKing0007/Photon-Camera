#!/usr/bin/env python3
"""26902 exact single-trigger 22+1+1 three-stage handoff gate.
Preserve working 26901 verified 17-stage build/handoff mechanics unchanged.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def man(n):
 d={}
 for line in (R/n).read_text().splitlines():
  h,sep,p=line.partition('  ')
  assert sep=='  ' and re.fullmatch('[0-9a-f]{64}',h) and p and p not in d,(n,line)
  d[p]=h
 return d
old=man('26902_BASE_FULL_APP.sha256');new=man('26902_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=man('26902_UNCHANGED_PROTECTED.sha256')
mod=sorted(k for k in old.keys()&new.keys() if old[k]!=new[k]);add=sorted(new.keys()-old.keys());delete=sorted(old.keys()-new.keys())
assert len(old)==len(new)==2026 and len(pro)==2023
assert len(mod)==3 and not add and not delete
assert mod==(R/'26902_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert not (R/'26902_ADDITIONS.txt').read_bytes() and not (R/'26902_DELETIONS.txt').read_bytes()
assert set(pro)==set(old)-set(mod) and all(pro[k]==old[k]==new[k] for k in pro)
pay=R/'handoff_payload_26902'
assert {p.relative_to(pay).as_posix() for p in pay.rglob('*') if p.is_file()}=={p[4:] for p in mod}
assert all(H(pay/k[4:])==new[k] for k in mod)
assert 'VERSION_NAME=0.9726902' in (pay/'version.properties').read_text()
assert 'VERSION_BUILD=26902' in (pay/'version.properties').read_text()
wf=R/'.github/workflows/build-26902-iris-rawr.yml'
if not wf.is_file():wf=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26902-iris-rawr.yml'
assert wf.is_file()
s=wf.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26902.txt'\n"
assert s.count('      - name: ')==6
steps=('Replay exact successful 26901 parent runner','Derive SHA-sealed 26902 successor guarded runner','Run inherited 17-stage 26902 build','Prove single intended 26902 APK','Seal exact EXECUTED 26902 runner','Upload authoritative 26902 proof and APK')
assert all(s.count('      - name: '+step)==1 for step in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
assert s.count('python3 -S generate_26900_build.py .')==2
assert s.count('python3 -S generate_26901_build.py .')==2
assert s.count('python3 -S generate_26902_build.py .')==2
assert s.count('bash build_26902_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26902')==1
assert 'build_26902_iris_rawr_outputs/' in s and 'IrisCamera-0.9726902-26902-iris-rawr-debug.apk' in s
rsha=(R/'26902_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[0-9a-f]{64}',rsha) and s.count('--expected-sha256 '+rsha)==1
assert '--expected-sha256 bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9' not in s
tr=R/'TRIGGER_26902.txt'
if not tr.is_file():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26902.txt'
assert tr.read_bytes()==b'RUN_26902_B_OFF_LENS_RELATIVE_GENTLE_SHARPEN_V1\n'
assert not any(p.suffix=='.apk' for p in R.rglob('*') if p.is_file())
if sys.argv[1:]==['--draft']:
 print('PASS 26902 draft 3 changed/2023 protected, lens relative gain/radius, sole trigger');sys.exit(0)
assert not sys.argv[1:]
seal=man('26902_HANDOFF_HASHES.sha256')
def resolve(path):
 p=R/path
 if p.is_file():return p
 if path.startswith('.github/workflows/'):return R.parent/'STAGE_2_WORKFLOW'/path
 if path=='TRIGGER_26902.txt':return R.parent/'STAGE_3_UPLOAD_LAST'/path
 return p
assert all(resolve(path).is_file() and H(resolve(path))==sha for path,sha in seal.items())
allow=(R/'26902_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert allow==sorted(set(allow)) and set(allow)==set(seal)|{'26902_HANDOFF_HASHES.sha256'}
assert '26902_REPOSITORY_UPLOAD_ALLOWLIST.txt' in seal
paths=[(R/f'26902_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert all(p==sorted(set(p)) for p in paths)
assert not set(paths[0])&set(paths[1]+paths[2]) and not set(paths[1])&set(paths[2])
assert sorted(paths[0]+paths[1]+paths[2])==allow
assert paths[1]==['.github/workflows/build-26902-iris-rawr.yml']
assert paths[2]==['TRIGGER_26902.txt']
assert all('build_26902_iris_rawr.sh' not in p and 'build_26901_iris_rawr.sh' not in p for p in allow)
assert not any('__pycache__' in p or p.endswith('.pyc') for p in allow)
assert 'generate_26902_build.py' in paths[0] and 'verify_26902.py' in paths[0]
assert len(paths[0])==22 and len(allow)==24,(len(paths[0]),len(allow))
print('PASS 26902 exact SHA-sealed 22+1+1 stages, 2023 protected, sole trigger, six-job-step workflow and archived executed runner')
