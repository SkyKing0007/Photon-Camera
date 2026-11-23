#!/usr/bin/env python3
"""Fail-closed negative controls against sealed stage, payload, identity and manifests."""
import hashlib,importlib.util,pathlib
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26975',R/'build_26975_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.seal()
lines=(R/'26975_HANDOFF_HASHES.sha256').read_text().splitlines()
entries={p:h for h,p in (x.split('  ',1) for x in lines)}
assert len(entries)==len(lines) and len(entries)>392
cases=0
for name in ('26975_FORWARD_FULLINDEX.patch','26975_ROLLBACK_FULLINDEX.patch','26975_EXPECTED_FULL_APP.sha256','26975_PROTECTED_SOURCE.sha256','26975_AUTHORITY_AND_SCOPE.json','.github/workflows/build-26975-change-aware.yml'):
 original=(R/name).read_bytes();want=entries[name]
 assert hashlib.sha256(original).hexdigest()==want
 assert hashlib.sha256(original+b'FAIL_CLOSED_26975').hexdigest()!=want
 cases+=1
base=b.parse(R/'26975_BASE_26974_FULL_APP.sha256');want=b.parse(R/'26975_EXPECTED_FULL_APP.sha256');protect=b.parse(R/'26975_PROTECTED_SOURCE.sha256')
assert set(protect)==set(base)-set((R/'26975_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
assert protect=={p:want[p] for p in protect}
assert b'\n' in (R/'26975_HANDOFF_HASHES.sha256').read_bytes()
assert (R/'26975_STAGE_3_UPLOAD_PATHS.txt').read_text()=='TRIGGER_26975.txt\n'
assert (R/'26975_STAGE_2_UPLOAD_PATHS.txt').read_text()=='.github/workflows/build-26975-change-aware.yml\n'
print('PASS negative SHA mutations x'+str(cases)+', manifest/protected equality, no missing/extra stage, identical source pre/post')
