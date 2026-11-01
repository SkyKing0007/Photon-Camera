#!/usr/bin/env python3
"""26895 exact three-stage repository upload, authority, historical revert, SHA, single-trigger checks."""
from pathlib import Path
import hashlib,sys,re
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 d={}
 for line in (R/name).read_text().splitlines():
  v,p=line.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',v) and p not in d;d[p]=v
 return d
old=load('26895_BASE_FULL_APP.sha256');new=load('26895_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=load('26895_UNCHANGED_PROTECTED.sha256');hist=load('26895_HISTORICAL_26893_FULL_APP.sha256')
assert len(old)==2026 and len(new)==2025 and len(hist)==2025 and len(pro)==2021
modified=sorted(p for p in set(old)|set(new) if old.get(p)!=new.get(p))
assert len(modified)==5 and modified==(R/'26895_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert set(old)-set(new)=={'app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl'}
assert not set(new)-set(old)
assert set(pro)==set(old)-set(modified)
assert all(old[p]==new[p]==h for p,h in pro.items())
assert all(hist[p]==new[p] for p in new if p not in ['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties'])
assert (R/'26895_ADDITIONS.txt').read_bytes()==b''
assert (R/'26895_DELETIONS.txt').read_text().splitlines()==['app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl']
payload=R/'handoff_payload_26895'
files={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert files=={p.removeprefix('app/') for p in modified if p in new}
assert all(H(payload/p)==new['app/'+p] for p in files)
assert 'VERSION_NAME=0.9726895' in (payload/'version.properties').read_text()
assert 'VERSION_BUILD=26895' in (payload/'version.properties').read_text()
workflow=R/'.github/workflows/build-26895-iris-rawr.yml'
if not workflow.exists():workflow=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26895-iris-rawr.yml'
assert workflow.is_file();w=workflow.read_text()
assert w.startswith('name: Build 26895')
start=w.index('  push:\n');end=w.index('  workflow_dispatch:',start)
assert w[start:end]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26895.txt'\n"
assert w.count("      - 'TRIGGER_26895.txt'")==1
assert w.count('      - name: ')==6
seq=['Replay SHA-pinned successful 26894 historical runner','Derive SHA-sealed 26895 successor guarded runner','Run inherited 17-stage 26895 build','Prove single intended 26895 APK','Seal exact EXECUTED 26895 runner','Upload authoritative 26895 proof and APK']
assert all(w.count('      - name: '+x)==1 for x in seq)
assert all(w.index(a)<w.index(b) for a,b in zip(seq,seq[1:]))
assert w.count('          python3 -S generate_26895_build.py .')==2
assert w.count('          bash build_26895_iris_rawr.sh')==1
assert w.count('          python3 -S photon_preserve_successful_runner.py 26895')==1
assert 'IrisCamera-0.9726895-26895-iris-rawr-debug.apk' in w
assert 'build_26895_iris_rawr_outputs/' in w
assert '1f9dcc045b6ca5fa8928443dcc28b98907b7fad152546d802445b74207244be6' in w
sha=(R/'26895_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',sha) and sha in w
trigger=R/'TRIGGER_26895.txt'
if not trigger.exists():trigger=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26895.txt'
assert trigger.read_bytes()==b'RUN_26895_26893_BASELINE_IRIS_SATURATION_1P14_V1\n'
assert not any(f.suffix=='.apk' for f in R.rglob('*') if f.is_file())
sealed=load('26895_HANDOFF_HASHES.sha256')
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26895 DRAFT 5 source paths/one deletion/2021 protected/one trigger');sys.exit(0)
assert sys.argv[1:]==[]
# At archive validation the workflow and trigger are in neighboring stages, not root.
def resolve(p):
 r=R/p
 if r.exists():return r
 if p.startswith('.github/workflows/'):
  r=R.parent/'STAGE_2_WORKFLOW'/p
 elif p=='TRIGGER_26895.txt':
  r=R.parent/'STAGE_3_UPLOAD_LAST'/p
 return r
assert all(resolve(p).is_file() and H(resolve(p))==h for p,h in sealed.items()),'sealed upload SHA mismatch'
list_paths=(R/'26895_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert list_paths==sorted(set(list_paths))
assert set(list_paths)==set(sealed)|{'26895_HANDOFF_HASHES.sha256','26895_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26895-iris-rawr.yml' in list_paths and 'TRIGGER_26895.txt' in list_paths
assert 'build_26895_iris_rawr.sh' not in list_paths and 'build_26894_iris_rawr.sh' not in list_paths
assert not any('__pycache__' in p or p.endswith('.pyc') for p in list_paths)
print('PASS 26895 exact 26893 source restoration, per-lens saturation, 2021 protected, one deletion, sealed three stages')
