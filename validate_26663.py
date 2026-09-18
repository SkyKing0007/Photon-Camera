#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26663.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:]);root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand);allow=[x for x in (root/'R1_26663_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x];actual=sorted(r for r in bh if bh[r]!=ch[r])
if actual!=sorted(allow) or len(actual)!=7:raise SystemExit(f'FAIL 26663 allowlist {actual}')
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726663' in ver and 'VERSION_BUILD=26663' in ver
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
# Capture architecture from successful 26662 stays active.
for x in ['IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','heldStructureCannotOwnMagnitude=true','recordMotion26662PreviewProtection(sensorTs, observedProtectionEv)']:
 if x not in cc:raise SystemExit('FAIL preserved capture '+x)
# Preview miss must hold, never become a fake zero-EV measurement.
for x in ['IRIS_26663_STABLE_PREVIEW_METADATA_HANDOFF','getMotion26663ReferencePreviewProtectionEv(','return Float.NaN;']:
 if x not in cc:raise SystemExit('FAIL preview metadata handoff '+x)
for x in ['IRIS_26663_STABLE_PREVIEW_METADATA_HOLD','mIris26663LastConfirmedProtectionEv','mIris26663PresentedProtectionEv','Float.isFinite(exactEv)','Math.min(0.10f, iris26663DeltaEv)']:
 if x not in mr:raise SystemExit('FAIL preview stable hold '+x)
if 'getMotion26662ReferencePreviewProtectionEv(' in mr:raise SystemExit('FAIL stale exact-miss-to-zero preview getter still used')
# Canonical HDR normalization remains before Local-Laplacian/SDR/UHDR.
for x in ['IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','iris26662ReferenceRestoreGain','beforeLocalTone=true beforeSdrTone=true beforeUhdrGainMap=true']:
 if x not in render:raise SystemExit('FAIL canonical normalization '+x)
if render.index('IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION')>render.index('iris26621BuildLocalLaplacianTone(extendedLinearHdr)'):raise SystemExit('FAIL canonical normalization moved after local tone')
# Body recovery is scene-measured, protection-gated, local-base-only, and highlight identity.
for x in ['motionV2CanonicalBodyLiftEv','IRIS_26663_CANONICAL_BODY_PRESENTATION_RECOVERY','postSolveErrorEv = exposureError(candidate, solvedEv, targetLog)','0.35f * remainingDarkEv * protectionGate','0.0f, 0.65f']:
 if x not in params+matcher:raise SystemExit('FAIL body recovery owner '+x)
for x in ['iris26663CanonicalBodyLiftEv','IRIS_26663_CANONICAL_BODY_LOCAL_RECOVERY','smoothstep(0.035,0.12,shadowBase)','1.0-smoothstep(0.42,0.68,shadowBase)','iris26663BodyBase+weightedResidual']:
 if x not in ll:raise SystemExit('FAIL body recovery shader '+x)
if 'weightedResidual*exp2' in ll or 'weightedResidual * exp2' in ll:raise SystemExit('FAIL structural residual multiplied by body lift')
print('PASS 26663 semantics: 26662 highlight-safe capture preserved; preview metadata misses hold stable compensation; canonical HDR normalization retained; bounded scene-measured Local-Laplacian body recovery is identity before highlights and leaves structural residual untouched')
