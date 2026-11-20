#!/usr/bin/env python3
"""Negative/alteration guards for 26968 sealed three-stage source metadata."""
import pathlib,hashlib,sys
R=pathlib.Path(__file__).resolve().parent
lines=(R/'26968_HANDOFF_HASHES.sha256').read_text().splitlines();d={}
for line in lines:
 sha,name=line.split('  ',1);assert name not in d and len(sha)==64;d[name]=sha
assert len(d)>=25
for name,sha in d.items():
 b=(R/name).read_bytes();assert hashlib.sha256(b).hexdigest()==sha
 assert hashlib.sha256(b+b'0').hexdigest()!=sha
 if len(b):assert hashlib.sha256(b[:-1]).hexdigest()!=sha
assert (R/'26968_STAGE_3_UPLOAD_PATHS.txt').read_text().strip()=='TRIGGER_26968.txt'
assert '.github/workflows/build-26968-change-aware.yml' not in (R/'26968_STAGE_1_UPLOAD_PATHS.txt').read_text()
assert 'TRIGGER_26968.txt' not in (R/'26968_STAGE_1_UPLOAD_PATHS.txt').read_text()
print('PASS 26968 hash tamper/missing/append negative guards and strict three-stage ordering')
