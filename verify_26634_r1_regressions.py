#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26634_r1_regressions.py BASE CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); root=Path(__file__).resolve().parent
changed=set((root/'R1_26634_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
# Permanent source-domain regressions
assert not any(x.startswith('app/build/') or x.startswith('app/.cxx/') for x in changed)
assert len(changed)==8
# No second denoise stage is introduced: only the existing MGC Q8 variance-map transport is populated.
stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'coerceIn(0.75f, 1.0f)' in stack and 'coerceIn(192, 256)' in stack
# Existing native Q8 consumer remains byte-identical; Kotlin contract defines Q8 as variance multiplier, 256 identity.
native='app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_full_resolution_denoise_jni.cpp'
assert (b/native).read_bytes()==(c/native).read_bytes()
maprel='app/src/main/java/com/hinnka/mycamera/raw/MgcSpatialStrengthMap.kt'
assert (b/maprel).read_bytes()==(c/maprel).read_bytes()
mtxt=(c/maprel).read_text(); assert 'Q8 variance multiplier' in mtxt and 'IDENTITY_Q8 = 256' in mtxt
# MotionTrace retained byte-identical
mt='app/src/main/java/com/particlesdevs/photoncamera/util/MotionTrace.java'
assert (b/mt).read_bytes()==(c/mt).read_bytes()
# normal logger retained; dedicated lifecycle persistence gone
lg=(c/'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java').read_text()
assert 'writeToFile' in lg and 'iris-process-lifecycle-' not in lg and 'getFD().sync()' not in lg
# 26633 luma ceiling stays 0.35, SR path not edited by 26634
br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert '0.35f * supportGate26633' in br
# no UHDR/gainmap source changes; entire protected manifests verify separately
assert not any('uhdr' in p.lower() or 'gainmap' in p.lower() for p in changed)
# DNG exact 7 files unchanged
for line in (root/'R1_26634_DNG_BASE.sha256').read_text().splitlines():
    _,rel=line.split('  ',1); assert (b/rel).read_bytes()==(c/rel).read_bytes(), rel
print('PASS 26634 permanent regressions: no stronger denoise, no duplicate denoise, MotionTrace/PhotonLog retained, lifecycle file removed, UHDR/DNG untouched')
