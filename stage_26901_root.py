#!/usr/bin/env python3
"""26901 frozen three-stage push-safe handoff against exact successful compiled 26900."""
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
old=man('26901_BASE_FULL_APP.sha256');new=man('26901_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=man('26901_UNCHANGED_PROTECTED.sha256')
mod=sorted(k for k in old.keys()&new.keys() if old[k]!=new[k]);add=sorted(new.keys()-old.keys());delete=sorted(old.keys()-new.keys())
assert len(old)==len(new)==2026 and len(pro)==2020
assert len(mod)==6 and not add and not delete
assert mod==(R/'26901_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert not (R/'26901_ADDITIONS.txt').read_bytes() and not (R/'26901_DELETIONS.txt').read_bytes()
assert set(pro)==set(old)-set(mod) and all(pro[k]==old[k]==new[k] for k in pro)
pay=R/'handoff_payload_26901'
assert {p.relative_to(pay).as_posix() for p in pay.rglob('*') if p.is_file()}=={p[4:] for p in mod}
assert all(H(pay/k[4:])==new[k] for k in mod)
assert 'VERSION_NAME=0.9726901' in (pay/'version.properties').read_text()
assert 'VERSION_BUILD=26901' in (pay/'version.properties').read_text()
w=R/'.github/workflows/build-26901-iris-rawr.yml'
if not w.is_file():w=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26901-iris-rawr.yml'
assert w.is_file()
s=w.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26901.txt'\n"
assert s.count('      - name: ')==6
steps=('Replay exact successful 26900 parent runner','Derive SHA-sealed 26901 successor guarded runner','Run inherited 17-stage 26901 build','Prove single intended 26901 APK','Seal exact EXECUTED 26901 runner','Upload authoritative 26901 proof and APK')
assert all(s.count('      - name: '+step)==1 for step in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
assert s.count('python3 -S generate_26899_build.py .')==2
assert s.count('python3 -S generate_26900_build.py .')==2
assert s.count('python3 -S generate_26901_build.py .')==2
assert s.count('bash build_26901_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26901')==1
assert 'build_26901_iris_rawr_outputs/' in s and 'IrisCamera-0.9726901-26901-iris-rawr-debug.apk' in s
rsha=(R/'26901_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[0-9a-f]{64}',rsha) and s.count('--expected-sha256 '+rsha)==1
assert '--expected-sha256 1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6' not in s
tr=R/'TRIGGER_26901.txt'
if not tr.is_file():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26901.txt'
assert tr.read_bytes()==b'RUN_26901_B_OFF_FULL_RGB_BICUBIC_UNIVERSAL_LENS_GATE_V1\n'
assert not any(p.suffix=='.apk' for p in R.rglob('*') if p.is_file())
if sys.argv[1:]==['--draft']:
 print('PASS 26901 DRAFT actual successful 26900, 6 changed/2020 protected, lens-relative activation and displayed curve; single trigger');sys.exit(0)
assert not sys.argv[1:]
seal=man('26901_HANDOFF_HASHES.sha256')
def resolve(p):
 f=R/p
 if f.is_file():return f
 if p.startswith('.github/workflows/'):return R.parent/'STAGE_2_WORKFLOW'/p
 if p=='TRIGGER_26901.txt':return R.parent/'STAGE_3_UPLOAD_LAST'/p
 return f
assert all(resolve(k).is_file() and H(resolve(k))==sha for k,sha in seal.items()),'26901 staged bytes failed SHA seal'
allow=(R/'26901_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert allow==sorted(set(allow)) and set(allow)==set(seal)|{'26901_HANDOFF_HASHES.sha256'}
assert '26901_REPOSITORY_UPLOAD_ALLOWLIST.txt' in seal
paths=[(R/f'26901_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert all(p==sorted(set(p)) for p in paths)
assert not set(paths[0])&set(paths[1]+paths[2]) and not set(paths[1])&set(paths[2])
assert sorted(paths[0]+paths[1]+paths[2])==allow
assert paths[1]==['.github/workflows/build-26901-iris-rawr.yml']
assert paths[2]==['TRIGGER_26901.txt']
assert all('build_26901_iris_rawr.sh' not in p and 'build_26900_iris_rawr.sh' not in p for p in allow)
assert not any('__pycache__' in p or p.endswith('.pyc') for p in allow)
assert 'generate_26901_build.py' in paths[0] and 'verify_26901.py' in paths[0]
assert len(paths[0])==25 and len(allow)==27
print('PASS exact 26901 manifests/staged hashes/25+1+1 paths; 2020 protected; single-trigger 6-step workflow, 17-stage archived parent preservation')
