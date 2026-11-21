#!/usr/bin/env python3
"""SHA tamper/missing/append and three-stage upload negative checks."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
hashes={}
for line in (R/'26971_HANDOFF_HASHES.sha256').read_text().splitlines():
 h,p=line.split('  ',1)
 assert p not in hashes and len(h)==64
 hashes[p]=h
 assert (R/p).exists(),p
 b=(R/p).read_bytes()
 assert hashlib.sha256(b).hexdigest()==h,p
 assert hashlib.sha256(b+b'0').hexdigest()!=h
 if len(b):assert hashlib.sha256(b[:-1]).hexdigest()!=h
assert len(hashes)>=25
stage=[(R/f'26971_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert stage[1]==['.github/workflows/build-26971-change-aware.yml']
assert stage[2]==['TRIGGER_26971.txt']
assert stage[0]==sorted((set(hashes)|{'26971_HANDOFF_HASHES.sha256'})-set(stage[1])-set(stage[2]))
assert '.github/workflows/build-26971-change-aware.yml' not in stage[0] and 'TRIGGER_26971.txt' not in stage[0]
assert '26970_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml' in stage[0]
assert 'handoff_payload_26971/app/version.properties' in stage[0]
print('PASS 26971 all handoff hashes tamper/missing/append, trigger and workflow exact three-stage ordering')
