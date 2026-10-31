#!/usr/bin/env python3
"""Strict eight-file runtime scope, single trigger, exact 3-stage repo layout."""
import pathlib,hashlib,sys,re
R=pathlib.Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 o={}
 for ln in (R/n).read_text().splitlines():
  h,k=ln.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',h) and k not in o
  o[k]=h
 return o
old=load('26890_BASE_FULL_APP.sha256');new=load('26890_EXPECTED_CANDIDATE_FULL_APP.sha256');prot=load('26890_UNCHANGED_PROTECTED.sha256')
changed=sorted(k for k in old if old[k]!=new.get(k))
assert len(old)==len(new)==2025 and len(prot)==2017 and len(changed)==8 and set(old)==set(new)
assert sorted(changed)==(R/'26890_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert all(old[p]==new[p]==h for p,h in prot.items())
assert not (R/'26890_DELETIONS.txt').read_bytes()
payload={p.relative_to(R/'handoff_payload_26890').as_posix() for p in (R/'handoff_payload_26890').rglob('*') if p.is_file()}
assert payload=={x[4:] for x in changed}
assert all(H(R/'handoff_payload_26890'/k[4:])==new[k] for k in changed)
assert (R/'TRIGGER_26890.txt').read_bytes()==b'RUN_26890_B_TONE_TOE_DEFAULT_B_A_NAME_SINGLE_TRIGGER_V1\n'
w=(R/'.github/workflows/build-26890-iris-rawr.yml').read_text()
assert w.startswith('name: Build 26890')
assert '  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - \'TRIGGER_26890.txt\'\n  workflow_dispatch:' in w
push=w.split('  push:\n',1)[1].split('  workflow_dispatch:',1)[0]
assert push.count("      - '")==1 and push.count('TRIGGER_26890.txt')==1
for entry in ['generate_26890_build.py','.github/workflows/build-26890-iris-rawr.yml','TRIGGER_26889.txt']:
 assert entry not in push,('premature Actions trigger',entry)
sequence=['Replay exact SHA-pinned successful 26889 historical workflow','Derive and seal exact-successor guarded 26890 runner','Run inherited guarded 17-stage 26890 build','Verify exactly one intended 26890 APK','Seal exact EXECUTED 26890 runner and compiled evidence','Upload authoritative 26890 proof and APK']
for item in sequence:assert w.count('      - name: '+item)==1,item
assert all(w.index(a)<w.index(b) for a,b in zip(sequence,sequence[1:]))
assert w.count('          bash build_26890_iris_rawr.sh')==1
assert w.count('          python3 -S photon_preserve_successful_runner.py 26890')==1
assert w.count('          python3 -S photon_26890_replay_exact_26889_workflow.py')==1
assert w.count('          python3 -S generate_26890_build.py .')==2
assert 'IrisCamera-0.9726890-26890-iris-rawr-debug.apk' in w
assert 'build_26890_iris_rawr_outputs/' in w
assert '4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73' in w
runner=(R/'26890_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[a-f0-9]{64}',runner) and runner in w
assert not any(x.suffix=='.apk' for x in R.rglob('*') if x.is_file())
if '--draft' in sys.argv:
 assert sys.argv[1:]==['--draft'];print('PASS 26890 DRAFT eight changed 2017 protected single-trigger only');sys.exit(0)
assert len(sys.argv)==1
sealed=load('26890_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and H(R/k)==v for k,v in sealed.items())
upload=(R/'26890_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert set(upload)==set(sealed)|{'26890_HANDOFF_HASHES.sha256','26890_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert '.github/workflows/build-26890-iris-rawr.yml' in upload and 'TRIGGER_26890.txt' in upload
assert 'build_26890_iris_rawr.sh' not in upload
assert not any('__pycache__' in x or x.endswith('.pyc') for x in upload)
print('PASS sealed 26890 frozen source, eight paths, 2017 protected, stage1 ALL, stage2 only YAML, stage3 only trigger')
