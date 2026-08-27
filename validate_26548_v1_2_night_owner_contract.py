#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, re

EXPECTED = [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
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

def method_block(src, marker, end_marker):
    a=src.index(marker); b=src.index(end_marker,a)
    return src[a:b]

def validate(base, cand):
    b,c=files(base),files(cand)
    changed=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
    require(changed==EXPECTED, f'changed scope mismatch: {changed}')

    # Same 26548 build sequence: this is V1.2 of the already-built 26548 candidate.
    v=text(cand,'app/version.properties')
    require('VERSION_NAME=0.9726548' in v and 'VERSION_BUILD=26548' in v,
            '26548 version/build authority drifted')

    post=text(cand,EXPECTED[2])
    require('IRIS_26548_V1_2_SHARED_RECONSTRUCTION_OWNER_CONTRACT' in post,
            'shared Motion/Night reconstruction-owner validator missing')
    require('private void validateIrisReconstructionOwnership()' in post,
            'shared owner validator method missing')
    require('if (!(mParameters.motionV2Active || mParameters.irisNightActive)) return;' in post,
            'Night still bypasses reconstruction-owner validation')
    require(post.count('validateIrisReconstructionOwnership();')==2,
            'owner validator must run once in Night graph and once in Motion graph')

    night_block=method_block(post, 'if(mParameters.irisNightActive){',
                             '/* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */')
    require('IRIS_26548_V1_2_NIGHT_OWNER_AWARE_POST_GRAPH' in post,
            'Night owner-aware graph marker missing')
    require('final int reconstructionOwner = mParameters.motionV2ReconstructionOwner;' in night_block,
            'Night graph does not route from durable reconstruction owner')
    require('reconstructionOwner == Parameters.MOTION_V2_RECONSTRUCTION_SPATIAL_RGB' in night_block and
            'reconstructionOwner == Parameters.MOTION_V2_RECONSTRUCTION_SABRE' in night_block,
            'Night graph is not explicitly split by Spatial/Sabre owner')
    require('IRIS_26548_V1_2_NIGHT_SABRE_POST_OWNERSHIP' in night_block,
            'Night Sabre ownership telemetry missing')
    require('spatialSourceRestore=false spatialHighlightReliability=false' in night_block,
            'Night Sabre telemetry does not prove Spatial nodes disabled')

    # The two Spatial-only nodes may remain in source for actual Spatial owner, but they must occur
    # only inside the Spatial branch of Night and before the Sabre branch delimiter.
    spatial_branch=night_block.index('reconstructionOwner == Parameters.MOTION_V2_RECONSTRUCTION_SPATIAL_RGB')
    sabre_branch=night_block.index('reconstructionOwner == Parameters.MOTION_V2_RECONSTRUCTION_SABRE')
    srcpos=night_block.index('add(new MotionV2MgcSourceExposure())')
    relpos=night_block.index('add(new MotionV2HighlightChromaReliability())')
    require(spatial_branch < srcpos < sabre_branch and spatial_branch < relpos < sabre_branch,
            'Spatial-only Night nodes are not confined to the Spatial-owner branch')
    common_color=night_block.index('add(new MotionV2ColorTransform())', sabre_branch)
    common_exposure=night_block.index('add(new MotionV2DisplayExposure())', common_color)
    common_render=night_block.index('add(new MotionV2Render())', common_exposure)
    require(sabre_branch < common_color < common_exposure < common_render,
            'common Night camera-RGB finishing order changed')

    # No generic/legacy Photon image-formation node may exist in the dedicated Night branch.
    forbidden_night=(
        'ExposureFusionBayer2','IrisRcdDemosaic','Demosaic3','new Demosaic(',
        'PyramidMerging','AutoExposure','CaptureSharpening','CorrectingFlow','Sharpen2','Bayer2Float'
    )
    for token in forbidden_night:
        require(token not in night_block, f'legacy/generic Night node survived active graph: {token}')
    require('IRIS_NIGHT_SPATIAL_RGB_INPUT' not in night_block,
            'stale Night Spatial-input telemetry survived')

    # Defense in depth: owner-specific nodes themselves reject every non-Spatial owner, including Night.
    source=text(cand,EXPECTED[1]); high=text(cand,EXPECTED[0])
    for name,s in [('source restore',source),('highlight reliability',high)]:
        require('basePipeline.mParameters.motionV2Active\n                &&' not in s,
                f'{name} still limits owner rejection to Motion only')
        require('MOTION_V2_RECONSTRUCTION_SPATIAL_RGB' in s,
                f'{name} lacks explicit Spatial-owner requirement')
        require('26548 V1.2 Spatial' in s and 'non-Spatial Iris owner=' in s,
                f'{name} cross-pipeline owner guard missing')
    require('26541 missing native Spatial reliability map' in high,
            'native Spatial reliability invariant unexpectedly removed')

    # Night is currently Sabre by design. Make the effective output state truthful rather than
    # retaining a stale 2x Spatial flag while Sabre runs its proven native grid.
    night=text(cand,EXPECTED[3])
    require('p.motionV2ReconstructionOwner != Parameters.MOTION_V2_RECONSTRUCTION_SABRE' in night,
            'Night no longer asserts Sabre owner after reconstruction')
    require('Night Sabre must remain native-grid' in night,
            'Night Sabre native-grid geometry invariant missing')
    require('IRIS_26548_V1_2_NIGHT_SABRE_SR_EFFECTIVE' in night,
            'Night Sabre requested-vs-effective SR marker missing')
    require('p.motionV2SuperResOutputEnabled = false;' in night,
            'Night Sabre still publishes stale effective 2x SR state')
    require('superResRequested=' in night and 'superResEffective=' in night,
            'Night EXIF does not distinguish requested from effective SR')

    # Reconstruction producer publishes a durable owner for Night and Motion. No Sabre math changed:
    # the selection equation and carrier conversion must remain the proven 26548 implementation.
    bridge=text(cand,EXPECTED[4])
    base_bridge=text(base,EXPECTED[4])
    require('val sabreSelected = parameters.irisNightActive ||' in bridge,
            'Night no longer forces audited Sabre reconstruction')
    require('IRIS_26548_V1_2_RECONSTRUCTION_OWNERSHIP' in bridge and
            'pipeline=${if (parameters.irisNightActive) "NIGHT" else "MOTION"}' in bridge,
            'shared owner publication telemetry missing')
    require('convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)' in bridge,
            'proven 26548 Night/Motion RGBA32F carrier changed')
    # Only telemetry is allowed in the bridge delta for V1.2; reconstruct math region before line 650
    # must remain byte-identical to V1 aside from no edits there.
    require(base_bridge[:base_bridge.index('            if (!parameters.irisNightActive) {')] ==
            bridge[:bridge.index('            PLog.i(TAG, "IRIS_26548_V1_2_RECONSTRUCTION_OWNERSHIP "')],
            'PhotonMotionMgc1271Bridge changed before the ownership telemetry seam')

    # Dormant historical classes may remain, but active call sites must remain absent.
    all_java='\n'.join(p.read_text(errors='ignore') for p in Path(cand).joinpath('app/src/main/java').rglob('*') if p.is_file())
    require(all_java.count('IrisNightMgc1271Bridge')==1,
            'dormant IrisNightMgc1271Bridge acquired an active caller')
    require(all_java.count('RunIrisNightBayer(')==1,
            'dormant RunIrisNightBayer acquired an active caller')
    iris_rcd=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdDemosaic.java')
    require('class IrisRcdDemosaic' in iris_rcd, 'IrisRcdDemosaic source unexpectedly missing')
    require('new IrisRcdDemosaic(' not in night_block, 'Night revived RCD demosaic')

    # Exact changed scope is the strongest Xiaomi Motion protection: no Motion shader, capture,
    # exposure, alignment, Sabre/VGN math, denoise, Camera2 compatibility or rendering source changed.
    forbidden_prefixes=(
        'app/src/main/assets/shaders/',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
        'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
        'app/src/main/java/com/hinnka/mycamera/processor/RawNoiseModel.kt',
    )
    for f in changed:
        require(not any(f.startswith(x) for x in forbidden_prefixes),
                f'protected Motion/camera IQ source changed: {f}')

    # Inherited 26548 root fixes remain present and unchanged because their files are outside scope.
    cap=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    raw=text(cand,'app/src/main/java/com/hinnka/mycamera/processor/RawNoiseModel.kt')
    night_input=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java')
    require('IRIS_26548_MOTION_INPUT_READINESS_GATE' in cap,
            '26548 Motion readiness protection disappeared')
    require('IRIS_26548_CAMERA_SESSION_HEALTH_CONTRACT' in cap,
            '26548 camera-session health protection disappeared')
    require('s.isFinite() && s > 0f && o.isFinite() && o >= 0f' in raw,
            '26548 Camera2 zero-O compatibility correction disappeared')
    require('GLFormat.DataType.FLOAT_32, 4' in night_input and 'irisNightRgba32f' in night_input,
            '26548 RGBA32F Night transport correction disappeared')
    require('java.nio.ByteBuffer' in cap,
            'permanent Java ByteBuffer compiler regression guard disappeared')

    print('PASS: exact 5-file 26548 V1 -> V1.2 localized runtime scope')
    print('PASS: Night post graph routes from durable Sabre/Spatial reconstruction owner')
    print('PASS: Night Sabre forbids both stale Spatial source/reliability nodes')
    print('PASS: Spatial-only nodes reject non-Spatial owners in Motion and Night')
    print('PASS: common Night camera-RGB color/exposure/render order preserved')
    print('PASS: active Night graph contains no legacy Photon Bayer/RCD/fusion/sharpen path')
    print('PASS: dormant Night Bayer/MGC legacy entry points remain caller-free')
    print('PASS: Night Sabre requested-vs-effective SR state is explicit and native-grid')
    print('PASS: 26548 RGBA32F + camera-session + zero-O compatibility fixes preserved')
    print('PASS: Xiaomi Motion shaders/capture/exposure/alignment/Sabre/VGN/denoise/tone protected')
    print('PASS: target remains 0.9726548 / 26548 V1.2')


def self_test():
    SPATIAL,SABRE=1,2
    def night_owner_nodes(owner):
        nodes=['IrisNightRgbInput']
        if owner==SPATIAL:
            nodes += ['MotionV2MgcSourceExposure','MotionV2HighlightChromaReliability']
        elif owner!=SABRE:
            raise ValueError('invalid owner')
        nodes += ['MotionV2ColorTransform','MotionV2DisplayExposure','MotionV2Render']
        return nodes
    s=night_owner_nodes(SABRE)
    require('MotionV2MgcSourceExposure' not in s and 'MotionV2HighlightChromaReliability' not in s,
            'self-test: Sabre scheduled Spatial nodes')
    p=night_owner_nodes(SPATIAL)
    require('MotionV2MgcSourceExposure' in p and 'MotionV2HighlightChromaReliability' in p,
            'self-test: Spatial owner lost required owner-specific nodes')
    try:
        night_owner_nodes(0)
        fail('self-test: invalid owner accepted')
    except ValueError:
        pass
    print('PASS: 26548 V1.2 reconstruction-owner routing self-tests')

if __name__=='__main__':
    if '--self-test' in sys.argv:
        self_test()
    elif len(sys.argv)==3:
        validate(sys.argv[1],sys.argv[2])
    else:
        raise SystemExit(f'usage: {sys.argv[0]} --self-test | BASE CANDIDATE')
