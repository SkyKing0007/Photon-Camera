#!/usr/bin/env python3
"""Validate exact successor six-source provenance and three-stage trigger order."""
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
old=load('26891_BASE_FULL_APP.sha256');new=load('26891_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=load('26891_UNCHANGED_PROTECTED.sha256')
assert len(old)==len(new)==2025 and len(protected)==2019 and set(old)==set(new)
modified=sorted(k for k in old if old[k]!=new[k]);assert len(modified)==6
assert modified==(R/'26891_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert set(protected)==set(old)-set(modified)
assert all(old[p]==new[p]==v for p,v in protected.items())
assert not (R/'26891_DELETIONS.txt').read_bytes()
payload=R/'handoff_payload_26891';files={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert files=={k[4:] for k in modified}
assert all(H(payload/p)==new['app/'+p] for p in files)
assert (R/'TRIGGER_26891.txt').read_bytes()==b'RUN_26891_B_OFF_HDRQ_RAWR_NORMALIZE_PRESERVE_26890_V1\n'
workflow=R/'.github/workflows/build-26891-iris-rawr.yml'
w=workflow.read_text()
assert w.startswith('name: Build 26891')
assert "  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26891.txt'\n  workflow_dispatch:" in w
p=w.split('  push:\n',1)[1].split('  workflow_dispatch:',1)[0]
assert p.count("      - '")==1 and p.count('TRIGGER_26891.txt')==1
assert all(x not in p for x in ['generate_26891_build.py','handoff_payload_26891','build-26891-iris-rawr.yml'])
seq=['Replay SHA-pinned successful 26890 historical runner','Derive SHA-sealed 26891 successor guarded runner','Run inherited 17-stage 26891 build','Prove single intended 26891 APK','Seal exact EXECUTED 26891 runner','Upload authoritative 26891 proof and APK']
for x in seq: assert w.count('      - name: '+x)==1,x
assert all(w.index(a)<w.index(b) for a,b in zip(seq,seq[1:]))
assert w.count('          bash build_26891_iris_rawr.sh')==1
assert w.count('          python3 -S generate_26891_build.py .')==2
assert w.count('          python3 -S photon_preserve_successful_runner.py 26891')==1
assert 'IrisCamera-0.9726891-26891-iris-rawr-debug.apk' in w
assert 'build_26891_iris_rawr_outputs/' in w
assert '525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df' in w
runner=(R/'26891_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',runner) and runner in w
assert not any(f.suffix=='.apk' for f in R.rglob('*') if f.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft']; print('PASS 26891 DRAFT 6 paths/2019 protected/3-stage trigger');sys.exit(0)
assert len(sys.argv)==1
sealed=load('26891_HANDOFF_HASHES.sha256');assert all((R/p).is_file() and H(R/p)==v for p,v in sealed.items())
upload=(R/'26891_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert set(upload)==set(sealed)|{'26891_HANDOFF_HASHES.sha256','26891_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26891-iris-rawr.yml' in upload and 'TRIGGER_26891.txt' in upload
assert 'build_26891_iris_rawr.sh' not in upload and 'build_26890_iris_rawr.sh' not in upload
assert not any('__pycache__' in x or x.endswith('.pyc') for x in upload)
print('PASS sealed six changes, 2019 protected, all three stages, trigger-only path filter, deterministic runner SHA')
