#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

base=Path(sys.argv[1]); cand=Path(sys.argv[2])
A='app/'

def t(root,rel): return (root/A/rel).read_text()
def b(root,rel): return (root/A/rel).read_bytes()
def need(cond,msg):
    if not cond: raise SystemExit('FAIL: '+msg)

def sha(x): return hashlib.sha256(x).hexdigest()

expected={
'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java',
'src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
'src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java',
'src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIView.java',
'src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'src/main/java/com/particlesdevs/photoncamera/util/log/ActivityLifecycleMonitor.java',
'src/main/res/drawable/ic_super_res_off.xml',
'src/main/res/drawable/ic_super_res_on.xml',
'version.properties',
}
def files(root):
    # 26562 V1.1 permanent Actions regression: compare the exact audited runtime
    # authority scope used by the successful 26561 procedure, not unrelated app/
    # checkout files (tests, proguard rules, SupportedList, app .gitignore).
    # Native/vendor trees are verified independently by the pinned vendor manifest.
    r=root/A
    paths=[]
    main=r/'src/main'
    for p in main.rglob('*'):
        if not p.is_file():
            continue
        rel=p.relative_to(r).as_posix()
        if rel.startswith('src/main/cpp/third_party_26507/') or rel.startswith('src/main/cpp/deps/'):
            continue
        paths.append(p)
    deps_gitignore=r/'src/main/cpp/deps/.gitignore'
    if deps_gitignore.is_file():
        paths.append(deps_gitignore)
    for rel in ('version.properties','build.gradle'):
        q=r/rel
        if q.is_file():
            paths.append(q)
    paths=sorted(set(paths))
    def one(p): return p.relative_to(r).as_posix(),sha(p.read_bytes())
    with ThreadPoolExecutor(max_workers=32) as pool:
        return dict(pool.map(one,paths))
B=files(base);C=files(cand)
changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
need(changed==expected,f'changed-file allowlist mismatch unexpected={sorted(changed-expected)} missing={sorted(expected-changed)}')
need('src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java' in B and 'src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java' not in C,'old Spatial SR DNG writer not intentionally removed')
need('src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java' not in B and 'src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java' in C,'new Sabre SR DNG writer ownership invalid')
print('PASS exact 18-file runtime allowlist including obsolete Spatial DNG writer removal')

# Existing embedded Sabre shader bodies must be byte-identical; exactly one addition.
pat=re.compile(r'\b(?:val|private val)\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',re.S)
SB=dict(pat.findall(t(base,'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')))
SC=dict(pat.findall(t(cand,'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')))
need(set(SC)-set(SB)=={'superResLinearRaw26562'},f'unexpected new Sabre shader literals {sorted(set(SC)-set(SB))}')
need(not(set(SB)-set(SC)),f'existing Sabre shader literal removed {sorted(set(SB)-set(SC))}')
need(all(SB[k]==SC[k] for k in SB),'an existing Sabre shader literal changed')
for k in ('superResDetailMerge26561','superResDetailResolve26561','merge','mergeShadowLong26558'):
    need(k in SC,f'missing protected shader {k}')
print(f'PASS existing Sabre shader literal invariance {len(SB)}/{len(SB)}; exactly one 26562 DNG export shader added')

post=t(cand,'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
need('expectedOutputScale = mParameters.motionV2SuperResOutputEnabled ? 2.0f : 1.0f' in post,'PostPipeline lacks strict 1x/2x SR output contract')
need('motionV2SpatialReconstructionZoom - 1.0f' in post,'PostPipeline does not forbid old Spatial reconstruction zoom')
need('26560 " + pipeline\n                    + " changed proven Sabre native-grid geometry' not in post,'exact 26561 device crash guard survived')
print('PASS stale Motion crash guard replaced by strict native-Sabre + 1x/2x output contract')

night=t(cand,'src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
need('iris26562ExpectedOutputScale = iris26562NightSuperResRequested ? 2.0f : 1.0f' in night,'Night lacks legal 2x contract')
need('p.motionV2SuperResOutputEnabled = false' not in night,'Night still forcibly disables SR')
need('IrisSabreSuperResDngWriter.write' in night,'Night SR DNG does not use Sabre writer')
need('IRIS_26562_NIGHT_SR_DNG_DEGRADED_TO_NATIVE' in night,'Night missing explicit SR-DNG degradation')
print('PASS Night SR 2x ownership, no forced-disable, Sabre DNG routing')

stack=t(cand,'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
bridge=t(cand,'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
need('DNG remains the proven 1x NORMAL Sabre sidecar' not in bridge and 'dngScale=1.0\")' not in bridge,
    'stale 26561 native-only SR DNG text survived')
need('SABRE_LINEAR_RAW_2X' in bridge and 'NORMALIZED16_NATIVE' in bridge,
    '26562 dynamic Sabre SR DNG owner logging missing')
need('IRIS_26561_SABRE_NATIVE_2X_SR_AUTHORITY' not in bridge and 'IRIS_26562_SABRE_NATIVE_2X_SR_DNG_AUTHORITY' in bridge,
    'stale 26561 SR authority marker survived 26562 DNG ownership transition')
need('frame.role == RawBurstFrameRole.NORMAL' in stack,'NORMAL-only SR fine-detail admission lost')
need('superResLinearRawPath = runCatching' in stack and 'IRIS_26562_SABRE_SR_DNG_EXPORT_FAILED_CONTINUE_JPEG' in stack,'isolated SR DNG producer failure contract missing')
need('nativeRgb = chromaPostprocessor.normalizationTargetTexture()' in stack,'SR DNG not sourced from current pre-VGN Sabre camera RGB')
idx_transform=stack.index('renderSabreOutputTransform(' , stack.index('val fullOutput'))
idx_sr=stack.index('streamSabreSuperResLinearRaw(',idx_transform)
idx_vgn=stack.index('chromaPostprocessor.process(',idx_sr)
need(idx_transform < idx_sr < idx_vgn,'SR DNG export must be after Sabre output transform and before VGN')
need('superResLinearRawPath = superResLinearRawPath' in stack,'RawStackResult does not publish SR LinearRaw')
need('superResLinearRawPathForCleanup' in bridge,'bridge lacks SR LinearRaw lifecycle owner')
need('stacked.superResLinearRawPath,' in bridge,'bridge does not publish actual LinearRaw path')
need('26561 Sabre SR must preserve native 1x normalized16 DNG ownership' not in bridge,'stale native-only DNG assertion survived')
print('PASS Sabre 2x LinearRaw producer/publish/lifecycle; pre-VGN camera-domain base + NORMAL fine detail')

shader=SC['superResLinearRaw26562']
for fragment in [
    'uniform highp usampler2D uNativeRgb;',
    'uniform sampler2D uAccumulatedDetail;',
    'float supportGate = smoothstep(1.0, supportEnd, minimumSupport);',
    'float signalGate = smoothstep(0.002, 0.020, blockMean);',
    'float logDetail = clamp(log2(max(currentLuma, 1.0e-6) / blockMean), -0.75, 0.75);',
    'float trustedLogDetail = logDetail * supportGate * signalGate;',
    'float detailFactor = exp2(trustedLogDetail);',
    'vec3 linearRgb = clamp(nativeRgbAt(sourceCoordinate) * detailFactor, 0.0, 1.0);',
]: need(fragment in shader,f'new SR LinearRaw shader missing exact contract: {fragment}')
# Exact detail math core matches 26561 resolver; no saturation/color transform.
resolver=SC['superResDetailResolve26561']
for fragment in ['smoothstep(1.0, supportEnd, minimumSupport)','smoothstep(0.002, 0.020, blockMean)','-0.75, 0.75','logDetail * supportGate * signalGate']:
    need(fragment in resolver and fragment in shader,f'LinearRaw detail core diverges from 26561 resolver fragment={fragment}')
need('saturation' not in shader.lower() and 'ColorMatrix' not in shader,'SR LinearRaw shader introduces presentation color math')
print('PASS new 2x LinearRaw shader reuses exact 26561 signed-log detail gates and preserves RGB ratios')

writer=t(cand,'src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java')
need('PHOTOMETRIC_LINEAR_RAW = 34892' in writer and 'SAMPLES_PER_PIXEL = 3' in writer,'new DNG is not 3-channel LinearRaw')
need('TAG_NOISE_PROFILE' not in writer and 'noiseProfile' not in writer,'invalid Bayer NoiseProfile leaked into SR LinearRaw DNG')
need('Motion Spatial Super Res' not in writer and 'Spatial' not in writer,'stale Spatial DNG provenance survived')
need('Iris 26562' in writer and 'Sabre Super Res LinearRaw' in writer,'Sabre DNG provenance missing')
need(writer.count('entries.add(longEntry(TAG_IMAGE_WIDTH, width));')==1,'duplicate TIFF ImageWidth entry')
need('Math.multiplyExact(Math.multiplyExact((long) width, (long) height), 6L)' in writer,'RGB16 6-byte/pixel payload contract missing')
print('PASS Sabre LinearRaw DNG serializer: RGB16, no fake CFA, no stale Spatial provenance/noise tag')

hdrx=t(cand,'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
need(hdrx.count('IrisSabreSuperResDngWriter.write')==2,'Motion RAW-only/deferred DNG paths not both Sabre-owned')
need('IrisMotionSuperResDngWriter' not in hdrx,'old Spatial DNG writer active in Motion')
need('IRIS_26562_MOTION_SR_DNG_DEGRADED_TO_NATIVE' in hdrx,'Motion missing explicit SR DNG degrade log')
img=t(cand,'src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
need('IRIS_26562_MOTION_SR_JPEG_DEGRADED_TO_NATIVE' in img,'Motion missing SR JPEG publication resilience')
need('saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);' in img,'Motion SR failure does not retain native multiframe encoder')
print('PASS Motion SR JPEG/DNG publication resilience remains multiframe Sabre')

# Lifecycle reset.
mon=t(cand,'src/main/java/com/particlesdevs/photoncamera/util/log/ActivityLifecycleMonitor.java')
frag=t(cand,'src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
ui=t(cand,'src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
zoom=t(cand,'src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java')
app=t(cand,'src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java')
need('iris26562StartedActivities' in mon and 'IRIS_26562_MAIN.post' in mon,'app-wide delayed started-count background detector missing')
need('iris26562StartedActivities != 0' in mon,'internal activity handoff protection missing')
need('IRIS_26562_FOREGROUND_RESET_DEFERRED processing=true cameraResume=false' in frag,'in-flight processing reset defer missing')
need('PreferenceKeys.setCameraModeOrdinal(CameraMode.MOTION.ordinal());' in frag and 'PreferenceKeys.setIrisSuperRes(false);' in frag,'foreground mode/SR reset missing')
need('IrisZoomController.resetForForegroundSession();' in frag,'foreground physical 1x owner reset missing')
need('mCameraUIView.forceForegroundMotionReset();' in frag,'retained UI reset missing')
need('if (iris26562ApplyForegroundResetIfReady())' in frag,'camera resume not gated by reset readiness')
reset_block=ui[ui.index('public void forceForegroundMotionReset()'):ui.index('@Override\n    public void refresh',ui.index('public void forceForegroundMotionReset()'))]
need('uiEventsListener.onCameraModeChanged' not in reset_block,'UI reset fires duplicate camera mode callback')
need('currentState.reConfigureModeViews(CameraMode.MOTION);' in reset_block,'retained UI reset does not run full Motion UI-only reconfiguration')
need('mProcessingProgressBar.setVisibility(View.GONE);' in reset_block and 'mVideoRecordingInfo.setVisibility(View.GONE);' in reset_block,'retained foreground reset leaves stale video/processing overlays')
need('staleVideoUiCleared=true' in reset_block,'foreground UI cleanup regression marker missing')
need('resetForForegroundSession()' in zoom and 'resetForNewCameraActivitySession();' in zoom[zoom.index('resetForForegroundSession()'):zoom.index('public void onLensInventoryReady()')],'foreground reset does not reuse proven 1x state primitive')
need('PreferenceKeys.setIrisSuperRes(false);' in app,'cold start does not reset SR off')
print('PASS cold/background lifecycle contract: defer processing; Motion + physical 1x + SR OFF; no duplicate UI restart')

# Existing camera inventory ordering must stay: onOpenCamera -> init list -> 1x inventory owner before route is elsewhere.
need('irisZoomController.onLensInventoryReady();' in frag,'1x inventory owner callback lost')

# Exact icon geometry mapping from supplied SVGs.
for rel in ['src/main/res/drawable/ic_super_res_on.xml','src/main/res/drawable/ic_super_res_off.xml']:
    ET.fromstring(t(cand,rel))
on=t(cand,'src/main/res/drawable/ic_super_res_on.xml'); off=t(cand,'src/main/res/drawable/ic_super_res_off.xml')
need('viewportWidth="24"' in on and 'M2.5,18.5 L8.5,9.5 L11.5,13.5 L14.5,9 L21.5,18.5 Z' in on and 'strokeWidth="1.6"' in on,'ON icon not supplied geometry')
for opacity in ('0.35','0.5','0.4','0.3','0.55'): need(f'strokeAlpha="{opacity}"' in off,f'OFF icon missing supplied opacity {opacity}')
for pathdata in ('M2.5,18.5 L8.5,9.5 L11.5,13.5 L14.5,9 L21.5,18.5 Z','M2.2,18.8 L8.2,9.8 L11.2,13.8 L14.2,9.3 L21.2,18.8 Z','M2.8,18.2 L8.8,9.2 L11.8,13.2 L14.8,8.7 L21.8,18.2 Z'): need(pathdata in off,'OFF icon missing supplied ghosted mountain path')
print('PASS exact supplied Super Res ON/OFF icon geometry mapping')

# Version.
ver=t(cand,'version.properties')
need('VERSION_NAME=0.9726562' in ver and 'VERSION_BUILD=26562' in ver,'version/build not 26562')

# Protect unrelated ownership bytes.
protected=[
'src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'src/main/res/xml/preferences.xml',
]
for rel in protected: need(b(base,rel)==b(cand,rel),f'protected unrelated owner changed: {rel}')
print(f'PASS protected unrelated merge/VGN/encoder/frame-policy/settings bytes invariant ({len(protected)} files)')
print('PASS 26562 focused architectural validation')
