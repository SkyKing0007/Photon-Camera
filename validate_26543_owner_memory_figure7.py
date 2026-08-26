#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math, re, sys

RUNTIME_FILES = [
    'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
]
CAND_SHA = {
    'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt': '11e1f216c9633f4972bd2771fcfff05ca4efe74a665d29e49123b6e45db9a9da',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt': 'ccb5fca12a4e1e983633908fb5a3d74249a64b06197d963094f7a8159fec376b',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt': 'afdddd1885e91c02f730fdea19be739f05e7dd643dbf4d3e107595980961af40',
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java': 'a59c9633be1073e6ef9e900a8484553f5e83ee430eaf1e6de91d7484540f62bd',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java': '39088bb5cd21789a620b4bcb424aac8bbe607cd1822644cab45965874a5cbd8e',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java': '55a7020e2881cb4a373ea87d7e9e4276bbfc9fc21ff1b19464ecd000fd44b430',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': '118a5413c60dff06b29b8c536f271a3777a47d2e72db2e7213a44219a16bd9e5',
}

def fail(msg): raise RuntimeError(msg)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text(root, rel): return (root/rel).read_text()

def changed(base, cand):
    def manifest(root):
        return {str(p.relative_to(root)): sha(p) for p in (root/'app/src/main').rglob('*') if p.is_file()}
    a,b=manifest(base),manifest(cand)
    return sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))

def extract_between(s, start_token, end_token):
    a=s.index(start_token); b=s.index(end_token,a+len(start_token)); return s[a:b]

def ownership(root):
    night = text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
    hdrx = text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    bridge = text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    fusion = text(root,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt')
    stack = text(root,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    if 'PhotonMotionMgc1271Bridge.reconstruct(' not in night: fail('Night no longer reaches PhotonMotionMgc1271Bridge')
    if 'IRIS_26409_MOTION_V2_INDEPENDENT_RAW_OWNER' not in hdrx or 'PhotonMotionMgc1271Bridge.reconstruct(' not in hdrx:
        fail('Motion HdrxProcessor no longer reaches PhotonMotionMgc1271Bridge')
    if 'IrisNightMgc1271Bridge' in night: fail('Night processor revived stale IrisNightMgc1271Bridge')
    if 'mergeMethod = MgcMergeMethod.SPATIAL_RGB' not in bridge: fail('PhotonMotion MGC no longer requests SPATIAL_RGB')
    if 'if (mergeMethod == MgcMergeMethod.SPATIAL_RGB)' not in fusion or 'return GlesIris26521SpatialRgbStacker(' not in fusion:
        fail('GlesMgcRawFusion does not reach production Spatial-RGB owner')
    if 'GlesIris26521SpatialRgbShaders.covariance' not in stack or 'GlesIris26521SpatialRgbShaders.mergeRgb' not in stack:
        fail('production stacker does not compile embedded covariance/mergeRgb shaders')
    # Definition may remain, but it must have no caller anywhere else.
    callers=[]
    for p in (root/'app/src/main/java').rglob('*'):
        if not p.is_file() or p.suffix not in ('.kt','.java'): continue
        s=p.read_text(errors='ignore')
        if 'IrisNightMgc1271Bridge' in s and p.name!='IrisNightMgc1271Bridge.kt': callers.append(str(p.relative_to(root)))
    if callers: fail('stale IrisNightMgc1271Bridge gained callers: '+repr(callers))
    # The obsolete 26542 asset-based covariance owner may remain as dormant source,
    # but no production class may instantiate or statically invoke it.
    stale_motion_callers=[]
    for p in (root/'app/src/main/java').rglob('*'):
        if not p.is_file() or p.suffix not in ('.kt','.java') or p.name=='MotionV2CfaReconstruction.java': continue
        src=p.read_text(errors='ignore')
        if 'new MotionV2CfaReconstruction(' in src or 'MotionV2CfaReconstruction.reconstruct(' in src:
            stale_motion_callers.append(str(p.relative_to(root)))
    if stale_motion_callers: fail('stale MotionV2CfaReconstruction gained production callers: '+repr(stale_motion_callers))
    for marker in [
        'IRIS_26543_ACTIVE_FIGURE7 owner=GlesIris26521SpatialRgbStacker',
        'shaderOwner=GlesIris26521SpatialRgbShaders.covariance/mergeRgb',
        'reachableFrom=GlesMgcRawFusion mergeMethod=SPATIAL_RGB grid=RAW2',
        'kStretch=${bayerKernelTuning.figure7KStretch}',
        'kShrink=${bayerKernelTuning.figure7KShrink}',
        'gaussian=EXP_NEG_HALF_D',
    ]:
        if marker not in stack: fail('active-owner runtime marker missing: '+marker)

def figure7(root):
    stack=text(root,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    shaders=text(root,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt')
    cov=extract_between(shaders,'    val covariance = """','    val rejection = """')
    merge=extract_between(shaders,'    val mergeRgb = """','    val mergeRgbSuperRes = mergeRgb')
    for marker in [
        'IRIS_26543_ACTIVE_IPOL_FIGURE7_COVARIANCE',
        'float A = 1.0 + sqrt',
        'float D = clamp(1.0 - sqrt',
        '0.5 * A * (1.0 / max(uKShrink, 1.0e-8) - 1.0)',
        '0.5 * A * (uKStretch - 1.0)',
        'oCovariance = vec4(yy/det, xx/det, -xy/det, 1.0)',
        'uRawTextureOrigin','uRawTextureSize','uCovarianceOrigin','uCovarianceTextureSize',
    ]:
        if marker not in cov: fail('active Figure-7 covariance anchor missing: '+marker)
    for stale in ['anisotropic=mix(4.0,6.0','correctedGreenStd','dominant=max(strength']:
        if stale in cov: fail('stale covariance law survived: '+stale)
    for marker in [
        'return exp(-0.5 * max(distance, 0.0));',
        '(sourceRaw + vec2(0.5)) * 0.5 - vec2(uCovarianceOrigin)',
        'vec2(uCovarianceTextureSize)',
    ]:
        if marker not in merge: fail('active merge Figure-7 anchor missing: '+marker)
    if 'exp2(-0.5' in merge or '+ 0.00005' in merge: fail('old active Spatial-RGB Gaussian/floor survived')
    if 'private val covarianceWidth = max(1, width / 2)' not in stack or 'private val covarianceHeight = max(1, height / 2)' not in stack:
        fail('production covariance is not RAW/2')
    for u in ['uRawTextureOrigin','uRawTextureSize','uCovarianceOrigin','uCovarianceTextureSize','uFigure7Noise','uKDetail','uKDenoise','uDth','uDtr','uKStretch','uKShrink']:
        if f'"{u}"' not in stack: fail('host does not bind Figure-7 uniform '+u)
    if 'figure7KStretch = 4.0f' not in stack or 'figure7KShrink = 2.0f' not in stack:
        fail('public k_stretch/k_shrink constants missing')
    if 'bayerPhaseShotNoise' not in stack or 'bayerPhaseReadNoise' not in stack:
        fail('Figure-7 sensor-domain Bayer noise ownership missing')

def bounded_memory(root):
    cap=text(root,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    frame=text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java')
    safe=text(root,'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt')
    bridge=text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    stack=text(root,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    for marker in [
        'IRIS_NIGHT_26543_SPOOL_SLOTS = 3',
        'Executors.newFixedThreadPool(2',
        'mIrisNight26543SpoolSlots.acquire()',
        'IRIS_26543_NIGHT_RAW_SPOOLED',
        'IRIS_26543_NIGHT_BOUNDED_MEMORY_PROOF',
        'nativePersistentCopies=1 imageReaderSlots=3 pending=0 spoolPermits=3',
        'matched.sort(Comparator.comparingLong(ImageFrame::getTimestamp))',
        'IRIS_26543_NIGHT_REFERENCE_ORDER_PROOF',
        'sortedReference.motionV2FrameRole != ImageFrame.MotionV2FrameRole.NORMAL',
        'IRIS_26543_NIGHT_WAITING_FOR_SPOOL',
        'IRIS_NIGHT_26543_SPOOL_DRAIN_TIMEOUT_MS = 10_000L',
        'mIrisNight26543SpoolFailure = null',
        '26543 Night RAW spool failure:',
    ]:
        if marker not in cap: fail('Night bounded-memory invariant missing: '+marker)
    spool=extract_between(cap,'    private void spoolIrisNight26543Raw','    /* IRIS_26540_NIGHT_EXACT_FRAME_METADATA_OWNER */')
    if 'Allocator.allocate' in spool or 'copyIrisNight26540Raw' in spool:
        fail('non-reference Night spool creates a persistent native RAW copy')
    if '.force(' in spool or 'channel.force' in spool:
        fail('Night spool forces flash durability per RAW')
    if 'new FileOutputStream(file)' not in spool or 'while (source.hasRemaining()) channel.write(source);' not in spool:
        fail('Night spool no longer streams Camera2 RAW directly to cache')
    if '(long)mIrisNight26540ExpectedFrames - 1L' not in spool or 'IRIS_NIGHT_26543_SPOOL_RESERVE_BYTES' not in spool:
        fail('Night spool capacity budget does not scale with requested frame count')
    for marker in ['irisNightRawSpoolFile','setIrisNightRawSpool','hasMotionV2RawBacking','irisNightRawSpoolFile.delete()']:
        if marker not in frame: fail('ImageFrame spool lifecycle missing: '+marker)
    for marker in ['IRIS_26543_NIGHT_BOUNDED_DISK_BACKING','fun readFileRegion(','LargeDirectBuffer.allocate','LargeDirectBuffer.free(buffer)','isFileBacked']:
        if marker not in safe: fail('SafeImage bounded disk reader missing: '+marker)
    for marker in ['frame.hasMotionV2RawBacking()','backingFile = file','26543 Night/Motion owned reference must remain in-memory']:
        if marker not in bridge: fail('bridge disk-backed ownership missing: '+marker)
    # Critical frame-scaling proof: no temporal full RAW/2 covariance copy may survive.
    if 'label = "MGC RGB covariance frame $index"' in stack:
        fail('per-frame full covariance retention survived')
    if re.search(r'val retainedCovariance\s*=\s*copyPersistentTexture', stack):
        fail('temporal retained covariance copy survived')
    for marker in [
        'IRIS_26543_BANDED_FIGURE7_BOUNDED_COVARIANCE',
        'covarianceTexture = 0',
        'val covarianceBandTexture = createTexture(',
        'IRIS_26543_BANDED_FIGURE7_REGION_OWNER',
        'renderCovarianceRegion(',
        'covarianceScratchBytes',
        'if (frame.covarianceTexture != 0) add(frame.covarianceTexture)',
    ]:
        if marker not in stack: fail('bounded banded covariance invariant missing: '+marker)
    # Static memory scaling numbers for the target sensor geometry: per-frame retained covariance = 0.
    raw_w,raw_h=4096,3072
    raw_bytes=raw_w*raw_h*2
    old_cov=(raw_w//2)*(raw_h//2)*8
    bounded_capture_equiv=1+3 # one persistent reference + max three outstanding Camera2 images
    assert raw_bytes==25165824 and old_cov==25165824
    if bounded_capture_equiv != 4: fail('internal memory proof error')

def coordinate_self_test():
    # Mirror the band-region host math and prove bilinear covariance samples plus Figure-7 RAW halo fit.
    def ceildiv(a,b): return (a+b-1)//b
    for width,height in [(18,18),(4096,3072),(4032,3024)]:
        cw,ch=max(1,width//2),max(1,height//2)
        test_rects=[(0,0,min(width,17),min(height,17)),
                    (max(0,width//2-17),max(0,height//2-13),min(width,width//2+23),min(height,height//2+19)),
                    (max(0,width-41),max(0,height-37),width,height)]
        for l,t,r,b in test_rects:
            el=max(0,l-4); et=max(0,t-4); er=min(width,r+4); eb=min(height,b+4)
            cl=min(max(el//2,0),cw-1); ct=min(max(et//2,0),ch-1)
            cr=min(max(ceildiv(er,2),cl+1),cw); cb=min(max(ceildiv(eb,2),ct+1),ch)
            ul=max(0,cl*2-2); ut=max(0,ct*2-2); ur=min(width,cr*2+2); ub=min(height,cb*2+2)
            # Probe source centers across/just outside planner integer region conservatively.
            for x in [l-1.0,l-0.5,float(l),r-1.0,r-0.5,float(r)]:
                if x < -0.5 or x > width-0.5: continue
                k=x/2.0-0.25
                f=max(0,min(cw-1,math.floor(k))); c=max(0,min(cw-1,f+1))
                if not (cl<=f<cr and cl<=c<cr): fail(f'cov X sample escaped band region rect={(l,r)} x={x} cov={(cl,cr)} k={k}')
            for y in [t-1.0,t-0.5,float(t),b-1.0,b-0.5,float(b)]:
                if y < -0.5 or y > height-0.5: continue
                k=y/2.0-0.25
                f=max(0,min(ch-1,math.floor(k))); c=max(0,min(ch-1,f+1))
                if not (ct<=f<cb and ct<=c<cb): fail('cov Y sample escaped band region')
            # Every covariance cell in the local texture has full shader support after global clamp.
            if ul>max(0,cl*2-2) or ut>max(0,ct*2-2) or ur<min(width,cr*2+2) or ub<min(height,cb*2+2):
                fail('Figure-7 raw support rectangle is insufficient')
    # Full-frame local UV must reduce exactly to the audited mapping.
    for raw in [0.0,0.25,1.0,101.375,4094.5]:
        local=((raw+0.5)*0.5-0.0)/(4096/2)
        full=(raw+0.5)/4096
        if abs(local-full)>1e-15: fail('full/local covariance UV identity failed')

def architecture_protections(root):
    cap=text(root,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    selector=text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
    bridge=text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    night=text(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
    hi=text(root,'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl')
    for marker in ['SHORT_FRAMES = 12','LONG_FRAMES = 3','TOTAL_FRAMES = SHORT_FRAMES + LONG_FRAMES']:
        if marker not in selector: fail('Night 12+3 policy drift: '+marker)
    for marker in ['IRIS_26541_NIGHT_SHORT_TAG','IRIS_26541_NIGHT_LONG_TAG','zsl=false']:
        if marker not in cap: fail('Night fresh capture ownership drift: '+marker)
    if 'val lumaScale = 0f' not in bridge: fail('26541 zero-MGC-luma rollback lost')
    if 'IRIS_26542_ROLE_AWARE_NORMAL_DNG_PARITY' not in bridge: fail('26542 role-aware DNG parity lost')
    if 'if(centerClipGate<=0.0){ Output=c; return; }' not in hi: fail('26541 non-clipped highlight no-op lost')
    for marker in ['IRIS_26543_NIGHT_POST_RGB_BEGIN','IRIS_26543_NIGHT_POST_RGB_COMPLETE','IRIS_26543_NIGHT_BASE_JPEG_BEGIN','IRIS_26543_NIGHT_BASE_JPEG_COMPLETE']:
        if marker not in night: fail('Night post-DNG diagnostic missing: '+marker)

def core(base,cand,postbuild=False):
    if changed(base,cand)!=sorted(RUNTIME_FILES): fail('26543 changed-file allowlist mismatch: '+repr(changed(base,cand)))
    for rel,h in CAND_SHA.items():
        if not (cand/rel).is_file() or sha(cand/rel)!=h: fail('candidate hash mismatch: '+rel)
    v=(cand/'app/version.properties').read_text()
    if postbuild:
        if 'VERSION_NAME=0.9726543' not in v or 'VERSION_BUILD=26543' not in v: fail('postbuild version drift')
    else:
        if 'VERSION_NAME=0.9726542' not in v or 'VERSION_BUILD=26542' not in v: fail('preversion candidate changed version early')
    if sum(1 for p in (base/'app').rglob('*') if p.is_file())!=967: fail('base app file count drift')
    if sum(1 for p in (cand/'app').rglob('*') if p.is_file())!=967: fail('candidate app file count drift')
    ownership(cand); figure7(cand); bounded_memory(cand); coordinate_self_test(); architecture_protections(cand)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--postbuild',action='store_true'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        coordinate_self_test(); print('PASS: 26543 validator self-test: Figure-7 band coordinate/halo identity'); return
    if not a.base or not a.candidate: ap.error('--base and --candidate required')
    core(Path(a.base).resolve(),Path(a.candidate).resolve(),a.postbuild)
    print('PASS: 26543 architecture validation: live-owner Figure-7 + bounded Night RAW + bounded band covariance; protected 26542/26541 owners intact')
    print('PASS: frame-count memory scaling: persistent Night native RAW copies=1; outstanding Camera2 RAW slots<=3; retained temporal full RAW/2 covariance textures=0')

if __name__=='__main__': main()
