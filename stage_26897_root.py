#!/usr/bin/env python3
"""Exact three-stage 26897 SHA seal, single trigger, 26895 rollback source protection."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def read(name):
 d={}
 for ln in (R/name).read_text().splitlines():
  v,p=ln.split('  ',1);assert p not in d and re.fullmatch('[a-f0-9]{64}',v);d[p]=v
 return d
old=read('26897_BASE_FULL_APP.sha256');new=read('26897_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=read('26897_UNCHANGED_PROTECTED.sha256')
changed=[p for p in sorted(old) if old.get(p)!=new.get(p)]
assert len(old)==len(new)==2025 and len(pro)==2022 and len(changed)==3
assert set(old)==set(new) and set(pro)==set(old)-set(changed)
assert all(old[p]==new[p]==h for p,h in pro.items())
assert changed==(R/'26897_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert all(H(R/'handoff_payload_26897'/p[4:])==new[p] for p in changed)
assert not (R/'26897_ADDITIONS.txt').read_bytes() and not (R/'26897_DELETIONS.txt').read_bytes()
assert 'VERSION_NAME=0.9726897' in (R/'handoff_payload_26897/version.properties').read_text()
assert 'VERSION_BUILD=26897' in (R/'handoff_payload_26897/version.properties').read_text()
w=R/'.github/workflows/build-26897-iris-rawr.yml'
if not w.exists():w=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26897-iris-rawr.yml'
assert w.is_file();s=w.read_text()
assert s.startswith('name: Build 26897')
a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26897.txt'\n"
assert s.count('      - name: ')==6
stages=['Replay SHA-pinned successful 26895 historical runner','Derive SHA-sealed 26897 successor guarded runner','Run inherited 17-stage 26897 build','Prove single intended 26897 APK','Seal exact EXECUTED 26897 runner','Upload authoritative 26897 proof and APK']
assert all(s.count('      - name: '+x)==1 for x in stages)
assert all(s.index(a)<s.index(b) for a,b in zip(stages,stages[1:]))
assert s.count('          python3 -S generate_26897_build.py .')==2
assert s.count('          bash build_26897_iris_rawr.sh')==1
assert s.count('          python3 -S photon_preserve_successful_runner.py 26897')==1
assert 'IrisCamera-0.9726897-26897-iris-rawr-debug.apk' in s
assert 'build_26897_iris_rawr_outputs/' in s
assert 'a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b' in s
sha=(R/'26897_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',sha) and sha in s
tr=R/'TRIGGER_26897.txt'
if not tr.exists():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26897.txt'
assert tr.read_bytes()==b'RUN_26897_INDEPENDENT_MOTION_DNG_SABRE_BEFORE_B_V1\n'
assert not any(p.suffix=='.apk' for p in R.rglob('*') if p.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26897 draft 3 files, 2022 protected, exact 26895 parent and one trigger');sys.exit()
assert sys.argv[1:]==[]
seal=read('26897_HANDOFF_HASHES.sha256')
def resolve(p):
 f=R/p
 if f.exists():return f
 if p.startswith('.github/workflows/'):
  return R.parent/'STAGE_2_WORKFLOW'/p
 if p=='TRIGGER_26897.txt':return R.parent/'STAGE_3_UPLOAD_LAST'/p
 return f
assert all(resolve(p).is_file() and H(resolve(p))==h for p,h in seal.items())
u=(R/'26897_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert u==sorted(set(u))
assert set(u)==set(seal)|{'26897_HANDOFF_HASHES.sha256','26897_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26897-iris-rawr.yml' in u and 'TRIGGER_26897.txt' in u
assert 'build_26897_iris_rawr.sh' not in u and 'build_26895_iris_rawr.sh' not in u
assert not any('__pycache__' in p or p.endswith('.pyc') for p in u)
print('PASS 26897 sealed 3 stages, 2025 compiled source, 3 modified, 2022 protected, one exact trigger')
