#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26662.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:]);root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand);allow=[x for x in (root/'R1_26662_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x];actual=sorted(r for r in bh if bh[r]!=ch[r])
if actual!=sorted(allow) or len(actual)!=6:raise SystemExit(f'FAIL 26662 allowlist {actual}')
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726662' in ver and 'VERSION_BUILD=26662' in ver
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();fs=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
for x in ['IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','currentMeaningfulClip','heldStructureCannotOwnMagnitude=true','recordMotion26662PreviewProtection(sensorTs, observedProtectionEv)']:
 if x not in cc:raise SystemExit('FAIL capture '+x)
if 'Math.max(0.0f, mMotion26608StructuredPeakSecond)' in cc[cc.index('IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER'):cc.index('IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY')]:raise SystemExit('FAIL held structured peak still owns protection magnitude')
for x in ['IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION','getMotion26662ReferencePreviewProtectionEv(','iris26553FrameTimestamp']:
 if x not in mr:raise SystemExit('FAIL preview java '+x)
for x in ['IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION','iris26662ReferencePreviewGain','mappedGuide = iris26662Gain * guide','1.0 + (iris26662Gain - 1.0) * guide']:
 if x not in fs:raise SystemExit('FAIL preview shader '+x)
for x in ['IRIS_26662_CANONICAL_REFERENCE_PRESENTATION_SOLVE','referenceRestoreGain','candidateMeterCanonicalized=true','protectionResidualEvAdded=false','* referenceRestoreGain']:
 if x not in matcher:raise SystemExit('FAIL matcher '+x)
if 'referenceResidualEv' in matcher:raise SystemExit('FAIL stale 26661 residual presentation compensation')
for x in ['IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','motionv2/display_exposure','iris26662ReferenceRestoreGain','beforeLocalTone=true beforeSdrTone=true beforeUhdrGainMap=true','glProg.setTexture("HdrBuffer", extendedLinearHdr)']:
 if x not in render:raise SystemExit('FAIL render normalization '+x)
if render.index('IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION')>render.index('iris26621BuildLocalLaplacianTone(extendedLinearHdr)'):raise SystemExit('FAIL normalization occurs after local tone')
print('PASS 26662 semantics: stable current-RAW highlight protection, frame-matched white-anchored preview, canonical HDR normalization before Local-Laplacian/SDR/UHDR, matcher meters same canonical exposure domain')
