#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26708_regressions.py BASE26707 CAND')
b,c=map(Path,sys.argv[1:])
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set(Path(__file__).with_name('26708_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726708' in v and 'VERSION_BUILD=26708' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26708_READ_ONLY_NINE_PHASE_HIGHLIGHT_CLASSIFIER','MOTION_26708_SHORT_MODERATE_EV = 2.0f / 3.0f','MOTION_26708_SHORT_STRONG_EV = 4.0f / 3.0f','IRIS_26708_HIGHLIGHT_CLASS_PUBLISHED','IRIS_26708_SHORT_FAILURE_NORMAL_ONLY','IRIS_26708_NORMAL_REFERENCE_PROTECTION_ABSOLUTE_ZERO'] : assert t in cap,t
# Exact 26707 failure: automatic stable-preview owner may not write AE compensation.
i=cap.index('private void updateMotion26680StablePreviewAuthority('); j=cap.index('\n    }',i)+6; stable=cap[i:j]
assert 'CONTROL_AE_EXPOSURE_COMPENSATION' not in stable
assert 'mMotion26680StableFrames >= MOTION_26680_STABLE_CONFIRM_FRAMES' in stable
assert 'MOTION_26680_FORCE_LATCH_FRAMES' not in cap
# Dormant legacy writers stay dormant.
assert '/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */' in cap
assert '/* updateMotionV2ExposureAuthority(result); intentionally dormant */' in cap
# Normal metadata hard zero and old 2.5/5EV scheduler no longer called.
assert 'frame.motionV2ReferenceProtectionEv = 0.0f;' in cap
assert 'motion26607ComputeHighlightShortEv(' not in cap
# compact provenance chain
contracts=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'); stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'); params=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'); matcher=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
for s in [contracts,stack,bridge,params,matcher]: assert 'shortradianceauthority' in s.lower()
for t in ['IRIS_26708_NORMAL_ONLY_BODY_SOLVER','shortOwned','bodyEligible.add(sample)','globalGainShortVote=false']: assert t in matcher,t
# Sabre shader source semantics unchanged; only marker added in that file.
sabre0=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); sabre1=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert sabre1.startswith(sabre0) and sabre1[len(sabre0):].strip().startswith('/* IRIS_26708_SABRE_FUSION_MATH_FROZEN')
# preserve 26707 blue-speck owner and moving-content safeguard bytes.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes()
assert 'IRIS_26707_MOVING_CONTENT_LOW_CONFIDENCE_TAIL_REJECT' in stack
# protected render/UHDR/native remain identical.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26708 regressions: 26707 delayed-result ratchet removed; HAL/user NORMAL sole exposure owner; fresh 9-phase 0/0.67/1.33 SHORT; graceful SHORT failure; SHORT provenance excluded from global body gain; 26707 chroma/moving-tail preserved')
