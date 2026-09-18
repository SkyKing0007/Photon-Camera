#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26661.py BASE CANDIDATE')
base=Path(sys.argv[1]);cand=Path(sys.argv[2]);root=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
allow=[x for x in (root/'R1_26661_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]; actual=sorted(r for r in bh if bh[r]!=ch[r])
if actual!=sorted(allow) or len(actual)!=8: raise SystemExit(f'FAIL 26661 allowlist {actual}')
ver=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726661' in ver and 'VERSION_BUILD=26661' in ver
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
for x in ['IRIS_26661_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','MOTION_26661_REFERENCE_HEADROOM_TARGET = 0.72f','MOTION_26661_MAX_PROTECTION_EV = 1.50f','negativeOnly=true','postShutterHighlightShort=false','adaptiveHighlightSafeZslReference=true']:
 if x not in cc: raise SystemExit('FAIL capture owner '+x)
for stale in ['updateMotionV2ExposureAuthority(result); intentionally dormant */\n                updateMotionV2ExposureAuthority(result);','preserveExistingZslExposurePolicy=true']:
 if stale in cc: raise SystemExit('FAIL stale exposure owner '+stale)
frame=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java').read_text(); params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text(); bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text(); mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text(); fs=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
for txt in (frame,params):
 if 'motionV2ReferenceProtectionEv' not in txt: raise SystemExit('FAIL reference EV handoff field')
for x in ['IRIS_26661_GOOGLE_HDR_BRACKETING_REFERENCE_OWNER','referenceProtectionPresentationOnly=true','longGlobalBrightnessAuthority=false']:
 if x not in bridge: raise SystemExit('FAIL bridge '+x)
for x in ['IRIS_26661_GOOGLE_REFERENCE_PRESENTATION_COMPENSATION','referenceResidualEv = referenceProtectionEv * (1.0f - matchStrength)','longGlobalBrightnessAuthority=false']:
 if x not in matcher: raise SystemExit('FAIL matcher '+x)
for x in ['IRIS_26661_GOOGLE_REFERENCE_LIVE_PREVIEW_COMPENSATION','getMotion26661ReferencePreviewProtectionEv','iris26661ReferencePreviewGain']:
 if x not in mr+fs: raise SystemExit('FAIL preview '+x)
# Merge/render/UHDR/color/Night/DNG/SR owners outside intended scope stay byte identical.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/color_transform.glsl']:
 if bh[r]!=ch[r]: raise SystemExit('FAIL protected HDR/IQ owner '+r)
for r in bh:
 if r not in allow and bh[r]!=ch[r]: raise SystemExit('FAIL protected changed '+r)
print('PASS 26661 semantics: adaptive negative-only highlight-safe ZSL reference + exact EV presentation handoff; LONG remains shadow/SNR evidence; 26660 render/UHDR and protected IQ owners frozen')
