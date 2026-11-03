#!/usr/bin/env python3
"""26898 immutable 3-stage scope/version/source/trigger/hash release gate."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for s in (R/name).read_text().splitlines():
  v,p=s.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',v) and p not in d
  d[p]=v
 return d
old=manifest('26898_BASE_FULL_APP.sha256');new=manifest('26898_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=manifest('26898_UNCHANGED_PROTECTED.sha256')
changed=sorted(k for k in old if old[k]!=new[k])
assert len(old)==len(new)==2025 and len(protected)==2020 and len(changed)==5
assert set(old)==set(new) and set(protected)==set(old)-set(changed)
assert all(old[k]==new[k]==v for k,v in protected.items())
assert changed==(R/'26898_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert all(sha(R/'handoff_payload_26898'/k[4:])==new[k] for k in changed)
assert not (R/'26898_ADDITIONS.txt').read_bytes() and not (R/'26898_DELETIONS.txt').read_bytes()
assert 'VERSION_NAME=0.9726898' in (R/'handoff_payload_26898/version.properties').read_text()
assert 'VERSION_BUILD=26898' in (R/'handoff_payload_26898/version.properties').read_text()
workflow=R/'.github/workflows/build-26898-iris-rawr.yml'
if not workflow.exists():workflow=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26898-iris-rawr.yml'
assert workflow.is_file()
s=workflow.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26898.txt'\n"
assert s.count('      - name: ')==6
names=('Replay SHA-pinned successful 26895 historical runner','Derive SHA-sealed 26898 successor guarded runner','Run inherited 17-stage 26898 build','Prove single intended 26898 APK','Seal exact EXECUTED 26898 runner','Upload authoritative 26898 proof and APK')
assert all(s.count('      - name: '+n)==1 for n in names)
assert all(s.index('      - name: '+n)<s.index('      - name: '+m) for n,m in zip(names,names[1:]))
assert s.count('python3 -S generate_26898_build.py .')==2
assert s.count('bash build_26898_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26898')==1
assert 'IrisCamera-0.9726898-26898-iris-rawr-debug.apk' in s
assert 'build_26898_iris_rawr_outputs/' in s
assert '1a0b521c75e12003e0ab31e91bbe9ab8ae9c85b261ba8988ed37cf2e4cfc8dd3' in s
runner_sha=(R/'26898_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',runner_sha) and runner_sha in s
tr=R/'TRIGGER_26898.txt'
if not tr.exists():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26898.txt'
assert tr.read_bytes()==b'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V1\n'
assert not any(p.suffix=='.apk' for p in R.rglob('*') if p.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26898 draft original compiled 26897 2025 source, 5 intended, 2020 protected');sys.exit(0)
assert sys.argv[1:]==[]
seal=manifest('26898_HANDOFF_HASHES.sha256')
def resolve(p):
 f=R/p
 if f.is_file():return f
 if p.startswith('.github/workflows/'):
  return R.parent/'STAGE_2_WORKFLOW'/p
 if p=='TRIGGER_26898.txt':return R.parent/'STAGE_3_UPLOAD_LAST'/p
 return f
assert all(resolve(p).is_file() and sha(resolve(p))==h for p,h in seal.items()),'26898 sealed staged byte drift'
allow=(R/'26898_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert allow==sorted(set(allow))
assert set(allow)==set(seal)|{'26898_HANDOFF_HASHES.sha256','26898_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26898-iris-rawr.yml' in allow and 'TRIGGER_26898.txt' in allow
assert 'build_26898_iris_rawr.sh' not in allow
assert not any('__pycache__' in p or p.endswith('.pyc') for p in allow)
print('PASS 26898 SHA-sealed 3-stage upload, single trigger, full actual source manifests, exact runner, 2020 protected')
