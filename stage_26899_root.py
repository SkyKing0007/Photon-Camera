#!/usr/bin/env python3
"""Exact 3-stage SHA-sealed 26899 delivery gate, no early workflow push trigger."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def man(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,rel=line.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',h) and rel not in d
  d[rel]=h
 return d
old=man('26899_BASE_FULL_APP.sha256');new=man('26899_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=man('26899_UNCHANGED_PROTECTED.sha256')
mod=sorted(p for p in old.keys()&new.keys() if old[p]!=new[p]);add=sorted(new.keys()-old.keys());delete=sorted(old.keys()-new.keys())
assert len(old)==2025 and len(new)==2026 and len(pro)==2021
assert len(mod)==4 and len(add)==1 and not delete
assert sorted(mod+add)==(R/'26899_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert (R/'26899_ADDITIONS.txt').read_text().splitlines()==add
assert not (R/'26899_DELETIONS.txt').read_bytes()
assert all(pro[k]==old[k]==new[k] for k in pro)
assert {p.relative_to(R/'handoff_payload_26899').as_posix() for p in (R/'handoff_payload_26899').rglob('*') if p.is_file()}=={x[4:] for x in mod+add}
assert all(H(R/'handoff_payload_26899'/x[4:])==new[x] for x in mod+add)
assert 'VERSION_NAME=0.9726899' in (R/'handoff_payload_26899/version.properties').read_text()
assert 'VERSION_BUILD=26899' in (R/'handoff_payload_26899/version.properties').read_text()
wf=R/'.github/workflows/build-26899-iris-rawr.yml'
if not wf.exists():wf=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26899-iris-rawr.yml'
assert wf.is_file()
s=wf.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26899_V2.txt'\n"
assert s.count('      - name: ')==6
steps=('Replay SHA-pinned successful 26898 historical runner','Derive SHA-sealed 26899 successor guarded runner','Run inherited 17-stage 26899 build','Prove single intended 26899 APK','Seal exact EXECUTED 26899 runner','Upload authoritative 26899 proof and APK')
assert all(s.count('      - name: '+x)==1 for x in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
assert s.count('python3 -S generate_26899_build.py .')==2
assert s.count('bash build_26899_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26899')==1
assert 'IrisCamera-0.9726899-26899-iris-rawr-debug.apk' in s
assert 'build_26899_iris_rawr_outputs/' in s
assert '9c97ed074b1d4ec48528e1d63103aed3198d44406a0c3f4820ad3309c203c99a' in s
expected=(R/'26899_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[0-9a-f]{64}',expected) and expected in s
tr=R/'TRIGGER_26899_V2.txt'
if not tr.exists():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26899_V2.txt'
assert tr.read_bytes()==b'RUN_26899_B_OFF_ONLY_ZOOM_LUMA_SHARPEN_V2\n'
# The failed V1 exact-byte trigger stays unchanged in the repository.
original_trigger=R/'TRIGGER_26899.txt'
if original_trigger.exists():
 assert original_trigger.read_bytes()==b'RUN_26899_B_OFF_ONLY_ZOOM_LUMA_SHARPEN_V1\n', '26899 V1 trigger must remain untouched'
assert not any(x.suffix=='.apk' for x in R.rglob('*') if x.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26899 draft candidate 2025->2026, B SR OFF one new GLSL, 2021 protected, correct six-step workflow');sys.exit(0)
assert sys.argv[1:]==[]
seal=man('26899_HANDOFF_HASHES.sha256')
def resolve(p):
 f=R/p
 if f.is_file():return f
 if p.startswith('.github/workflows/'):
  return R.parent/'STAGE_2_WORKFLOW'/p
 if p=='TRIGGER_26899_V2.txt':return R.parent/'STAGE_3_UPLOAD_LAST'/p
 return f
assert all(resolve(p).is_file() and H(resolve(p))==h for p,h in seal.items()),'26899 staged byte/hash mismatch'
allow=(R/'26899_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert allow==sorted(set(allow))
assert set(allow)==set(seal)|{'26899_HANDOFF_HASHES.sha256','26899_REPOSITORY_UPLOAD_ALLOWLIST.txt','TRIGGER_26899.txt'}
assert '.github/workflows/build-26899-iris-rawr.yml' in allow and 'TRIGGER_26899_V2.txt' in allow and 'TRIGGER_26899.txt' in allow
assert 'build_26899_iris_rawr.sh' not in allow
assert not any('__pycache__' in x or x.endswith('.pyc') for x in allow)
paths=[(R/f'26899_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert set(sum(paths,[]))==set(allow)-{'TRIGGER_26899.txt'}
assert set(paths[0]).isdisjoint(paths[1]+paths[2])
assert paths[1]==['.github/workflows/build-26899-iris-rawr.yml']
assert paths[2]==['TRIGGER_26899_V2.txt']
print('PASS 26899 3-stage exact SHA-sealed output; full source manifest, frozen protected, B-only 1.1-30+ zoom; exact trigger/runner')
