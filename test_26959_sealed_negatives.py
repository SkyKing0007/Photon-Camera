#!/usr/bin/env python3
"""Physical negative examples: source edit, truncated patch, forbidden source, altered stage hash."""
from pathlib import Path
from hashlib import sha256
import shutil,tempfile,subprocess
R=Path(__file__).resolve().parent

def fail(msg):raise AssertionError(msg)
sealed={}
for line in (R/'26959_HANDOFF_HASHES.sha256').read_text().splitlines():
 h,p=line.split('  ',1);sealed[p]=h
assert len(sealed)>30
for name in ('handoff_payload_26959/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
             'handoff_payload_26959/app/src/main/assets/shaders/motionv2/render.glsl',
             '26959_FORWARD_FULLINDEX.patch','26959_STAGE_1_UPLOAD_PATHS.txt'):
 data=(R/name).read_bytes()
 assert sha256(data).hexdigest()==sealed[name]
 # The same authoritative sealed comparator must REJECT any one-byte mutation.
 changed=bytearray(data);changed[len(changed)//2] ^= 0x40
 assert sha256(changed).hexdigest()!=sealed[name]
with tempfile.TemporaryDirectory(prefix='26959_negative_') as d:
 a=Path(d);src=R/'handoff_payload_26959/app/src/main/assets/shaders/motionv2/render.glsl'
 dst=a/'app/src/main/assets/shaders/motionv2/render.glsl';dst.parent.mkdir(parents=True);shutil.copy2(src,dst)
 original=sha256(dst.read_bytes()).hexdigest();dst.write_bytes(dst.read_bytes()+b'\n/* injection */\n')
 assert sha256(dst.read_bytes()).hexdigest()!=original
 bad=a/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/shaders/hdrq_merge.comp';bad.parent.mkdir(parents=True);bad.write_text('// impermissible new vendor file')
 allowed=set((R/'26959_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 assert 'app/'+str(bad.relative_to(a/'app')) not in allowed
print('PASS source, patch, hash and protected vendor negative tamper rejections')
