#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26665.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:]);root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand);allow=[x for x in (root/'R1_26665_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
actual=sorted(r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r))
if actual!=sorted(allow) or len(actual)!=6:raise SystemExit(f'FAIL 26665 allowlist {actual}')
if set(ch)-set(bh) or set(bh)-set(ch):raise SystemExit('FAIL 26665 additions/removals')
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726665' in ver and 'VERSION_BUILD=26665' in ver
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();renderj=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text();rs=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();gm=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
# Successful 26664 capture + stable preview + canonical HDR stay owned upstream.
for x in ['IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','heldStructureCannotOwnMagnitude=true','recordMotion26662PreviewProtection(sensorTs, observedProtectionEv)','IRIS_26663_STABLE_PREVIEW_METADATA_HANDOFF']:
 if x not in cc:raise SystemExit('FAIL preserved capture/preview '+x)
for x in ['IRIS_26663_STABLE_PREVIEW_METADATA_HOLD','mIris26663LastConfirmedProtectionEv','mIris26663PresentedProtectionEv','Float.isFinite(exactEv)','Math.min(0.10f, iris26663DeltaEv)']:
 if x not in mr:raise SystemExit('FAIL stable preview '+x)
for x in ['IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','iris26662ReferenceRestoreGain','beforeLocalTone=true beforeSdrTone=true beforeUhdrGainMap=true']:
 if x not in renderj:raise SystemExit('FAIL canonical HDR '+x)
if renderj.index('IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION')>renderj.index('iris26621BuildLocalLaplacianTone(extendedLinearHdr)'):raise SystemExit('FAIL normalization moved after local tone')
# Local-Laplacian is strictly protected in 26665.
llp='app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'
if sha(base/llp)!=sha(cand/llp):raise SystemExit('FAIL local-laplacian bytes changed')
if sha(cand/llp)!='68525a67c02c008c35327ac4b1b682481f6956beb23a1bcd3d38f4623460ebf2':raise SystemExit('FAIL successful-26664 local-laplacian authority')
# 26664 body owner remains, and new controls cannot overlap its protected-HDR gate.
for x in ['IRIS_26664_SCENE_GLOBAL_LOG_BODY_RECOVERY','bodyLiftEv = clamp(0.65f * remainingDarkEv * protectionGate','smoothstep(0.10f, 0.40f, referenceProtectionEv)','IRIS_26664_SCENE_GLOBAL_LOG_BODY_TONE','fadeStartLog=-3.6438561898','fadeEndLog=-0.6214883767']:
 if x not in matcher+rs:raise SystemExit('FAIL preserved 26664 body owner '+x)
for x in ['IRIS_26665_LOW_KEY_SCENE_INTENT','smoothstep(0.02f, 0.08f, referenceProtectionEv)','medianDark26665','upperDark26665','previewDark26665','0.70f * iris26665LowKeyIntent','isoDriven=false shutterDriven=false sceneSemantic=false','nightRouteUnchanged=true']:
 if x not in matcher:raise SystemExit('FAIL low-key intent '+x)
for x in ['motionV2ShadowDepthEv','IRIS_26665_BLACK_SAFE_SHADOW_DEPTH_DECISION','crowdingExcessEv26665','bodyDrGate26665','legacyFree26665','0.0f, 0.45f']:
 if x not in matcher+params:raise SystemExit('FAIL shadow-depth decision '+x)
# Shader transfer appears on both final routes, after 26664 body and before frozen 26660 highlight gamma.
for x in ['iris26665ShadowDepthEv','IRIS_26665_BLACK_SAFE_SHADOW_DEPTH','y<=0.004 || y>=0.30','16.0*t*t*(1.0-t)*(1.0-t)','return y*exp2(-depthEv*bump);']:
 if x not in rs:raise SystemExit('FAIL shadow-depth shader '+x)
if rs.count('mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);')!=2:raise SystemExit('FAIL new depth must own both final Motion routes')
for anchor in ['mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n    mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n    mappedGuide=iris26660ObjectColorGamma(mappedGuide);','mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n            mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n            mappedGuide=iris26660ObjectColorGamma(mappedGuide);']:
 if anchor not in rs:raise SystemExit('FAIL final tone order')
# UHDR: same new SDR depth model, frozen 26658 HDR target math and SR shared route.
for x in ['IRIS_26665_UHDR_SHADOW_DEPTH_PARITY','iris26665BlackSafeShadowDepth(sharedGuide26665)','IRIS_26660_UHDR_POP_TARGET_FROZEN_TO_26658','float localStructureScale=globalSdrGuide>1.0e-7','float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);']:
 if x not in gm:raise SystemExit('FAIL UHDR parity '+x)
for x in ['glProg.setVar("iris26665ShadowDepthEv"','true2xSharedMap=','motionV2SuperResOutputEnabled']:
 if x not in renderj:raise SystemExit('FAIL SR/UHDR runtime handoff '+x)
# New controls are presentation only; no capture owner consumes parameter.
for p in (cand/'app/src/main/java/com/particlesdevs/photoncamera/capture').rglob('*.java'):
 if 'motionV2ShadowDepthEv' in p.read_text():raise SystemExit('FAIL capture consumes shadow-depth scalar '+str(p))
print('PASS 26665 semantics: exact six-file presentation scope; 26664 capture/preview/HDR/local-Laplacian protected; low-key intent + black-safe shadow depth are Motion-only, non-overlapping with protected-HDR body recovery, SR/UHDR matched-intent parity retained')
