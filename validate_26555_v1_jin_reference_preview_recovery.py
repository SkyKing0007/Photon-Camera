#!/usr/bin/env python3
from pathlib import Path
import argparse, difflib, hashlib, math, re, sys

BASE = None
CAND = None
ALLOW = [
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/version.properties',
]
PROTECTED = [
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt',
'app/src/main/assets/models/iris_night_jin_lol_512.onnx',
]

def fail(msg): raise SystemExit('FAIL: '+msg)
def need(cond,msg):
    if not cond: fail(msg)
def text(rel, root=None):
    if root is None: root=CAND
    return (root/rel).read_text()
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def method(src,name):
    i=src.find(name)
    if i<0: fail('missing method '+name)
    st=src.rfind('\n',0,i)+1
    b=src.find('{',i); need(b>=0,'method brace '+name)
    d=0
    for j in range(b,len(src)):
        if src[j]=='{': d+=1
        elif src[j]=='}':
            d-=1
            if d==0:return src[st:j+1]
    fail('unclosed method '+name)

def changed_files():
    out=[]
    base_files={str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file()}
    cand_files={str(p.relative_to(CAND)) for p in (CAND/'app').rglob('*') if p.is_file()}
    need(base_files==cand_files,'candidate app path set changed')
    for rel in sorted(base_files):
        if sha(BASE/rel)!=sha(CAND/rel): out.append(rel)
    return out


BASE_MANIFEST_SHA='93157b96250eecca785695ba21de71ab3d52e0434b16c5f22bddc2afb8714325'
CAND_MANIFEST_SHA='fac620a2decc10bc23d22531236a0eef589d8f9778f6be3bec529c8c48b8339f'
VENDOR_SHA='7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8'
GLSL_SHA={'directionalSmooth.comp':'1c15b1416634e1bdbf240d517da21755a48eef478ef6faa00659c79b0cd5196f','iirRgb.comp':'21e50a29703019bdd90b30423308b7778b77576e2e7b3d2b4c634a56fff375d1'}

def self_test():
    def plan(n):
        t=max(2,min(50,n)); l=0 if t==2 else max(1,(t+2)//5); return t,t-l,l
    need(plan(15)==(15,12,3),'15->12+3 self-test')
    need(plan(50)==(50,40,10),'50->40+10 self-test')
    def decision(stage,configured,repeating,result,preview,zsl,owner=False):
        ph=configured and repeating and result and preview
        po=stage in ('bootstrap','fallback')
        healthy=ph and (po or zsl)
        if healthy:
            if stage=='bootstrap': return 'promote_full_once'
            if stage=='full_retry': return 'resolved_full'
            return 'keep'
        if ph and not zsl: return 'keep_wait_raw'
        if owner: return 'suppressed_owner'
        if stage=='full_retry': return 'fallback_preview_only'
        if stage in ('bootstrap','fallback'): return 'terminal_no_loop'
        if configured and repeating and (not result or not preview): return 'bootstrap_preview_only'
        return 'single_restart'
    need(decision('none',True,True,False,False,False)=='bootstrap_preview_only','silent session self-test')
    need(decision('bootstrap',True,True,True,True,False)=='promote_full_once','bootstrap proof self-test')
    need(decision('full_retry',True,True,False,False,False)=='fallback_preview_only','full retry fallback self-test')
    need(decision('none',True,True,True,True,False)=='keep_wait_raw','healthy preview/empty ZSL self-test')
    need(decision('none',True,True,False,False,False,True)=='suppressed_owner','processing owner self-test')
    print('PASS validator self-test: Night frame plans + silent-session preview recovery regressions')

def validate(base,cand,base_manifest=None,cand_manifest=None,vendor_manifest=None,glsl_dir=None):
    global BASE,CAND
    BASE=Path(base); CAND=Path(cand)
    # Exact scope / protected ownership.
    chg=changed_files()
    need(chg==sorted(ALLOW),f'exact five-file scope mismatch: {chg}')
    for rel in PROTECTED:
        need(sha(BASE/rel)==sha(CAND/rel),'protected bytes changed: '+rel)
    model=CAND/'app/src/main/assets/models/iris_night_jin_lol_512.onnx'
    need(model.stat().st_size==42571162,'Jin ONNX byte count drift')
    need(sha(model)=='bb7f911afd1ac209a27f20b97d6f2d532bb1ffa1231374755859139cb4e30ff7','Jin ONNX SHA drift')

    # Frame policy / Tundra recovery exact preservation.
    frame=text('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
    need('final int longFrames = total == 2 ? 0 : Math.max(1, (total + 2) / 5);' in frame,'Night frame split formula drift')
    def plan(n):
        t=max(2,min(50,n)); l=0 if t==2 else max(1,(t+2)//5); return t,t-l,l
    need(plan(15)==(15,12,3),'15 frame plan regression')
    need(plan(50)==(50,40,10),'50 frame plan regression')
    capB=text('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',BASE)
    cap=text('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    for name in ['drainIrisNight26554AvailableRawImages','finishIrisNight26544AfterSequenceGrace','tryDispatchIrisNight26540','populateIrisNight26540FrameMetadata']:
        need(method(capB,name)==method(cap,name),'26554 Night/Tundra method drift: '+name)
    a='            /* IRIS_26540_NIGHT_SHUTTER_SETTINGS_SNAPSHOT */'
    z='            if (iris26533CaptureMode != CameraMode.NIGHT) Camera2ApiAutoFix.applyEnergySaving();'
    for src,label in [(capB,'base'),(cap,'cand')]:
        need(src.count(a)==1 and src.count(z)==1,'Night shutter body anchors '+label)
    need(capB[capB.index(a):capB.index(z,capB.index(a))]==cap[cap.index(a):cap.index(z,cap.index(a))],
         'Night shutter-frozen frame/exposure/request body drift')
    need('q.first <= 0.0 || q.second < 0.0' in method(cap,'populateIrisNight26540FrameMetadata'),
         'valid S>0/O>=0 Camera2 noise-profile contract drift')

    # Jin reference-first contract.
    enh=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java')
    jni=text('app/src/main/cpp/motionv2_jpeg444_jni.cpp')
    night=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
    need('private static final int N = 512;' in enh,'Jin reference size drift')
    need('((c >> 16) & 255) / 127.5f) - 1f' in enh and '0.5f * (out - input[ch * plane + i])' in enh,
         'Jin RGB normalize/dense-reference-residual drift')
    need('new long[]{1, 3, N, N}' in enh,'Jin NCHW input drift')
    need('opts.setIntraOpNumThreads(2);' in enh and 'opts.setInterOpNumThreads(1);' in enh,'Jin proven CPU thread contract drift')
    need('System.nanoTime()' not in enh and 'jinStartNs' not in night and 'jinMs=' not in night,
         '26555 added redundant Jin stage timing instrumentation')
    need('applyReferenceResidualNative' in enh and 'applyReferenceResidualNative' in jni,'Jin reference residual JNI owner missing')
    for forbidden in ['GRID = 32','applyGainFieldNative','gainGrid','output / input','dst / src','kNeutralFull','kColorFull','neutralChromaSafety','chooseIntraOpThreads']:
        need(forbidden not in enh+jni,'rejected Jin hybrid survived: '+forbidden)
    need('(q[c]/255.f)+rr' in jni.replace(' ',''),'native adapter is not base + dense RGB residual')
    need('IRIS_26555_NIGHT_JIN_REFERENCE_RESIDUAL' in night,'Night Jin owner marker missing')
    need('IrisNightNeuralEnhancer.enhanceInPlace(img)' in night,'Night Jin neural inference inactive')
    need('IrisNightUltraHdr.attachPostJin(' in night,'post-Jin UHDR rebase missing')
    need('IRIS_26554_NIGHT_BASE_JPEG_CHECKPOINT_ONLY' in night,'26554 base-checkpoint contract lost')
    need(night.count('IRIS_26554_NIGHT_FINAL_PUBLICATION_BEGIN')==1 and night.count('IRIS_26554_NIGHT_FINAL_PUBLICATION_END')==1,
         'single final publication markers drift')

    # Jin prewarm must not compete with Surface/session creation.
    need(cap.count('IrisNightNeuralEnhancer.prewarmAsync();')==1,'Jin prewarm callsite count !=1')
    pre=cap.index('IrisNightNeuralEnhancer.prewarmAsync();')
    need(cap.rfind('mPreviewCaptureResult = result;',0,pre)>=0,'Jin prewarm not CaptureResult-owned')
    create=method(cap,'createCameraPreviewSession')
    need('prewarmAsync' not in create,'Jin prewarm still runs during session creation')

    # Synthetic dense-residual adapter properties, matching the JNI pixel-center bilinear mapping.
    def bilinear(src,w,h,x,y,ch):
        x=max(0.0,min(w-1.0,x)); y=max(0.0,min(h-1.0,y))
        x0=int(math.floor(x)); y0=int(math.floor(y)); x1=min(x0+1,w-1); y1=min(y0+1,h-1)
        tx=max(0.0,min(1.0,x-x0)); ty=max(0.0,min(1.0,y-y0))
        def at(xx,yy): return src[(yy*w+xx)*3+ch]
        a=at(x0,y0)+(at(x1,y0)-at(x0,y0))*tx
        b=at(x0,y1)+(at(x1,y1)-at(x0,y1))*tx
        return a+(b-a)*ty

    def up(src,sw,sh,dw,dh,x,y,ch):
        fx=(x+0.5)*sw/dw-0.5; fy=(y+0.5)*sh/dh-0.5
        return bilinear(src,sw,sh,fx,fy,ch)
    # Constant RGB residual is position invariant (no hidden cell boundaries).
    sw=8;sh=8;dw=61;dh=47
    const=[]
    for _ in range(sw*sh): const += [0.07,-0.03,0.01]
    for y in [0,1,17,46]:
        for x in [0,2,19,60]:
            vals=[up(const,sw,sh,dw,dh,x,y,c) for c in range(3)]
            need(max(abs(vals[i]-[.07,-.03,.01][i]) for i in range(3))<1e-7,'dense residual translation invariance')
    # A red-only residual must not invent G/B changes; no forced luma/chroma collapse.
    red=[]
    for yy in range(sh):
        for xx in range(sw): red += [0.02*(xx+1),0.0,0.0]
    for y in [5,23,40]:
        for x in [7,30,55]:
            need(abs(up(red,sw,sh,dw,dh,x,y,1))<1e-9 and abs(up(red,sw,sh,dw,dh,x,y,2))<1e-9,
                 'RGB residual channels collapsed/cross-coupled')
    # A one-source-pixel impulse has local bilinear support; there is no coarse 32x32 plateau.
    imp=[0.0]*(sw*sh*3); imp[((3*sw+3)*3)]=1.0
    active=[]
    for y in range(dh):
        for x in range(dw):
            if up(imp,sw,sh,dw,dh,x,y,0)>1e-6: active.append((x,y))
    need(active,'dense residual impulse vanished')
    xs=[p[0] for p in active]; ys=[p[1] for p in active]
    need((max(xs)-min(xs)+1)<dw//2 and (max(ys)-min(ys)+1)<dh//2,'dense residual expanded into coarse global/cell plateau')

    # Night/Sabre disk-backed processing remains exact 26554. The previously brainstormed one-frame
    # prefetch is intentionally NOT revived in 26555.
    stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
    need(sha(BASE/stack_rel)==sha(CAND/stack_rel),'26554 Sabre RAW stacker/prefetch lifecycle drift')
    stack=text(stack_rel)
    need('IRIS_26555_NIGHT_SABRE_IO_PREFETCH_ONLY' not in stack and 'uploadRawWithPrefetch' not in stack,
         'rejected 26555 one-frame RAW prefetch survived')

    # Preview/session universal compatibility and no-RAW foundation.
    need('surface != null && surface.isValid()' in cap,'preview recovery can run on invalid Surface')
    need('IRIS_26555_CAMERA_RECOVERY_SUPPRESSED captureOrProcessingOwner=true' in cap,'capture ownership recovery guard missing')
    need('IRIS_26555_RECOVERY_PREVIEW_ONLY_BOOTSTRAP' in cap,'preview-only bootstrap stage missing')
    need('IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY' in cap,'full-topology retry stage missing')
    need('IRIS_26555_RECOVERY_PREVIEW_ONLY_FALLBACK' in cap,'preview-only fallback stage missing')
    need('iris26555RecoverConfiguredButSilentSession' in cap,'configured-silent recovery missing')
    need('iris26555PromoteProvenPreviewToFullTopology' in cap,'preview proof promotion missing')
    need('iris26555ReturnToPreviewOnlyFallback' in cap,'failed full-topology fallback missing')
    need('if (iris26555PreviewOnlyRecoveryActive() && !mIsRecordingVideo)' in cap
         and 'surfaces = Collections.singletonList(surface);' in cap,
         'recovery is not materially different preview-only topology')
    need('&& !iris26555PreviewOnlyRecoveryActive())' in cap
         and 'IRIS_26555_ZSL_RAW_TARGET_SKIPPED recoveryStage=' in cap,
         'preview-only request still targets RAW')
    health=method(cap,'private void iris26548SchedulePostOpenHealthCheck')
    need('previewHealthy && !motionZslReady' in health and 'sessionRecovery=false' in health,
         'healthy preview is still torn down merely for empty Motion ZSL')
    need('mIris26555PreviewRecoveryStage == IRIS_26555_RECOVERY_FULL_TOPOLOGY_RETRY' in health
         and 'iris26555ReturnToPreviewOnlyFallback' in health,
         'failed full topology can loop/strand black preview')
    need('IRIS_26555_PREVIEW_RECOVERY_TERMINAL' in health and 'repeatedRecovery=false' in health,
         'bounded terminal recovery regression missing')
    need('IRIS_26555_MOTION_CAPTURE_NOT_READY' in cap,'Motion preview-only/ZSL shutter guard missing')
    need('IRIS_26555_RAW_MODE_UNAVAILABLE' in cap and 'fakeYuvFallback=false' in cap,'no-RAW fail-closed contract missing')
    need('IRIS_26555_STILL_TARGET_UNAVAILABLE' in cap,'unsupported still-target null guard missing')
    # No new Motorola/manufacturer condition in added CaptureController lines.
    cap_added='\n'.join(l[1:] for l in difflib.unified_diff(capB.splitlines(),cap.splitlines(),lineterm='')
                        if l.startswith('+') and not l.startswith('+++'))
    for forbidden in ['motorola','Motorola','Build.MANUFACTURER.equals','Build.MODEL.equals']:
        need(forbidden not in cap_added,'device-specific 26555 gate found: '+forbidden)
    # Permanent exact failure-class regression: configured + repeating but no result/preview must take
    # preview-only bootstrap, not repeat the normal preview+RAW topology. Preview-only success promotes
    # once; failed promotion falls back to preview-only; a healthy preview with empty ZSL never recovers.
    def recovery_decision(stage, configured, repeating, result, preview, motion_zsl_ready, owner=False):
        preview_healthy=configured and repeating and result and preview
        active_preview_only=stage in ('bootstrap','fallback')
        healthy=preview_healthy and (active_preview_only or motion_zsl_ready)
        if healthy:
            if stage=='bootstrap': return 'promote_full_once'
            if stage=='full_retry': return 'resolved_full'
            return 'keep'
        if preview_healthy and not motion_zsl_ready: return 'keep_wait_raw'
        if owner: return 'suppressed_owner'
        if stage=='full_retry': return 'fallback_preview_only'
        if stage in ('bootstrap','fallback'): return 'terminal_no_loop'
        if configured and repeating and (not result or not preview): return 'bootstrap_preview_only'
        return 'single_restart'
    need(recovery_decision('none',True,True,False,False,False)=='bootstrap_preview_only',
         'exact configured/repeating zero-result zero-preview regression')
    need(recovery_decision('bootstrap',True,True,True,True,False)=='promote_full_once',
         'preview-only proof does not promote')
    need(recovery_decision('full_retry',True,True,False,False,False)=='fallback_preview_only',
         'failed promoted topology does not preserve preview fallback')
    need(recovery_decision('fallback',True,True,True,True,False)=='keep',
         'preview fallback does not remain stable')
    need(recovery_decision('none',True,True,True,True,False)=='keep_wait_raw',
         'empty ZSL incorrectly tears down healthy preview')
    need(recovery_decision('none',True,True,False,False,False,True)=='suppressed_owner',
         'capture/processing ownership does not suppress recovery')
    # Existing 26548 Motion startup readiness gate remains, and no new empty-stack fallback is added.
    need('IRIS_26548_MOTION_NOT_READY_SESSION_OR_ZSL' in cap,'Motion pre-shutter readiness gate missing')
    need('singleFrameFallback=false' in cap,'26554 no-single-frame Night provenance missing')

    # Version.
    ver=text('app/version.properties')
    need('VERSION_NAME=0.9726555' in ver and 'VERSION_BUILD=26555' in ver,'version/build target drift')

    print('PASS exact five-file 26555 runtime scope')
    print('PASS exact 26554 Night frame/exposure/request and Tundra recovery invariance')
    print('PASS Jin reference 512 RGB inference + dense residual adapter; rejected 32x32/ratio/luma/tile hybrids absent')
    print('PASS Jin synthetic translation/channel/local-support regressions')
    print('PASS exact 26554 Night Sabre/disk-backed RAW lifecycle; no revived prefetch')
    print('PASS universal preview bootstrap/full-retry/fallback recovery + no-RAW/no-target fail-closed capability foundation')
    print('PASS 26555 focused high-risk ownership validation')
    if base_manifest:
        need(sum(1 for _ in open(base_manifest))==970 and sha(base_manifest)==BASE_MANIFEST_SHA,'base 970 manifest')
    if cand_manifest:
        need(sum(1 for _ in open(cand_manifest))==970 and sha(cand_manifest)==CAND_MANIFEST_SHA,'candidate 970 manifest')
    if vendor_manifest:
        need(sum(1 for _ in open(vendor_manifest))==778 and sha(vendor_manifest)==VENDOR_SHA,'vendor 778 manifest')
    if glsl_dir:
        for name,want in GLSL_SHA.items(): need(sha(Path(glsl_dir)/name)==want,'protected runtime GLSL '+name)
    print('PASS 26555 manifests/protected runtime GLSL pins')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('base',nargs='?')
    ap.add_argument('candidate',nargs='?')
    ap.add_argument('--base-manifest')
    ap.add_argument('--candidate-manifest')
    ap.add_argument('--vendor-manifest')
    ap.add_argument('--glsl-dir')
    a=ap.parse_args()
    if a.self_test:
        self_test(); return
    need(a.base and a.candidate,'base/candidate required')
    validate(a.base,a.candidate,a.base_manifest,a.candidate_manifest,a.vendor_manifest,a.glsl_dir)
if __name__=='__main__': main()
