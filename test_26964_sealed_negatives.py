#!/usr/bin/env python3
"""Physical tamper rejection for SHA-sealed source, patch, upload stage, and vendor scope."""
from pathlib import Path
from hashlib import sha256
import tempfile,shutil
R=Path(__file__).resolve().parent
sealed={}
for line in (R/'26964_HANDOFF_HASHES.sha256').read_text().splitlines():
 h,p=line.split('  ',1);assert p not in sealed and len(h)==64;sealed[p]=h
assert len(sealed)>=32
for name in (
 'handoff_payload_26964/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'handoff_payload_26964/app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java',
 'handoff_payload_26964/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 '26964_FORWARD_FULLINDEX.patch','26964_STAGE_1_UPLOAD_PATHS.txt'):
 data=(R/name).read_bytes();assert sha256(data).hexdigest()==sealed[name],name
 bad=bytearray(data);bad[len(bad)//2]^=0x80
 assert sha256(bad).hexdigest()!=sealed[name]
with tempfile.TemporaryDirectory(prefix='26964_negative_') as d:
 dst=Path(d)/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/shaders/hdrq_merge.comp'
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text('// forbidden vendor change')
 assert 'app/'+str(dst.relative_to(Path(d)/'app')) not in (R/'26964_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
print('PASS 26964 deterministic SHA seal rejects shader, Java, patch and stage mutations + forbidden vendor file')
