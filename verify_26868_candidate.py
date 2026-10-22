#!/usr/bin/env python3
"""Strict deterministic 26867 compiled-authority reconstruction for 26868."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser()
p.add_argument('base',type=Path);p.add_argument('candidate',type=Path)
p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--transform',action='store_true')
a=p.parse_args();root=a.root.resolve();base=a.base.resolve();candidate=a.candidate.resolve()

def manifest(name):
    out={}
    for ln in (root/name).read_text().splitlines():
        h,f=ln.split('  ',1)
        assert f.startswith('app/') and len(h)==64 and f not in out,(name,ln)
        bytes.fromhex(h);out[f]=h
    return out

def snapshot(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
prior=manifest('26868_BASE_26867_FULL_APP.sha256')
post=manifest('26868_EXPECTED_CANDIDATE_FULL_APP.sha256')
protected=manifest('26868_UNCHANGED_PROTECTED.sha256')
new=manifest('26868_NEW_CHANGED_SHA256.txt')
allowed=(root/'26868_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==1991 and len(post)==1992
assert len(allowed)==8 and len(set(allowed))==8
assert set(new)==set(allowed)
assert set(prior)<=set(post)
assert set(prior)-set(allowed)==set(protected)
assert len(protected)==1984
assert set(allowed)=={x for x in set(prior)|set(post) if prior.get(x)!=post.get(x)}
assert all(x.startswith('app/src/') or x=='app/version.properties' for x in allowed)
assert not any(x.startswith(('app/build/','app/.cxx/')) for x in allowed)
assert 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26868DirectLong.kt' in allowed
assert 'app/version.properties' in allowed
assert snapshot(base)==prior,'26867 successful compiled-candidate authority mismatch'
if a.transform:
    assert base!=candidate
    shutil.rmtree(candidate,ignore_errors=True);shutil.copytree(base,candidate)
    for f in allowed:
        src=root/'handoff_payload_26868'/f
        assert src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==post[f],f
        dst=candidate/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
assert snapshot(candidate)==post,'candidate exact 1992-file bytes mismatch'
assert all(prior[f]==post[f]==protected[f] for f in protected)
version=(candidate/'app/version.properties').read_text()
assert version.count('VERSION_NAME=0.9726868')==1 and version.count('VERSION_BUILD=26868')==1
print('PASS 26867 source authority (1991) -> frozen 26868 candidate (1992), exact allowlist 8; protected/DNG/native/vendor byte identity; version')
