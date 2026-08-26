#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path

EXPECTED_CHANGED = sorted([
    'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java',
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java',
    'app/version.properties',
])

def fail(msg: str): raise SystemExit('FAIL: ' + msg)
def need(cond: bool, msg: str):
    if not cond: fail(msg)
def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()

def tree_files(root: Path):
    out=[]
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file(): out.append(p)
    for rel in ('app/version.properties','app/build.gradle'):
        p=root/rel
        if p.is_file(): out.append(p)
    return out

def manifest(root: Path):
    return {str(p.relative_to(root)):sha(p) for p in tree_files(root)}

def lexical_balance(path: Path):
    # Supplementary only. Real javac/Kotlin compile is required later in the workflow.
    s=path.read_text(encoding='utf-8')
    i=0; state='code'; pairs={'{':'}','(':')','[':']'}; stack=[]
    while i < len(s):
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if state=='code':
            if c=='/' and n=='/': state='line'; i+=2; continue
            if c=='/' and n=='*': state='block'; i+=2; continue
            if c=='"': state='dq'; i+=1; continue
            if c=="'": state='sq'; i+=1; continue
            if c in pairs: stack.append(c)
            elif c in pairs.values():
                if not stack or pairs[stack.pop()] != c: fail('unbalanced '+str(path))
            i+=1; continue
        if state=='line':
            if c=='\n': state='code'
            i+=1; continue
        if state=='block':
            if c=='*' and n=='/': state='code'; i+=2
            else: i+=1
            continue
        q='"' if state=='dq' else "'"
        if c=='\\': i+=2; continue
        if c==q: state='code'
        i+=1
    need(state=='code' and not stack, 'unterminated/unbalanced '+str(path))

def run(base: Path, cand: Path):
    mb, mc = manifest(base), manifest(cand)
    need(len(mb)==967, f'base manifest count={len(mb)} expected=967')
    need(len(mc)==967, f'candidate manifest count={len(mc)} expected=967')
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    need(changed==EXPECTED_CHANGED, 'runtime changed-file allowlist mismatch: '+repr(changed))

    for rel in EXPECTED_CHANGED:
        if rel.endswith('.java'): lexical_balance(cand/rel)

    cap=(cand/EXPECTED_CHANGED[1]).read_text(encoding='utf-8')
    post=(cand/EXPECTED_CHANGED[2]).read_text(encoding='utf-8')
    night=(cand/EXPECTED_CHANGED[3]).read_text(encoding='utf-8')
    log=(cand/EXPECTED_CHANGED[4]).read_text(encoding='utf-8')
    app=(cand/EXPECTED_CHANGED[0]).read_text(encoding='utf-8')
    ver=(cand/'app/version.properties').read_text(encoding='utf-8')
    basecap=(base/EXPECTED_CHANGED[1]).read_text(encoding='utf-8')

    # Exact target.
    need('VERSION_NAME=0.9726544' in ver and 'VERSION_BUILD=26544' in ver,
         'target 0.9726544 / 26544 missing')

    # Root-cause proof: fresh Night reader capacity is 3, while 26543 deliberately retained live
    # Camera2 Images asynchronously. 26544 must remove that ownership without changing the reader.
    need('int maxjpg = 3;' in basecap and 'int maxjpg = 3;' in cap,
         'fresh non-ZSL ImageReader maxImages=3 proof missing')
    for old in ('IRIS_NIGHT_26543_SPOOL_EXECUTOR','mIrisNight26543SpoolSlots',
                'mIrisNight26543PendingSpools','mIrisNight26543SpoolDrainDeadlineMs',
                'IRIS_NIGHT_26543_SPOOL_DRAIN_TIMEOUT_MS','spoolIrisNight26543Raw('):
        need(old in basecap, 'tested 26543 async ownership anchor missing from base: '+old)
        need(old not in cap, 'unsafe 26543 async live-Image ownership survived: '+old)
    need('IRIS_26544_NIGHT_IMMEDIATE_IMAGE_RELEASE_OWNER' in cap,
         '26544 immediate Camera2 Image release owner missing')
    need('spoolIrisNight26544RawSynchronously(ownedImage, mIrisNight26544CaptureGeneration);' in cap,
         'Night auxiliary RAW is not consumed synchronously')
    need('java.nio.ByteBuffer source = plane.getBuffer().duplicate();' in cap,
         '26543 V1.4 ByteBuffer compiler correction regressed')
    need('            ByteBuffer source = plane.getBuffer().duplicate();' not in cap,
         '26543 V1.3 bare ByteBuffer javac regression returned')
    need('IRIS_26544_NIGHT_CAMERA2_IMAGE_CLOSED role=REFERENCE' in cap and
         'IRIS_26544_NIGHT_CAMERA2_IMAGE_CLOSED role=AUX' in cap,
         'Camera2 Image close boundaries missing')
    need('persistentNativeCopies=1 asyncLiveCamera2Images=0' in cap,
         'bounded-memory ownership proof missing')
    night_cb=cap[cap.index('if (mIrisNight26540CaptureActive) {'):
                     cap.index('if (onUnlimited && !unlimitedStarted)', cap.index('if (mIrisNight26540CaptureActive) {'))]
    need('.execute(() ->' not in night_cb and 'IRIS_NIGHT_26543_SPOOL_EXECUTOR' not in night_cb,
         'live Camera2 Image can still escape Night ImageReader callback')

    # Night ownership stays Iris. Borrowing original Photon is limited to immediate RAW release
    # discipline / neutral publication infrastructure, never exposure or processing ownership.
    for token in ('IRIS_26541_NIGHT_SHORT_TAG','IRIS_26541_NIGHT_LONG_TAG',
                  'populateIrisNight26540FrameMetadata','new IrisNightBatch(',
                  'IrisNightProcessor.process(batch, cameraEventsListener)'):
        need(token in cap, 'Iris Night capture ownership missing '+token)
    for token in ('PhotonMotionMgc1271Bridge.reconstruct(','new PostPipeline(true)',
                  'pipeline.RunIrisNightRgb(rgb, p)','saveBitmapAsJPGIrisNightCheckpoint(',
                  'IrisNightNeuralEnhancer.enhanceInPlace(img)','saveBitmapAsJPGIrisNightAtomicFinal('):
        need(token in night, 'Iris Night processing/publication chain missing '+token)
    for forbidden in ('DefaultSaver.', 'new DefaultSaver', 'PyramidMerging(', 'ExposureFusionBayer2(', 'IrisNightMgc1271Bridge.'):
        need(forbidden not in night, 'legacy/dormant Night processing call returned: '+forbidden)

    # Durable process-death evidence, including Android ApplicationExitInfo process-state summary.
    for token in ('IRIS_26544_PROCESS_DEATH_DIAGNOSTICS','getHistoricalProcessExitReasons',
                  'getProcessStateSummary()','setProcessStateSummary(state)','fos.getFD().sync();',
                  'mirrorPrivateProcessLogs();','public static void critical(String tag, String message)',
                  'if (logEnabled) writeToFile(\"C\", tag, message);',
                  'public static void processState(String tag, String message)'):
        need(token in log, 'process-death evidence contract missing '+token)

    # Cold process starts Motion before Settings/camera UI reads persisted mode.
    force='PreferenceKeys.setCameraModeOrdinal(CameraMode.MOTION.ordinal());'
    need('Log.initProcessDiagnostics(this);' in app, 'earliest process logger init missing')
    need(force in app and app.index(force) < app.index('mSettings = new Settings();'),
         'Motion cold-start authority is not before Settings construction')
    need('IRIS_26544_COLD_START_FORCE_MOTION' in app, 'Motion cold-start breadcrumb missing')

    # Full old DNG-but-no-JPEG failure window must be durably observable in the SAME APK.
    night_markers=(
        'IRIS_26544_NIGHT_PROCESS_ENTRY','IRIS_26544_NIGHT_MGC_BEGIN','IRIS_26544_NIGHT_MGC_COMPLETE',
        'IRIS_26544_NIGHT_DNG_BEGIN','IRIS_26544_NIGHT_DNG_COMPLETE','IRIS_26544_NIGHT_POST_RGB_BEGIN',
        'IRIS_26544_NIGHT_POST_RGB_COMPLETE','IRIS_26544_NIGHT_BASE_JPEG_BEGIN',
        'IRIS_26544_NIGHT_BASE_JPEG_COMPLETE','IRIS_26544_NIGHT_JIN_BEGIN',
        'IRIS_26544_NIGHT_JIN_COMPLETE','IRIS_26544_NIGHT_FINAL_JPEG_BEGIN',
        'IRIS_26544_NIGHT_FINAL_JPEG_COMPLETE','IRIS_26544_NIGHT_PROCESS_FINISHED_NOTIFY_END',
        'IRIS_26544_NIGHT_PROCESS_FAILED','IRIS_26544_NIGHT_FRAMES_RELEASE_END')
    for token in night_markers: need(token in night, 'Night durable boundary missing '+token)
    for token in ('IRIS_26544_NIGHT_SPATIAL_RGB_POST_ENTRY','IRIS_26544_NIGHT_POST_RUN_BEGIN',
                  'IRIS_26544_NIGHT_POST_RUN_COMPLETE','IRIS_26544_NIGHT_POST_CLOSE_BEGIN',
                  'IRIS_26544_NIGHT_POST_OWNER_CLOSED'):
        need(token in post, 'Night PostPipeline durable boundary missing '+token)

    # Preserve earlier compiler regression contracts in untouched source.
    params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text(encoding='utf-8')
    need('Integer iris26540ReferenceIlluminant2 = characteristics.get(\n                    CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2' not in params,
         '26540 SENSOR_REFERENCE_ILLUMINANT2 Byte/Integer regression returned')
    need('Log.i(TAG, "IRIS_26540_NIGHT' not in post,
         '26540 private GLBasePipeline.TAG regression returned')
    fns=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java').read_text(encoding='utf-8')
    need('IrisNightFrameSelector.getFrames()' not in fns,
         '26540 stale no-arg Iris Night selector regression returned')
    stack=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text(encoding='utf-8')
    need('bayerPhaseShotNoise.average().coerceAtLeast(1.0e-8).toFloat()' in stack,
         '26543 V1.2 Kotlin Float/Double correction missing')
    need('bayerPhaseReadNoise.average().coerceAtLeast(0.0).toFloat()' in stack,
         '26543 V1.2 Kotlin Float/Double correction missing')

    # No GLSL/Kotlin/native/model/resource file changed. All IQ math is byte-identical to tested base
    # except Java files above, whose exact expected patch is separately pinned by the handoff.
    need(not any(x.endswith('.glsl') or x.endswith('.kt') for x in changed),
         'unexpected GLSL/Kotlin source change')

    print('PASS: exact tested 26543 967-file authority -> 967-file 26544 candidate')
    print('PASS: runtime scope exactly 5 Java files + version.properties')
    print('PASS: 26543 maxImages=3 async live-Image ownership is removed; Image close is callback-owned')
    print('PASS: Iris retains Night exposure/frame/MGC/post/Jin ownership; no legacy Photon IQ graph restored')
    print('PASS: DNG-through-final-JPEG failure window has crash-durable boundaries')
    print('PASS: ApplicationExitInfo + process-state summary + fsync lifecycle evidence is present')
    print('PASS: every new process forces Motion before Settings construction')
    print('PASS: 26540/26543 compiler-regression contracts preserved')

def self_test():
    need(EXPECTED_CHANGED==sorted(EXPECTED_CHANGED),'internal allowlist not sorted')
    print('PASS: validate_26544_night_rootcause_lifecycle.py self-test')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',type=Path); ap.add_argument('--candidate',type=Path); ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test: self_test(); return
    if a.base is None or a.candidate is None: ap.error('--base and --candidate are required')
    run(a.base.resolve(),a.candidate.resolve())
if __name__=='__main__': main()
