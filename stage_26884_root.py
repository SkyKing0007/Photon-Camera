#!/usr/bin/env python3
"""26884 three-stage root namespace, exact 2009 compiled source and 4-file transform."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for row in (R/name).read_text().splitlines():
  h,k=row.split('  ',1);assert k not in d;d[k]=h
 return d
allow=(R/'26884_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)==3 and allow==sorted(set(allow))
assert (R/'26884_DELETIONS.txt').read_bytes()==b''
old=manifest('26884_BASE_26883_FULL_APP.sha256');new=manifest('26884_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=manifest('26884_UNCHANGED_PROTECTED.sha256')
assert len(old)==len(new)==2009 and len(protected)==2006
assert set(allow)=={k for k in old if old[k]!=new[k]}
assert set(old)==set(new) and set(protected)==set(old)-set(allow)
assert all(old[k]==new[k]==v for k,v in protected.items())
payload=R/'handoff_payload_26884'
actual={'app/'+p.relative_to(payload/'app').as_posix() for p in (payload/'app').rglob('*') if p.is_file()}
assert actual==set(allow),('unexpected runtime payload files',actual^set(allow))
assert all(sha(payload/k)==new[k] for k in allow)
assert manifest('26884_PAYLOAD_SHA256.txt')=={'handoff_payload_26884/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26884.txt').read_bytes()==b'RUN_26884_RAWR_HIGHLIGHT_OFF_SHARED_B_V1\n'
assert (R/'.github/workflows/build-26884-iris-rawr.yml').read_text().count('TRIGGER_26884.txt')>=2
for n in ('generate_26884_build.py','verify_26884_candidate.py','verify_26884_patches.py','verify_26884_semantics.py','verify_26884_expanded_glsl.py','regressions/26884_successor_contract.py'):
 assert (R/n).is_file(),('missing new guarded validator',n)
package=manifest('26884_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==h for k,h in package.items())
allowed=set((R/'26884_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
expected=set(package)|{'26884_HANDOFF_HASHES.sha256','26884_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert allowed==expected,('strict upload scope mismatch',sorted(allowed^expected))
assert all(not k.startswith('app/') for k in allowed),'no direct repository app source writes'
assert not any('__pycache__' in k.split('/') or k.endswith(('.pyc','.pyo')) for k in set(package)|allowed),'Python cache in sealed handoff'
assert 'build_26884_iris_rawr.sh' not in allowed,'runner MUST be generated from prior successful 26883 in Actions'
print('PASS 26884 strict 3-source allowlist / 2006 protected 0 additions-deletions / exact cache-free three-stage trigger handoff')
