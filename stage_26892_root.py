#!/usr/bin/env python3
"""Validate exact successor four-source provenance and three-stage trigger order."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(fn):
 out={}
 for ln in (R/fn).read_text().splitlines():
  sha,path=ln.split('  ',1)
  assert re.fullmatch('[a-f0-9]{64}',sha) and path not in out
  out[path]=sha
 return out
old=load('26892_BASE_FULL_APP.sha256');new=load('26892_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=load('26892_UNCHANGED_PROTECTED.sha256')
assert len(old)==len(new)==2025 and len(protected)==2021 and set(old)==set(new)
modified=sorted(k for k in old if old[k]!=new[k]);assert len(modified)==4
assert modified==(R/'26892_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert set(protected)==set(old)-set(modified)
assert all(old[p]==new[p]==v for p,v in protected.items())
assert not (R/'26892_DELETIONS.txt').read_bytes()
payload=R/'handoff_payload_26892';files={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert files=={k[4:] for k in modified}
assert all(H(payload/p)==new['app/'+p] for p in files)
assert (R/'TRIGGER_26892.txt').read_bytes()==b'RUN_26892_SCENE_ADAPTIVE_SDR_BACKLIGHT_CONTRAST_V1\n'
workflow=R/'.github/workflows/build-26892-iris-rawr.yml'
w=workflow.read_text()
assert w.startswith('name: Build 26892')
assert "  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26892.txt'\n  workflow_dispatch:" in w
p=w.split('  push:\n',1)[1].split('  workflow_dispatch:',1)[0]
assert p.count("      - '")==1 and p.count('TRIGGER_26892.txt')==1
assert all(x not in p for x in ['generate_26892_build.py','handoff_payload_26892','build-26892-iris-rawr.yml'])
seq=['Replay SHA-pinned successful 26891 historical runner','Derive SHA-sealed 26892 successor guarded runner','Run inherited 17-stage 26892 build','Prove single intended 26892 APK','Seal exact EXECUTED 26892 runner','Upload authoritative 26892 proof and APK']
for x in seq: assert w.count('      - name: '+x)==1,x
assert all(w.index(a)<w.index(b) for a,b in zip(seq,seq[1:]))
assert w.count('          bash build_26892_iris_rawr.sh')==1
assert w.count('          python3 -S generate_26892_build.py .')==2
assert w.count('          python3 -S photon_preserve_successful_runner.py 26892')==1
assert 'IrisCamera-0.9726892-26892-iris-rawr-debug.apk' in w
assert 'build_26892_iris_rawr_outputs/' in w
assert 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' in w
runner=(R/'26892_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',runner) and runner in w
assert not any(f.suffix=='.apk' for f in R.rglob('*') if f.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft']; print('PASS 26892 DRAFT 4 paths/2021 protected/3-stage trigger');sys.exit(0)
assert len(sys.argv)==1
sealed=load('26892_HANDOFF_HASHES.sha256');assert all((R/p).is_file() and H(R/p)==v for p,v in sealed.items())
upload=(R/'26892_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert set(upload)==set(sealed)|{'26892_HANDOFF_HASHES.sha256','26892_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26892-iris-rawr.yml' in upload and 'TRIGGER_26892.txt' in upload
assert 'build_26892_iris_rawr.sh' not in upload and 'build_26890_iris_rawr.sh' not in upload
assert not any('__pycache__' in x or x.endswith('.pyc') for x in upload)
print('PASS sealed four changes, 2021 protected, all three stages, trigger-only path filter, deterministic runner SHA')
