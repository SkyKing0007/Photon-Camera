#!/usr/bin/env python3
"""26882 staging: exact root replacement files, strict runtime namespace and trigger."""
from pathlib import Path
import sys,hashlib
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(n):
 d={}
 for row in (R/n).read_text().splitlines():
  h,k=row.split('  ',1);assert k not in d;d[k]=h
 return d
allow=(R/'26882_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)==3 and allow==sorted(set(allow))
assert (R/'26882_DELETIONS.txt').read_bytes()==b''
old=manifest('26882_BASE_26881_FULL_APP.sha256');new=manifest('26882_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=manifest('26882_UNCHANGED_PROTECTED.sha256')
assert len(old)==len(new)==2009 and len(protected)==2006
assert set(allow)=={k for k in old if old[k]!=new[k]}
assert {k for k in protected}==set(old)-set(allow)
assert {k for k in new}==set(old)
assert all(old[k]==new[k]==v for k,v in protected.items())
payload=R/'handoff_payload_26882';actual={'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}
assert actual==set(allow),('unexpected payload path',actual^set(allow))
assert all(sha(payload/k)==new[k] for k in allow)
assert manifest('26882_PAYLOAD_SHA256.txt')=={'handoff_payload_26882/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26882.txt').read_bytes()==b'RUN_26882_SPEKTRA_ROTATED_RAW_B_WHITE_OFF_V1\n'
workflow=R/'.github/workflows/build-26882-iris-rawr.yml'
assert workflow.is_file() and workflow.read_text().count('TRIGGER_26882.txt')>=2
assert all((R/n).is_file() for n in ('generate_26882_build.py','verify_26882_candidate.py','verify_26882_patches.py','verify_26882_semantics.py','verify_26882_expanded_glsl.py','regressions/26882_actual_successor_contract.py'))
# This validates only the namespace supplied through the three upload stages.
# The repository app/src is untouched until successful candidate-first transform.
package=manifest('26882_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==h for k,h in package.items())
allowed=set((R/'26882_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
# Permanent 26882 source-only handoff regression: no generated Python bytecode is
# required to run the workflow, and a .pyc must never become a hash dependency.
assert not any('__pycache__' in x.split('/') or x.endswith(('.pyc','.pyo')) for x in set(package)|allowed), 'generated Python cache included in sealed upload contract'
assert '26882_REPOSITORY_UPLOAD_ALLOWLIST.txt' in allowed
expected=set(package)|{'26882_HANDOFF_HASHES.sha256','26882_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert allowed==expected,(sorted(allowed^expected))
assert not any(x.startswith('app/') for x in allowed)
print('PASS 26882 stage-root exact 3-file runtime allowlist + 2006 protected, 0 deletions, no repository app/src writes, isolated stage trigger')
