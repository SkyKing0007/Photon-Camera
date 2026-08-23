#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, re, subprocess, tempfile
from pathlib import Path

EXPECTED_CHANGED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def die(msg): raise SystemExit('FAIL: '+msg)
def need(text, token, label):
    if token not in text: die(f'{label}: missing {token}')
def forbid(text, token, label):
    if token in text: die(f'{label}: forbidden {token}')
def extract_shader(text,name):
    m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    if not m: die('cannot extract shader '+name)
    return m.group(1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--candidate',required=True); ap.add_argument('--patch'); ap.add_argument('--rollback'); ap.add_argument('--json-out'); ap.add_argument('--postbuild',action='store_true'); a=ap.parse_args()
    b=Path(a.base); c=Path(a.candidate)
    if not b.is_dir() or not c.is_dir(): die('base/candidate missing')
    cp=subprocess.run(['diff','-qr',str(b/'app/src/main'),str(c/'app/src/main')],text=True,stdout=subprocess.PIPE)
    changed=set()
    for line in cp.stdout.splitlines():
        m=re.search(r'(app/src/main/[^ ]+)',line)
        if m: changed.add(m.group(1))
    if changed!=EXPECTED_CHANGED: die(f'changed runtime set mismatch: {sorted(changed)}')

    shaders=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
    base_shaders=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
    if extract_shader(shaders,'mergeRgb') != extract_shader(base_shaders,'mergeRgb'): die('legacy mergeRgb changed below 8x')
    if extract_shader(shaders,'normalizeRgb16') != extract_shader(base_shaders,'normalizeRgb16'): die('legacy normalizeRgb16 changed below 8x')
    for tok in ['IRIS_26530_MOTION_SAFE_RAW_SUPERRES','mergeRgbSuperRes','uReconstructionZoom','uLumaTemporalScale','IRIS_26530_SUPERRES_LSC_SENSOR_COORDINATE','normalizeRgb16SuperRes']:
        need(shaders,tok,'shaders')
    need(shaders,'semanticSums.r * lumaFrameWeight','green/luma-only temporal scaling')
    need(shaders,'semanticSums.g * frameWeight','full R-G chroma temporal support')
    need(shaders,'semanticSums.b * frameWeight','full B-G chroma temporal support')
    forbid(shaders,'semanticSums.g * lumaFrameWeight','independent chroma weakening')
    need(shaders,'referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0)','SR shared sensor geometry')
    need(shaders,'vec2 uv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);','SR lens shading sensor coordinate')

    stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()
    for tok in ['IRIS_26530_LOW_ZOOM_LEGACY_SHADER_ISOLATION','displayedGlobalZoom >= 8f','reconstructionZoom > 1.0001f','iris26530TargetEffectiveLumaFrames','iris26530AuxiliaryLumaScale','if (frame.imageIndex == 0) 1f else iris26530LumaAuxScale','motionGate=existingSpatialRejection']:
        need(stack,tok,'stacker')
    need(stack,'if (globalZoom <= 50f) return 7f','7-frame tuned-GCam calibration')
    need(stack,'return 7f + 2f * (t * t * (3f - 2f * t))','smooth 7-to-9 >50x curve')
    need(stack,'val neff = sum * sum / sumSquares','effective-stack equation')
    need(stack,'reconstructionZoom = if (iris26530SuperResEnabled) reconstructionZoom else 1f','tile/shader geometry gating')

    planner=(c/'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt').read_text()
    for tok in ['IRIS_26530_SR_TILE_SHADER_GEOMETRY_PARITY','rawCenter + (fullRaw - rawCenter) / reconstructionZoom','reconstructionZoom: Float = 1f']:
        need(planner,tok,'tile planner')

    bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    for tok in ['displayedGlobalZoom >= 8f','minOf(2f, localOutputZoom)','parameters.motionV2SpatialReconstructionZoom = spatialReconstructionZoom','motionAuthority=existingSpatialRejection','cfaGeometry=sharedGreenOpponent']:
        need(bridge,tok,'bridge')

    params=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
    need(params,'motionV2SpatialReconstructionZoom = 1.0f','parameters')
    render=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
    need(render,'motionV2OutputZoom / spatialReconstructionZoom','JPEG/UHDR residual zoom')
    image_saver=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
    need(image_saver,'dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);','DNG full zoom authority')
    if image_saver != (b/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text(): die('ImageSaver/DNG runtime changed')
    hdr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    if hdr != (b/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text(): die('HdrxProcessor capture/zoom authority changed')
    fusion=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
    need(fusion,'GlesIris26521SpatialRgbStacker(','active Iris owner')
    # Do not introduce any new references to old/fallback owners. Historical comments may remain.
    base_bridge=(b/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    for tok in ['PyramidAlignment','Wronski','Sabre','single-frame fallback','ADRC']:
        if bridge.count(tok) != base_bridge.count(tok): die(f'bridge old-path reference count changed for {tok}')

    # Numeric proof of target curve and 15->7 auxiliary scale.
    def beta(n,t):
        if n<=1 or t>=n:return 1.0
        lo,hi=0.0,1.0
        for _ in range(80):
            x=(lo+hi)/2; m=n-1; ne=(1+m*x)**2/(1+m*x*x)
            if ne<t: lo=x
            else: hi=x
        return (lo+hi)/2
    b15=beta(15,7)
    ne=(1+14*b15)**2/(1+14*b15*b15)
    if abs(ne-7)>1e-5 or not (0.1427<b15<0.1430): die(f'15->7 calibration math wrong beta={b15} neff={ne}')

    # Chroma postprocessor must remain byte-identical to predecessor.
    post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    if sha(c/post)!=sha(b/post): die('26529 directional chroma postprocessor changed')

    report={'status':'PASS','changed_files':sorted(changed),'low_zoom_legacy_shader_unchanged':True,'sr_threshold_displayed_x':8.0,'sr_raw_cap':2.0,'luma_target_8_to_50':7.0,'luma_target_120_plus':9.0,'fifteen_frame_aux_luma_scale':b15,'motion_gate':'existing Spatial rejection','chroma_temporal_support':'full','dng_default_crop':'unchanged motionV2OutputZoom','postbuild':a.postbuild}
    if a.json_out: Path(a.json_out).write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 26530 independent validation')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
