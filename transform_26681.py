#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26681.py BASE_ROOT OUTPUT_ROOT')
ROOT = Path(__file__).resolve().parent
BASE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
PAYLOAD = ROOT / 'handoff_payload_26681'

def read_manifest(path):
    out = {}
    for raw in path.read_text().splitlines():
        if not raw.strip(): continue
        h, rel = raw.split('  ', 1)
        out[rel] = h
    return out

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def file_map(root):
    return {str(p.relative_to(root)).replace('\\','/'):sha(p)
            for p in sorted((root/'app').rglob('*')) if p.is_file()}

base_expected=read_manifest(ROOT/'R1_26681_BASE_26680_R1_FULL_APP.sha256')
expected=read_manifest(ROOT/'R1_26681_EXPECTED_CANDIDATE_FULL_APP.sha256')
prewrite=read_manifest(ROOT/'R1_26681_PREWRITE_SOURCE_HASHES.sha256')
changed=[x for x in (ROOT/'R1_26681_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (ROOT/'R1_26681_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
deleted=[x for x in (ROOT/'R1_26681_DELETED_PATHS_MUST_EXIST.txt').read_text().splitlines() if x]

actual_base=file_map(BASE)
assert len(actual_base)==1727, len(actual_base)
assert actual_base==base_expected, 'base is not exact successful 26680 compiled candidate'
assert len(changed)==49 and len(set(changed))==49
assert len(added)==37 and len(set(added))==37
assert not deleted
assert set(prewrite)==set(changed)-set(added), (len(prewrite), len(set(changed)-set(added)))
for rel,h in prewrite.items():
    p=BASE/rel
    assert p.is_file() and sha(p)==h, f'prewrite mismatch: {rel}'
for rel in added:
    assert not (BASE/rel).exists(), f'added path exists in base: {rel}'

payload_files={str(p.relative_to(PAYLOAD)).replace('\\','/') for p in PAYLOAD.rglob('*') if p.is_file()}
assert payload_files==set(changed), (sorted(payload_files-set(changed))[:5], sorted(set(changed)-payload_files)[:5])

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
shutil.copytree(BASE/'app', OUT/'app')
for rel in changed:
    src=PAYLOAD/rel
    dst=OUT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

actual=file_map(OUT)
assert len(actual)==1764, len(actual)
assert actual==expected, 'candidate differs from frozen expected manifest'
vp=(OUT/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726681' in vp and 'VERSION_BUILD=26681' in vp
print('PASS transform 26681: exact 26680 authority -> 1764-file frozen candidate; 49 changed / 37 added / 0 deleted')
