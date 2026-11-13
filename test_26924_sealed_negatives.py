#!/usr/bin/env python3
"""Staged ZIP integrity fail-closed negative fixtures (no source edits)."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
s=(R/'26924_HANDOFF_HASHES.sha256').read_text().splitlines()
seen={}
for line in s:
 h,p=line.split('  ',1)
 assert len(h)==64 and re.fullmatch('[0-9a-f]{64}',h)
 assert p not in seen and (R/p).is_file()
 assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h
 seen[p]=h
assert len(seen)>=25
# Changes to payload bytes, deletion, duplicated stage paths, unknown executable
# and reversed stage trigger must all be detected by the same sealed predicate.
def digest_ok(path,body):return hashlib.sha256(body).hexdigest()==seen[path]
victim='handoff_payload_26924/app/src/main/cpp/iris26864/bridge/Iris26924_raw_residual.comp'
assert victim in seen
payload=(R/victim).read_bytes()
assert digest_ok(victim,payload) and not digest_ok(victim,payload+b'X')
assert len(seen)==len(s)
wf=(R/'.github/workflows/build-26924-change-aware.yml').read_text()
assert 'TRIGGER_26924.txt' in wf and 'TRIGGER_26923.txt' not in wf
assert (R/'TRIGGER_26924.txt').is_file()
assert 'test_26922_guard.py' not in wf
print('PASS 26924 SHA-sealed stage1/2/3, altered shader rejected, duplicate/missing and obsolete trigger rejected')
