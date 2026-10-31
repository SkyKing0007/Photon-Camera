#!/usr/bin/env python3
"""Strict frozen 26894 successor runtime, repo file/three-stage/trigger safety."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 d={}
 for line in (R/name).read_text().splitlines():
  x,p=line.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',x) and p not in d;d[p]=x
 return d
old=load('26894_BASE_FULL_APP.sha256');new=load('26894_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=load('26894_UNCHANGED_PROTECTED.sha256')
assert len(old)==2025 and len(new)==2026 and len(protected)==2021
modified=sorted(k for k in new if old.get(k)!=new[k]);assert len(modified)==5
assert modified==(R/'26894_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert set(new)-set(old)=={'app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl'}
assert not set(old)-set(new)
assert set(protected)==set(old)-set(modified)
assert all(old[p]==new[p]==v for p,v in protected.items())
assert (R/'26894_ADDITIONS.txt').read_text().splitlines()==['app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl']
assert (R/'26894_DELETIONS.txt').read_bytes()==b''
payload=R/'handoff_payload_26894';files={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert files=={k[4:] for k in modified}
assert all(H(payload/p)==new['app/'+p] for p in files)
assert (R/'TRIGGER_26894.txt').read_bytes()==b'RUN_26894_SPATIAL_FOREGROUND_NOISE_SAFE_FLAT_CONTRAST_V1\n'
assert (R/'TRIGGER_26894_RETRY_V2.txt').read_bytes()==b'RUN_26894_SPATIAL_FOREGROUND_NOISE_SAFE_FLAT_CONTRAST_V2\n'
workflow=R/'.github/workflows/build-26894-iris-rawr.yml';w=workflow.read_text()
assert w.startswith('name: Build 26894')
trigger="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26894_RETRY_V2.txt'\n  workflow_dispatch:"
assert trigger in w
p=w.split('  push:\n',1)[1].split('  workflow_dispatch:',1)[0]
assert p.count("      - '")==1 and p.count('TRIGGER_26894_RETRY_V2.txt')==1
assert all(x not in p for x in ['generate_26894_build.py','handoff_payload_26894','build-26894-iris-rawr.yml','26894_HANDOFF_HASHES.sha256'])
seq=['Replay SHA-pinned successful 26893 historical runner','Derive SHA-sealed 26894 successor guarded runner','Run inherited 17-stage 26894 build','Prove single intended 26894 APK','Seal exact EXECUTED 26894 runner','Upload authoritative 26894 proof and APK']
for x in seq:assert w.count('      - name: '+x)==1,x
assert all(w.index(a)<w.index(b) for a,b in zip(seq,seq[1:]))
assert w.count('          bash build_26894_iris_rawr.sh')==1
assert w.count('          python3 -S generate_26894_build.py .')==2
assert w.count('          python3 -S photon_preserve_successful_runner.py 26894')==1
assert 'IrisCamera-0.9726894-26894-iris-rawr-debug.apk' in w and 'build_26894_iris_rawr_outputs/' in w
assert '9a70b375fd5f0a1e5148cef7e4640b4014fe0a24d8e5f38fcada15bbc0713956' in w
runner=(R/'26894_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0];assert re.fullmatch('[a-f0-9]{64}',runner) and runner in w
assert not any(f.suffix=='.apk' for f in R.rglob('*') if f.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26894 DRAFT 5 paths/2021 protected/3 stages');sys.exit(0)
assert len(sys.argv)==1
sealed=load('26894_HANDOFF_HASHES.sha256');assert all((R/p).is_file() and H(R/p)==v for p,v in sealed.items())
upload=(R/'26894_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert set(upload)==set(sealed)|{'26894_HANDOFF_HASHES.sha256','26894_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26894-iris-rawr.yml' in upload and 'TRIGGER_26894.txt' in upload and 'TRIGGER_26894_RETRY_V2.txt' in upload
assert 'build_26894_iris_rawr.sh' not in upload and 'build_26893_iris_rawr.sh' not in upload
assert not any('__pycache__' in x or x.endswith('.pyc') for x in upload)
print('PASS 26894 full sealed source scope, 2021 protected, sole trigger, exact derived runner, three stages')
