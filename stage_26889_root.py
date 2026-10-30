#!/usr/bin/env python3
"""Fail closed: 26889 three-stage root, immutable preceding 26888 runner."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def man(filename):
 out={}
 for line in (R/filename).read_text().splitlines():
  h,k=line.split('  ',1)
  assert re.fullmatch(r'[0-9a-f]{64}',h) and k not in out
  out[k]=h
 return out
old=man('26889_BASE_FULL_APP.sha256');new=man('26889_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=man('26889_UNCHANGED_PROTECTED.sha256')
allow=(R/'26889_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2024 and len(new)==2025 and len(protect)==2015
modified={p for p in old if old[p]!=new.get(p)};added=set(new)-set(old)
assert len(modified)==9 and len(added)==1 and not(set(old)-set(new))
assert allow==sorted(modified|added) and 'app/version.properties' in modified
assert (R/'26889_DELETIONS.txt').read_bytes()==b''
assert set(protect)==set(old)-modified and all(old[p]==new[p]==h for p,h in protect.items())
files={p.relative_to(R/'handoff_payload_26889').as_posix() for p in (R/'handoff_payload_26889').rglob('*') if p.is_file()}
assert files=={p[4:] for p in allow} and len(files)==10
assert all(sha(R/'handoff_payload_26889'/p[4:])==new[p] for p in allow)
assert (R/'TRIGGER_26889.txt').read_bytes()==b'RUN_26889_B_OFF_SHUTTER_ADJACENT_MOTION_LONG_V1\n'
assert (R/'26889_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]=='4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73'
w=(R/'.github/workflows/build-26889-iris-rawr.yml').read_text()
steps=('      - name: Replay exact SHA-pinned successful 26888 historical setup and GLSL cleanup',
       '      - name: Derive and seal exact-successor guarded 26889 runner',
       '      - name: Run inherited guarded 17-stage 26889 build',
       '      - name: Verify exactly one intended 26889 APK',
       '      - name: Seal exact EXECUTED 26889 runner and compiled evidence',
       '      - name: Upload authoritative 26889 proof and APK')
assert all(w.count(s)==1 for s in steps) and all(w.index(a)<w.index(b) for a,b in zip(steps,steps[1:]))
assert w.count('          bash build_26889_iris_rawr.sh')==1
assert w.count('          python3 -S photon_preserve_successful_runner.py 26889')==1
assert w.count('          python3 -S photon_26889_replay_exact_26888_workflow.py')==1
assert w.count('          python3 -S generate_26889_build.py .')==1
assert w.count('          python3 -S stage_26889_root.py')==2
assert w.count("      - 'TRIGGER_26889.txt'")==1
assert '          test -f IrisCamera-0.9726889-26889-iris-rawr-debug.apk' in w
assert 'build_26889_iris_rawr_outputs/' in w
assert '5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753' in w
assert not any(p.suffix=='.apk' for p in R.rglob('*') if p.is_file())
if '--draft-scope' in sys.argv:
 assert sys.argv[1:]==['--draft-scope']
 print('PASS 26889 frozen candidate root, exact parent and chained 17-stage workflow DRAFT')
 sys.exit(0)
assert len(sys.argv)==1
sealed=man('26889_HANDOFF_HASHES.sha256')
assert all((R/p).is_file() and sha(R/p)==h for p,h in sealed.items())
repo=(R/'26889_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert repo==sorted(repo) and set(repo)==set(sealed)|{'26889_HANDOFF_HASHES.sha256','26889_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert 'build_26889_iris_rawr.sh' not in repo and 'build_26888_iris_rawr.sh' not in repo
assert not any('__pycache__' in x or x.endswith('.pyc') for x in repo)
print('PASS 26889 sealed source/trigger/exact original 26888 preparatory workflow, exact 17-stage runner archive after full APK proof')
