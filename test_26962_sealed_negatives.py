#!/usr/bin/env python3
"""One-byte mutation, missing source, unexpected vendor and patch tamper rejections."""
from pathlib import Path
from hashlib import sha256
R=Path(__file__).resolve().parent
sealed={p:h for h,p in (x.split('  ',1) for x in (R/'26962_HANDOFF_HASHES.sha256').read_text().splitlines())}
assert len(sealed)>=22
for p in ('handoff_payload_26962/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','handoff_payload_26962/app/version.properties','26962_FORWARD_FULLINDEX.patch','26962_ROLLBACK_FULLINDEX.patch','26962_STAGE_1_UPLOAD_PATHS.txt'):
 b=(R/p).read_bytes();assert sha256(b).hexdigest()==sealed[p]
 bad=bytearray(b);bad[len(bad)//2]^=1
 assert sha256(bad).hexdigest()!=sealed[p]
allowed=set((R/'26962_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
for p in ('app/src/main/cpp/vendor/rawr/merge.comp','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'):
 assert p not in allowed
assert (R/'handoff_payload_26962/app/version.properties').is_file()
print('PASS 26962 exact seal negative tamper, extra shader/vendor, and missing-file gates')
