#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
if len(sys.argv)!=3: raise SystemExit('usage: validate_26664.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:]);root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand);allow=[x for x in (root/'R1_26664_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x];actual=sorted(r for r in bh if bh[r]!=ch[r])
if actual!=sorted(allow) or len(actual)!=6:raise SystemExit(f'FAIL 26664 allowlist {actual}')
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726664' in ver and 'VERSION_BUILD=26664' in ver
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();renderj=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text();rs=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
# Keep successful 26663 capture + stable preview owners.
for x in ['IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','heldStructureCannotOwnMagnitude=true','recordMotion26662PreviewProtection(sensorTs, observedProtectionEv)','IRIS_26663_STABLE_PREVIEW_METADATA_HANDOFF']:
 if x not in cc:raise SystemExit('FAIL preserved capture/preview '+x)
for x in ['IRIS_26663_STABLE_PREVIEW_METADATA_HOLD','mIris26663LastConfirmedProtectionEv','mIris26663PresentedProtectionEv','Float.isFinite(exactEv)','Math.min(0.10f, iris26663DeltaEv)']:
 if x not in mr:raise SystemExit('FAIL stable preview '+x)
# Canonical HDR normalization remains before local tone.
for x in ['IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','iris26662ReferenceRestoreGain','beforeLocalTone=true beforeSdrTone=true beforeUhdrGainMap=true']:
 if x not in renderj:raise SystemExit('FAIL canonical normalization '+x)
if renderj.index('IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION')>renderj.index('iris26621BuildLocalLaplacianTone(extendedLinearHdr)'):raise SystemExit('FAIL normalization moved after local tone')
# 26663 spatial body island owner must be gone, exact successful 26662 remap restored.
for x in ['IRIS_26663_CANONICAL_BODY_LOCAL_RECOVERY','iris26663CanonicalBodyLiftEv','iris26663BodyBase']:
 if x in ll+renderj+matcher+params:raise SystemExit('FAIL stale 26663 spatial body owner '+x)
if sha(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')!='68525a67c02c008c35327ac4b1b682481f6956beb23a1bcd3d38f4623460ebf2':raise SystemExit('FAIL exact successful-26662 local remap not restored')
# New body owner is scene-global and after local tone, before unchanged highlight gamma.
for x in ['motionV2GlobalBodyLiftEv','IRIS_26664_SCENE_GLOBAL_LOG_BODY_RECOVERY','0.65f * remainingDarkEv * protectionGate','0.0f, 1.25f']:
 if x not in params+matcher:raise SystemExit('FAIL global body decision '+x)
for x in ['iris26664GlobalBodyLiftEv','IRIS_26664_SCENE_GLOBAL_LOG_BODY_TONE','fadeStartLog=-3.6438561898','fadeEndLog=-0.6214883767','return y*exp2(appliedEv);']:
 if x not in rs:raise SystemExit('FAIL global body shader '+x)
if rs.count('mappedGuide=iris26664GlobalBodyTone(mappedGuide);')!=2:raise SystemExit('FAIL global body map must own both local/nonlocal final routes')
if rs.index('mappedGuide=iris26664GlobalBodyTone(mappedGuide);')>rs.index('mappedGuide=iris26660ObjectColorGamma(mappedGuide);'):raise SystemExit('FAIL global body map must precede 26660 gamma')
# Mathematical monotonic/C1 bound for max 1.25EV over 0.08..0.65 log span.
width=math.log2(0.65)-math.log2(0.08); min_slope=1.0-1.5*1.25/width
if min_slope<=0.35:raise SystemExit(f'FAIL monotonic log slope bound {min_slope}')
print(f'PASS 26664 semantics: successful-26663 capture/preview/canonical HDR retained; 26663 spatial island owner removed; exact 26662 Local-Laplacian remap restored; scene-global C1 log body transfer is monotone (min log slope {min_slope:.3f}) and exact identity from guide 0.65 upward')
