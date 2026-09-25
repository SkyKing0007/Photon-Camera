#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26706_regressions.py BASE26705 CANDIDATE')
pkg=Path(__file__).resolve().parent;b=Path(sys.argv[1]);c=Path(sys.argv[2])
subprocess.run([sys.executable,'-S',str(pkg/'validate_26706.py'),str(b),str(c)],check=True)
st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
# 26699 performance regression: never restore the old full-resolution fusion decision readback call.
assert st.count('logSabreUniversalFusionDecision26651(')==1
assert 'IRIS_26699_FUSION_DECISION_BARRIER_REMOVED' in st and 'IRIS_26699_FUSION_RADIANCE_BARRIER_REMOVED' in st
# 26705 exposure regression: no NORMAL AE writer is revived.
cap=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
assert 'mMotion26701' not in cap and 'MOTION_26680_FORCE_LATCH_FRAMES' not in cap
# 26705/26704 visual and chroma protection remain in production SHORT shader.
sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for t in ['IRIS_26705_SHORT_RADIANCE_HIGHLIGHT_DOMAIN_ONLY','IRIS_26704_VALID_NORMAL_CHROMA_IMMUTABLE','IRIS_26704_FAIL_CLOSED_INFERRED_SHORT_RADIANCE']:
 assert t in sh,t
# 26704 Actions post-build marker regression: body-tone owner is inherited 26704, never renamed to 26706.
assert 'iris26704BodyToneStrength' in (c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
assert 'iris26706BodyToneStrength' not in (c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
print('PASS 26706 permanent regressions: 26705 NORMAL AE/SHORT capture frozen; production SHORT fusion frozen; no full-frame telemetry revival; inherited 26704 body-tone marker preserved')
