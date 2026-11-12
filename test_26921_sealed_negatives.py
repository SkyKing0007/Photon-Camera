#!/usr/bin/env python3
"""Fail-closed handoff negatives: exact sealed bytes, missing runtime overlay, incorrect allowlist."""
from pathlib import Path
import tempfile,subprocess,shutil
R=Path.cwd()
files=[x.split('  ',1)[1] for x in (R/'26921_HANDOFF_HASHES.sha256').read_text().splitlines()]
with tempfile.TemporaryDirectory(prefix='neg26921_') as tmp:
 d=Path(tmp)
 for p in files+['26921_HANDOFF_HASHES.sha256']:
  dest=d/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,dest)
 def seal():return subprocess.run(['python3','-S','build_26921_incremental.py','seal'],cwd=d,capture_output=True,text=True).returncode
 assert seal()==0,'valid original handoff did not seal'
 payload=d/'handoff_payload_26921/app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp'
 raw=payload.read_bytes();payload.write_bytes(raw+b'\n');assert seal()!=0,'altered native source accepted';payload.write_bytes(raw)
 payload.unlink();assert seal()!=0,'missing native source accepted';payload.write_bytes(raw)
 allow=d/'26921_CHANGED_RUNTIME_ALLOWLIST.txt';raw=allow.read_bytes();allow.write_bytes(raw+b'app/src/main/java/NotAllowed.java\n');assert seal()!=0,'expanded allowlist accepted';allow.write_bytes(raw)
 wf=d/'.github/workflows/build-26921-change-aware.yml';raw=wf.read_bytes();wf.write_bytes(raw+b'# tampered\n');assert seal()!=0,'altered workflow accepted';wf.write_bytes(raw)
 assert seal()==0,'valid handoff not restored'
print('PASS 26921 clean-stage handoff, altered/missing payload, allowlist expansion, workflow tampering rejected')
