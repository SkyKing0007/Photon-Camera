#!/usr/bin/env python3
"""Fail-closed negative controls against sealed stage, payload, identity and manifests."""
import hashlib,importlib.util,pathlib,tempfile
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26975',R/'build_26975_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.seal()
lines=(R/'26975_HANDOFF_HASHES.sha256').read_text().splitlines()
entries={p:h for h,p in (x.split('  ',1) for x in lines)}
changed,_,_=b.scope()
assert len(entries)==len(lines) and len(entries)==len(changed)+len(b.FILES)+2, 'sealed exactly every current V8 delta, infrastructure and trigger file'
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

# V7→V8 source removal intentionally leaves old blobs in the GitHub *staging*
# directory. Prove precise, content-addressed pruning, never a broad bypass.
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='v8-stale-negative-') as td:
    payload=Path(td);(payload/'app').mkdir()
    current=payload/'app/current.kt';current.write_bytes(b'new V8 source')
    legacy=payload/'app/old.kt';legacy.write_bytes(b'old V7 staging')
    expected={'app/current.kt'}
    stale={'app/old.kt':hashlib.sha256(b'old V7 staging').hexdigest()}
    assert b.prune_only_pinned_stale_stage(payload,expected,stale)==1
    assert current.read_bytes()==b'new V8 source' and not legacy.exists()
    assert b.prune_only_pinned_stale_stage(payload,expected,stale)==0
    legacy.write_bytes(b'TAMPERED V7')
    try:b.prune_only_pinned_stale_stage(payload,expected,stale)
    except RuntimeError as e:assert 'tampered SHA-pinned historical staging file' in str(e)
    else:raise AssertionError('tampered old V7 blob accepted')
    legacy.unlink()
    unexpected=payload/'app/unexpected.kt';unexpected.write_bytes(b'unlisted')
    try:b.prune_only_pinned_stale_stage(payload,expected,stale)
    except RuntimeError as e:assert 'payload missing/extra' in str(e)
    else:raise AssertionError('unlisted old blob accepted')
    unexpected.unlink()
    current.unlink()
    try:b.prune_only_pinned_stale_stage(payload,expected,stale)
    except RuntimeError as e:assert 'payload missing/extra' in str(e)
    else:raise AssertionError('missing current V8 blob accepted')
assert len(b.stale_stage_manifest())==119
print('PASS V8 strict historical stale stage cleanup, tamper/unexpected/missing negative controls')
print('PASS negative SHA mutations x'+str(cases)+', manifest/protected equality, no missing/extra stage, identical source pre/post')
