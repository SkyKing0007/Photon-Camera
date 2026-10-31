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
old=load('26893_BASE_FULL_APP.sha256');new=load('26893_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=load('26893_UNCHANGED_PROTECTED.sha256')
assert len(old)==len(new)==2025 and len(protected)==2021 and set(old)==set(new)
modified=sorted(k for k in old if old[k]!=new[k]);assert len(modified)==4
assert modified==(R/'26893_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert set(protected)==set(old)-set(modified)
assert all(old[p]==new[p]==v for p,v in protected.items())
assert not (R/'26893_DELETIONS.txt').read_bytes()
payload=R/'handoff_payload_26893';files={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert files=={k[4:] for k in modified}
assert all(H(payload/p)==new['app/'+p] for p in files)
assert (R/'TRIGGER_26893.txt').read_bytes()==b'RUN_26893_BACKLIT_FOREGROUND_DARKEN_ONLY_CONTRAST_V1\n'
assert (R/'TRIGGER_26893_RETRY_V2.txt').read_bytes()==b'RUN_26893_BACKLIT_FOREGROUND_DARKEN_ONLY_CONTRAST_V2\n'
workflow=R/'.github/workflows/build-26893-iris-rawr.yml'
w=workflow.read_text()
assert w.startswith('name: Build 26893')
assert "  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26893_RETRY_V2.txt'\n  workflow_dispatch:" in w
p=w.split('  push:\n',1)[1].split('  workflow_dispatch:',1)[0]
assert p.count("      - '")==1 and p.count('TRIGGER_26893_RETRY_V2.txt')==1
assert all(x not in p for x in ['generate_26893_build.py','handoff_payload_26893','build-26893-iris-rawr.yml','TRIGGER_26893.txt'])
seq=['Replay SHA-pinned successful 26892 historical runner','Derive SHA-sealed 26893 successor guarded runner','Run inherited 17-stage 26893 build','Prove single intended 26893 APK','Seal exact EXECUTED 26893 runner','Upload authoritative 26893 proof and APK']
for x in seq: assert w.count('      - name: '+x)==1,x
assert all(w.index(a)<w.index(b) for a,b in zip(seq,seq[1:]))
assert w.count('          bash build_26893_iris_rawr.sh')==1
assert w.count('          python3 -S generate_26893_build.py .')==2
assert w.count('          python3 -S photon_preserve_successful_runner.py 26893')==1
assert 'IrisCamera-0.9726893-26893-iris-rawr-debug.apk' in w
assert 'build_26893_iris_rawr_outputs/' in w
assert '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' in w
runner=(R/'26893_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',runner) and runner in w
assert not any(f.suffix=='.apk' for f in R.rglob('*') if f.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft']; print('PASS 26893 DRAFT 4 paths/2021 protected/3-stage trigger');sys.exit(0)
assert len(sys.argv)==1
sealed=load('26893_HANDOFF_HASHES.sha256');assert all((R/p).is_file() and H(R/p)==v for p,v in sealed.items())
upload=(R/'26893_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert set(upload)==set(sealed)|{'26893_HANDOFF_HASHES.sha256','26893_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26893-iris-rawr.yml' in upload and 'TRIGGER_26893.txt' in upload and 'TRIGGER_26893_RETRY_V2.txt' in upload
assert 'build_26893_iris_rawr.sh' not in upload and 'build_26890_iris_rawr.sh' not in upload
assert not any('__pycache__' in x or x.endswith('.pyc') for x in upload)
print('PASS sealed four changes, 2021 protected, all three stages, trigger-only path filter, deterministic runner SHA')
