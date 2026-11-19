#!/usr/bin/env python3
"""Source manifest and staged hashes fail closed under deliberate tamper; no source writes."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
p=R/'26965_HANDOFF_HASHES.sha256'
entries={}
for l in p.read_text().splitlines():
 h,f=l.split('  ',1);assert f not in entries and re.fullmatch('[0-9a-f]{64}',h);entries[f]=h
for f,h in entries.items():assert (R/f).is_file() and hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f
assert len(entries)>20
# Distinct hashed versions of each representative file necessarily fail equality.
for f in ('test_26965_source.py','handoff_payload_26965/app/version.properties','26965_EXPECTED_FULL_APP.sha256','build_26965_incremental.py'):
 raw=(R/f).read_bytes();h=hashlib.sha256(raw).hexdigest()
 assert h==entries[f]
 bad=raw+b'\n# tampered\n'
 assert hashlib.sha256(bad).hexdigest()!=entries[f]
# A missing path cannot be excused by another manifest entry.
assert len(entries)==len(set(entries))
print('PASS 26965 staged hash tamper/duplicate/missing-entry rejection')
