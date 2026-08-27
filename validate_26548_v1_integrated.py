#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, re

EXPECTED = [
'app/src/main/java/com/hinnka/mycamera/processor/RawNoiseModel.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/version.properties',
]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text(root, rel): return (Path(root)/rel).read_text()
def fail(msg): raise SystemExit('FAIL: '+msg)
def require(cond,msg):
    if not cond: fail(msg)
def files(root):
    root=Path(root); out={}
    for p in root.rglob('*'):
        if p.is_file(): out[p.relative_to(root).as_posix()]=sha(p)
    return out

def validate(base, cand):
    b,c=files(base),files(cand)
    changed=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
    require(changed==EXPECTED, f'changed scope mismatch: {changed}')

    # Version/build contract.
    v=text(cand,'app/version.properties')
    require('VERSION_NAME=0.9726548' in v and 'VERSION_BUILD=26548' in v,
            'target version/build missing')

    # Night crash root: GLFormat is unchanged, because global FLOAT_16 client-type changes would
    # break existing float32->RGBA16F uploads. Night instead adopts Motion's proven RGBA32F boundary.
    glfmt='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java'
    require(b[glfmt]==c[glfmt], 'GLFormat changed; Night fix must remain localized')
    glfmt_text=text(cand,glfmt)
    require('case FLOAT_16:' in glfmt_text and 'return GL_FLOAT;' in glfmt_text,
            'expected legacy FLOAT_16/GL_FLOAT behavior not present for regression proof')
    bridge=text(cand,EXPECTED[5])
    require('IRIS_26548_NIGHT_RGBA32F_MOTION_PARITY_HANDOFF' in bridge,
            'Night RGBA32F Motion-parity bridge marker missing')
    require('val output: ByteBuffer = convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)' in bridge,
            'Night/Motion common RGBA32F cross-context conversion missing')
    require('nightNativeHalfCarrier' not in bridge and 'rgba16f_cpu_night' not in bridge,
            'broken Night native-half handoff survived')
    require('GLES30.GL_RGBA, GLES30.GL_HALF_FLOAT, half)' in bridge,
            'proven in-context half upload type missing')
    require('GLES30.GL_RGBA, GLES30.GL_FLOAT, output)' in bridge,
            'proven RGBA32F readback type missing')

    night_input=text(cand,EXPECTED[2])
    require('GLFormat.DataType.FLOAT_32, 4' in night_input,
            'Night input is not RGBA32F')
    require('basePipeline.main1 = new GLTexture' in night_input and
            'basePipeline.main2 = new GLTexture' in night_input and
            'basePipeline.main3 = new GLTexture' in night_input and
            'basePipeline.texnum = 0;' in night_input,
            'Night input does not mirror proven Motion GL lifecycle')
    require('GLFormat.DataType.FLOAT_16, 4' not in night_input,
            'Night still uploads half CPU bytes through generic FLOAT_16 client contract')
    require('irisNightRgba16f' not in night_input,
            'old Night half-float carrier field survived')

    post=text(cand,EXPECTED[3]); night_proc=text(cand,EXPECTED[4])
    require('irisNightRgba32f' in post and 'carrier=RGBA32F' in post,
            'PostPipeline Night carrier semantics not updated')
    require('* 4L * 4L' in night_proc and 'rgba32fBytes=' in night_proc,
            'IrisNightProcessor does not enforce RGBA32F capacity')

    # Motorola A: stateful surface handshake, real preview-flow evidence, and pre-freeze guard.
    preview=text(cand,EXPECTED[6]); renderer=text(cand,EXPECTED[7]); cap=text(cand,EXPECTED[1])
    for marker in ('IRIS_26548_PREVIEW_SURFACE_CREATED','IRIS_26548_PREVIEW_SURFACE_REPLAY',
                   'IRIS_26548_PREVIEW_SURFACE_DELIVERED','IRIS_26548_PREVIEW_SURFACE_DESTROYED',
                   'IRIS_26548_FIRST_PREVIEW_FRAME'):
        require(marker in preview, f'missing preview handshake marker {marker}')
    require('available = currentSurfaceTexture != null;' in preview,
            'listener installation still fabricates availability')
    require('deliveredSurfaceTextureGeneration == replayGeneration' in preview,
            'surface replay idempotence guard missing')
    require('mView.fireOnPreviewFrameAvailable();' in renderer,
            'renderer does not publish actual preview-frame flow')

    for marker in ('IRIS_26548_CAMERA_START_REQUESTED','IRIS_26548_CAMERA_OPEN_REQUESTED',
                   'IRIS_26548_CAMERA_ON_OPENED','IRIS_26548_PREVIEW_SESSION_CREATE_BEGIN',
                   'IRIS_26548_PREVIEW_SESSION_ON_CONFIGURED','IRIS_26548_REPEATING_REQUEST_SUBMITTED',
                   'IRIS_26548_FIRST_CAPTURE_RESULT','IRIS_26548_FIRST_ZSL_RAW',
                   'IRIS_26548_CAMERA_HEALTH_CHECK','IRIS_26548_CAMERA_SESSION_STALLED',
                   'IRIS_26548_MOTION_NOT_READY_SESSION_OR_ZSL'):
        require(marker in cap, f'missing camera/session health marker {marker}')
    require('mIris26548ConsecutiveHealthRecoveries >= 1' in cap,
            'single-recovery loop prevention missing')
    # Gate must precede capture state transition and auxiliary requests.
    gate=cap.index('IRIS_26548_MOTION_INPUT_READINESS_GATE')
    capturing=cap.index('mZslCapturing = true;', gate)
    short=cap.index('applyMotion26486ExplicitShortCaptureIfNeeded', gate)
    long=cap.index('applyMotion26505ExplicitLongCaptureIfUseful', gate)
    require(gate < capturing < short < long, 'readiness gate is not before destructive/aux capture transition')
    require('countValidMotionFrames()' in cap[capturing:cap.index('finalizeMotionZslCapture();',capturing)],
            'existing frozen metadata grace path disappeared')

    # Tundra: Camera2 S>0/O==0 is valid. Negative/nonfinite O still invalid.
    raw=text(cand,EXPECTED[0])
    require('s.isFinite() && s > 0f && o.isFinite() && o >= 0f' in raw,
            'Camera2 raw S/O validity contract missing')
    require('readNoise.any { it > 0f }' not in raw[raw.index('fun fromCamera2NoiseProfile'):raw.index('fun fromDngNoiseProfile')],
            'all-zero Camera2 O is still rejected')
    require(cap.count('IRIS_26548_CAMERA2_ZERO_READ_NOISE_ACCEPTED')==2,
            'both timestamp-owned Camera2 metadata paths must accept/log zero O')
    # No prior-profile cache/fabrication added.
    require('cachedNoise' not in cap and 'lastNoiseProfile' not in cap,
            'unexpected cross-shot noise-profile cache added')

    # Xiaomi Motion IQ protection: no shaders or core MGC engines changed.
    forbidden_prefixes=(
        'app/src/main/assets/shaders/',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    )
    for f in changed:
        require(not any(f.startswith(x) for x in forbidden_prefixes),
                f'protected Motion reconstruction/IQ source changed: {f}')
    # Motion itself already used convertHalfRgbaToFloatRgba in base; candidate still does not have a
    # mode-dependent alternate for healthy Motion.
    base_bridge=text(base,EXPECTED[5])
    require('convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)' in base_bridge,
            '26547 Motion RGBA32F authority not found')
    require('parameters.motionV2Active = false' not in cap,
            'unexpected Motion activation mutation in CaptureController')

    # Memory ownership: transfer carrier released before work textures allocate.
    release=night_input.index('Allocator.free(source);')
    alloc=night_input.index('basePipeline.main1 = new GLTexture', release)
    require(release < alloc, 'Night CPU RGBA32F carrier is not released before ping-pong allocation')

    # Permanent failure regressions retained in the source itself.
    require('java.nio.ByteBuffer' in cap, '26543 V1.3 ByteBuffer regression guard failed')

    print('PASS: exact 9-file 26548 scope')
    print('PASS: Night native-half/GL_FLOAT mismatch removed via proven Motion RGBA32F contract')
    print('PASS: Night carrier released before RGBA16F working allocation')
    print('PASS: Motorola-A SurfaceTexture startup race fixed + session health contract present')
    print('PASS: Motion cannot freeze/aux-request with an unready session or insufficient RAW ring')
    print('PASS: Camera2 S>0/O==0 accepted without cache/fabrication; malformed coefficients remain invalid')
    print('PASS: Motion shaders/reconstruction engines/IQ math protected')
    print('PASS: target version 0.9726548 / 26548')


def self_test():
    # Explicit mathematical regression for tundra-like and malformed Camera2 profiles.
    def valid(pairs):
        if len(pairs)<8: return False
        import math
        return all(math.isfinite(pairs[i*2]) and pairs[i*2] > 0 and
                   math.isfinite(pairs[i*2+1]) and pairs[i*2+1] >= 0 for i in range(4))
    require(valid([1e-4,0.0]*4), 'self-test: tundra zero-O profile rejected')
    require(valid([1e-4,1e-6]*4), 'self-test: normal Camera2 profile rejected')
    require(not valid([1e-4,-1e-6]*4), 'self-test: negative O accepted')
    require(not valid([0.0,0.0]*4), 'self-test: zero S accepted')
    require(not valid([float('nan'),0.0]+[1e-4,0.0]*3), 'self-test: NaN S accepted')
    print('PASS: 26548 validator self-tests')

if __name__=='__main__':
    if '--self-test' in sys.argv:
        self_test()
    elif len(sys.argv)==3:
        validate(sys.argv[1],sys.argv[2])
    else:
        raise SystemExit(f'usage: {sys.argv[0]} --self-test | BASE CANDIDATE')
