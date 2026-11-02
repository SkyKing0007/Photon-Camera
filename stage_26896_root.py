#!/usr/bin/env python3
"""26896 exact three-stage repository upload, authority, historical revert, SHA, single-trigger checks."""
from pathlib import Path
import hashlib,sys,re
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 d={}
 for line in (R/name).read_text().splitlines():
  v,p=line.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',v) and p not in d;d[p]=v
 return d
old=load('26896_BASE_FULL_APP.sha256');new=load('26896_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=load('26896_UNCHANGED_PROTECTED.sha256')
assert len(old)==2025 and len(new)==2025 and len(pro)==2014
modified=sorted(p for p in set(old)|set(new) if old.get(p)!=new.get(p))
assert len(modified)==11 and modified==(R/'26896_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert not set(old)-set(new)
assert not set(new)-set(old)
assert set(pro)==set(old)-set(modified)
assert all(old[p]==new[p]==h for p,h in pro.items())
assert (R/'26896_ADDITIONS.txt').read_bytes()==b''
assert (R/'26896_DELETIONS.txt').read_bytes()==b''
payload=R/'handoff_payload_26896'
files={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert files=={p.removeprefix('app/') for p in modified}
assert all(H(payload/p)==new['app/'+p] for p in files)
assert 'VERSION_NAME=0.9726896' in (payload/'version.properties').read_text()
assert 'VERSION_BUILD=26896' in (payload/'version.properties').read_text()
workflow=R/'.github/workflows/build-26896-iris-rawr.yml'
if not workflow.exists():workflow=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26896-iris-rawr.yml'
assert workflow.is_file();w=workflow.read_text()
assert w.startswith('name: Build 26896')
start=w.index('  push:\n');end=w.index('  workflow_dispatch:',start)
assert w[start:end]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26896.txt'\n"
assert w.count("      - 'TRIGGER_26896.txt'")==1
assert w.count('      - name: ')==6
seq=['Replay SHA-pinned successful 26894 historical runner','Derive SHA-sealed 26896 successor guarded runner','Run inherited 17-stage 26896 build','Prove single intended 26896 APK','Seal exact EXECUTED 26896 runner','Upload authoritative 26896 proof and APK']
assert all(w.count('      - name: '+x)==1 for x in seq)
assert all(w.index(a)<w.index(b) for a,b in zip(seq,seq[1:]))
assert w.count('          python3 -S generate_26896_build.py .')==2
assert w.count('          bash build_26896_iris_rawr.sh')==1
assert w.count('          python3 -S photon_preserve_successful_runner.py 26896')==1
assert 'IrisCamera-0.9726896-26896-iris-rawr-debug.apk' in w
assert 'build_26896_iris_rawr_outputs/' in w
assert 'a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b' in w
sha=(R/'26896_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',sha) and sha in w
trigger=R/'TRIGGER_26896.txt'
if not trigger.exists():trigger=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26896.txt'
assert trigger.read_bytes()==b'RUN_26896_PIXEL_MOTION_GPU_BUDGET_SPEKTRA_NATIVE_RES_AND_SAVE_V1\n'
assert not any(f.suffix=='.apk' for f in R.rglob('*') if f.is_file())
sealed=load('26896_HANDOFF_HASHES.sha256')
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26896 DRAFT 11 existing changes/zero additions/deletions/2014 protected/one trigger');sys.exit(0)
assert sys.argv[1:]==[]
# At archive validation the workflow and trigger are in neighboring stages, not root.
def resolve(p):
 r=R/p
 if r.exists():return r
 if p.startswith('.github/workflows/'):
  r=R.parent/'STAGE_2_WORKFLOW'/p
 elif p=='TRIGGER_26896.txt':
  r=R.parent/'STAGE_3_UPLOAD_LAST'/p
 return r
assert all(resolve(p).is_file() and H(resolve(p))==h for p,h in sealed.items()),'sealed upload SHA mismatch'
list_paths=(R/'26896_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert list_paths==sorted(set(list_paths))
assert set(list_paths)==set(sealed)|{'26896_HANDOFF_HASHES.sha256','26896_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26896-iris-rawr.yml' in list_paths and 'TRIGGER_26896.txt' in list_paths
assert 'build_26896_iris_rawr.sh' not in list_paths and 'build_26895_iris_rawr.sh' not in list_paths
assert not any('__pycache__' in p or p.endswith('.pyc') for p in list_paths)
print('PASS 26896 exact 26895 compiled source, 11 changed, 2014 protected, zero additions or deletions, sealed three stages')
