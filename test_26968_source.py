#!/usr/bin/env python3
"""26968 exact-source and cross-owner constraints, unchanged 26965 photo processing."""
import pathlib,hashlib,sys,re
R=pathlib.Path(__file__).resolve().parent
P=R if '--live' in sys.argv else R/'handoff_payload_26968'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(m):return {path:h for h,path in (line.split('  ',1) for line in (R/m).read_text().splitlines())}
a=read('26968_BASE_26965_FULL_APP.sha256');b=read('26968_EXPECTED_FULL_APP.sha256');p=read('26968_PROTECTED_SOURCE.sha256')
changed=set((R/'26968_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
expected=set("""app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java
app/src/main/res/xml/preferences.xml
app/version.properties""".splitlines())
assert len(a)==len(b)==2055 and len(p)==2049
assert changed==expected=={x for x in a if a[x]!=b[x]}
assert set(a)==set(b) and p=={name:h for name,h in a.items() if name not in changed}
assert (R/'26968_ADDED_RUNTIME_PATHS.txt').read_text()==(R/'26968_DELETED_RUNTIME_PATHS.txt').read_text()==''
assert all(sha(P/x)==b[x] for x in expected)
assert 'VERSION_NAME=0.9726968' in (P/'app/version.properties').read_text()
assert 'VERSION_BUILD=26968' in (P/'app/version.properties').read_text()
if '--live' in sys.argv:
 from importlib.machinery import SourceFileLoader
 m=SourceFileLoader('ph26968',str(R/'build_26968_incremental.py')).load_module();assert m.scan(R)==b
C=(P/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
M=(P/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java').read_text()
S=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
T=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
assert C.count('IRIS_26968_PREVIEW_B_AUTO_ANTIBANDING_STARTUP')==1
assert C.count('iris26948BVerifiedPeriodNs(result)')==1
assert C.index('iris26948MeasuredPeriodNs == 0L')<C.index('Iris26909ShutterIsoMath.solveSceneLensAware(')
assert C.index('isVerifiedPeriodLockedBPlan26968(')<C.index('mPreviewRequestBuilder.set(CaptureRequest.CONTROL_AE_MODE,\n                    CaptureRequest.CONTROL_AE_MODE_OFF)',C.index('isVerifiedPeriodLockedBPlan26968('))
assert 'CONTROL_AE_ANTIBANDING_MODE_AUTO' in C
assert C.count('IRIS_26871_B_PREVIEW_HAL_ANTIBANDING')==1
assert M.count('isVerifiedPeriodLockedBPlan26968(')==1
assert 'verifiedPeriodNs != 8_333_333L && verifiedPeriodNs != 10_000_000L' in M
assert 'plan.shutterNs % verifiedPeriodNs != 0L' in M
assert 'photo tone owner sees 0.30..1.30' in S
assert S.count('PHOTO_SHADOWS_BIAS_26968 = 0.30f')==1
assert S.count('+ PHOTO_SHADOWS_BIAS_26968;')==1
assert 'public static Snapshot currentForNight26968()' in S
assert 'nightShadows = sm == null ? 0.0f' in S
assert 'snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f)' in S
assert 'Snapshot source = currentForNight26968();' in S
assert 'IrisMotionSettings.currentForNight26968()' in T
assert 'IrisMotionSettings.currentForNight26968()' in C
assert all(not (x.startswith('app/src/main/cpp/') or x.startswith('app/src/main/assets/shaders/') or '/spektra/' in x.lower() or 'GlesMgcRaw' in x) for x in changed)
for x in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'):
 assert a[x]==b[x],x
print('PASS 26968 exact successful 26965 source, six changed, 2049 protected, B flicker shutter gate and A/B Shadows Night isolation')
