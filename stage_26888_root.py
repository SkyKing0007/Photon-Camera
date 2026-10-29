#!/usr/bin/env python3
"""Fail-closed 26888 3-stage sealed root and exact successful 26887 predecessor chain."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def man(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,k=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and k not in d
  d[k]=h
 return d
old=man('26888_BASE_26887_FULL_APP.sha256');new=man('26888_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=man('26888_UNCHANGED_PROTECTED.sha256')
allow=(R/'26888_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2020 and len(new)==2024 and len(protect)==2015
existing={k for k in old if old.get(k)!=new.get(k)};added=set(new)-set(old)
assert len(existing)==5 and len(added)==4 and not (set(old)-set(new))
assert allow==sorted(existing|added) and 'app/version.properties' in existing
assert set(protect)==set(old)-existing and all(old[k]==new[k]==h for k,h in protect.items())
assert (R/'26888_DELETIONS.txt').read_bytes()==b''
payload=R/'handoff_payload_26888';actual={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
assert actual==set(allow)
assert all(sha(payload/k)==new[k] for k in allow)
assert man('26888_PAYLOAD_SHA256.txt')=={'handoff_payload_26888/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26888.txt').read_bytes()==b'RUN_26888_B_OFF_INDEPENDENT_MOTION_SUPPORT_V1\n'
w=(R/'.github/workflows/build-26888-iris-rawr.yml').read_text()
assert w.count('      - name: Run inherited guarded 17-stage 26888 build')==1
assert w.count('      - name: Seal exact EXECUTED 26888 runner and compiled evidence')==1
assert w.count('      - name: Upload authoritative 26888 proof and APK')==1
assert w.index('      - name: Verify exactly one intended 26888 APK')<w.index('      - name: Seal exact EXECUTED 26888 runner')<w.index('      - name: Upload authoritative 26888 proof and APK')
assert w.count('          python3 -S generate_26887_build.py .')==2
assert w.count('          python3 -S generate_26888_build.py .')==2
assert w.count('          bash build_26888_iris_rawr.sh')==1
assert w.count("      - 'TRIGGER_26888.txt'")==1
assert w.count("      - 'generate_26888_build.py'")==1
assert w.count("      - '.github/workflows/build-26888-iris-rawr.yml'")==1
assert w.count('          python3 -S photon_preserve_successful_runner.py 26888')==1
assert w.count('test "$(find handoff_payload_26888 -type f | wc -l)" -eq 9')==1
assert 'f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56' in w
assert 'IrisCamera-0.9726888-26888-iris-rawr-debug.apk' in w
runner_expected=(R/'26888_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
assert re.fullmatch('[0-9a-f]{64}',runner_expected)
assert runner_expected in w
assert not any(p.suffix.lower()=='.apk' for p in R.rglob('*') if p.is_file())
if '--draft-scope' in sys.argv:
 assert sys.argv[1:]==['--draft-scope']
 print('PASS 26888 frozen root candidate 2020->2024 scope and 17-stage workflow; draft only')
 sys.exit(0)
assert sys.argv[1:]==[]
sealed=man('26888_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==h for k,h in sealed.items()),'sealed 26888 staged bytes tampered'
upload=(R/'26888_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert set(upload)==set(sealed)|{'26888_HANDOFF_HASHES.sha256','26888_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert 'build_26888_iris_rawr.sh' not in upload and 'build_26887_iris_rawr.sh' not in upload
assert not any('__pycache__' in k or k.endswith('.pyc') for k in upload)
print('PASS sealed 26888 repository root, exact 9 changed runtime payload, runner/Actions/archival gates; real compilers still Actions-only')
