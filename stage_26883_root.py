#!/usr/bin/env python3
"""26883 three-stage root namespace, exact 2009 compiled source and 4-file transform."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for row in (R/name).read_text().splitlines():
  h,k=row.split('  ',1);assert k not in d;d[k]=h
 return d
allow=(R/'26883_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)==4 and allow==sorted(set(allow))
assert (R/'26883_DELETIONS.txt').read_bytes()==b''
old=manifest('26883_BASE_26882_FULL_APP.sha256');new=manifest('26883_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=manifest('26883_UNCHANGED_PROTECTED.sha256')
assert len(old)==len(new)==2009 and len(protected)==2005
assert set(allow)=={k for k in old if old[k]!=new[k]}
assert set(old)==set(new) and set(protected)==set(old)-set(allow)
assert all(old[k]==new[k]==v for k,v in protected.items())
payload=R/'handoff_payload_26883'
actual={'app/'+p.relative_to(payload/'app').as_posix() for p in (payload/'app').rglob('*') if p.is_file()}
assert actual==set(allow),('unexpected runtime payload files',actual^set(allow))
assert all(sha(payload/k)==new[k] for k in allow)
assert manifest('26883_PAYLOAD_SHA256.txt')=={'handoff_payload_26883/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26883.txt').read_bytes()==b'RUN_26883_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1\n'
assert (R/'.github/workflows/build-26883-iris-rawr.yml').read_text().count('TRIGGER_26883.txt')>=2
for n in ('generate_26883_build.py','verify_26883_candidate.py','verify_26883_patches.py','verify_26883_semantics.py','verify_26883_expanded_glsl.py','regressions/26883_successor_contract.py'):
 assert (R/n).is_file(),('missing new guarded validator',n)
package=manifest('26883_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==h for k,h in package.items())
allowed=set((R/'26883_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
expected=set(package)|{'26883_HANDOFF_HASHES.sha256','26883_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert allowed==expected,('strict upload scope mismatch',sorted(allowed^expected))
assert all(not k.startswith('app/') for k in allowed),'no direct repository app source writes'
assert not any('__pycache__' in k.split('/') or k.endswith(('.pyc','.pyo')) for k in set(package)|allowed),'Python cache in sealed handoff'
assert 'build_26883_iris_rawr.sh' not in allowed,'runner MUST be generated from prior successful 26882 in Actions'
print('PASS 26883 strict 4-source allowlist / 2005 protected 0 additions-deletions / exact cache-free three-stage trigger handoff')
