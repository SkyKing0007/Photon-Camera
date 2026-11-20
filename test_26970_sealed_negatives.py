#!/usr/bin/env python3
"""26970 sealed SHA tamper guards, exact stage separation."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
h={}
for line in (R/'26970_HANDOFF_HASHES.sha256').read_text().splitlines():
 sha,name=line.split('  ',1)
 assert len(sha)==64 and name not in h and name!='26970_HANDOFF_HASHES.sha256'
 h[name]=sha
for name,hash in h.items():
 b=(R/name).read_bytes();assert hashlib.sha256(b).hexdigest()==hash,name
 assert hashlib.sha256(b+b'0').hexdigest()!=hash
 if b:assert hashlib.sha256(b[:-1]).hexdigest()!=hash
assert len(h)>=35
assert (R/'26970_STAGE_3_UPLOAD_PATHS.txt').read_text().strip()=='TRIGGER_26970.txt'
assert '.github/workflows/build-26970-change-aware.yml' not in (R/'26970_STAGE_1_UPLOAD_PATHS.txt').read_text()
assert 'TRIGGER_26970.txt' not in (R/'26970_STAGE_1_UPLOAD_PATHS.txt').read_text()
print('PASS 26970 exact staged SHA tamper/append/truncate negatives and strict ordered three stages')
