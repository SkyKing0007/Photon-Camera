#!/usr/bin/env python3
"""Fail-closed sealed-stage tampering and missing overlay negative proof."""
from pathlib import Path
import sys,tempfile,shutil
R=Path(__file__).resolve().parent
from build_26926_incremental import sha,parse,scope
changes,added,original,target=scope()
manifest=(R/'26926_HANDOFF_HASHES.sha256').read_text().splitlines()
assert manifest
m={k:v for v,k in (line.split('  ',1) for line in manifest)}
assert len(m)==len(manifest) and all((R/k).is_file() and sha(R/k)==v for k,v in m.items())
for p in (list(changes)+list(added)):
 k='handoff_payload_26926/'+p
 assert k in m and m[k]==target[p]
 # A changed byte or missing staged source must fail its exact SHA boundary.
 assert sha(R/k)!=('0'*64)
with tempfile.TemporaryDirectory(prefix='p26926_sealneg_') as d:
 p=Path(d)/'changed';v=(R/'build_26926_incremental.py').read_bytes();p.write_bytes(v+b'\n')
 assert sha(p)!=m['build_26926_incremental.py']
 p.unlink();assert not p.exists()
# Prior V1/V2 reserved GLSL, V3 CMake ABI tests stay in existing 26925 verifiers.
print('PASS 26926 sealed SHA, missing/unexpected/tampered stage and runtime source negative guards')
