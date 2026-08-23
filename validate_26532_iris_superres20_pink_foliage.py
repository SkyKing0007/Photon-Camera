#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re, sys

ALLOWED = [x.strip() for x in '''
app/src/main/cpp/CMakeLists.txt
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt
app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt
app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java
app/src/main/java/com/particlesdevs/photoncamera/settings/SettingType.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java
app/src/main/res/values/ids.xml
app/src/main/res/values/strings.xml
'''.splitlines() if x.strip()]
NEW = 'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def files(root):
    root=Path(root)
    return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
def need(text, token, label, count=None):
    c=text.count(token)
    if c < 1: raise RuntimeError(f'missing {label}: {token}')
    if count is not None and c != count: raise RuntimeError(f'{label} count={c} expected={count}')
def forbid(text, token, label):
    if token in text: raise RuntimeError(f'forbidden {label}: {token}')
def read(root, rel): return (Path(root)/rel).read_text(encoding='utf-8')

def patch_scope(path):
    names=[]
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.startswith('diff --git a/'):
            m=re.match(r'diff --git a/(.+?) b/(.+)$',line)
            if not m or m.group(1)!=m.group(2): raise RuntimeError('invalid patch header '+line)
            names.append(m.group(1))
    return names

def geometry_tests():
    rows=[]
    for anchor in (1.0,3.0,4.1):
        for total in (1.0,2.0,5.0,10.0,20.0,30.0):
            if total < anchor: continue
            local=total/anchor; sr_total=min(total,20.0)
            recon=max(1.0,min(local,sr_total/anchor)) if local>1.0001 else 1.0
            residual=max(1.0,local/recon)
            if abs(recon*residual-local)>1e-6*max(1.0,local): raise RuntimeError('geometry identity')
            normal=anchor*local; sr=anchor*recon*residual
            if abs(normal-total)>1e-6 or abs(sr-total)>1e-6: raise RuntimeError('DNG/JPEG FOV parity')
            rows.append({'anchor':anchor,'total':total,'local':local,'recon':recon,'residual':residual})
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--candidate',required=True); ap.add_argument('--patch',required=True); ap.add_argument('--rollback',required=True); ap.add_argument('--json-out'); ap.add_argument('--versioned',action='store_true')
    a=ap.parse_args(); base=Path(a.base); cand=Path(a.candidate)
    bf,cf=files(base),files(cand)
    changed=sorted(k for k in set(bf)|set(cf) if bf.get(k)!=cf.get(k))
    expected_scope=sorted(ALLOWED + (['app/version.properties'] if a.versioned else []))
    if changed!=expected_scope: raise RuntimeError('candidate scope mismatch: '+repr(changed))
    if NEW in bf or NEW not in cf: raise RuntimeError('new DNG writer ownership invalid')
    if patch_scope(a.patch)!=ALLOWED: raise RuntimeError('forward patch scope/order mismatch')
    if patch_scope(a.rollback)!=ALLOWED: raise RuntimeError('rollback patch scope/order mismatch')
    v=read(cand,'app/version.properties')
    if a.versioned:
        need(v,'VERSION_NAME=0.9726532','versioned name',1); need(v,'VERSION_BUILD=26532','versioned build',1)
    else:
        need(v,'VERSION_NAME=0.9726531','prebuild version name',1); need(v,'VERSION_BUILD=26531','prebuild version build',1)

    bridge=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    need(bridge,'minOf(displayedGlobalZoom, 20.0f)','20x total SR cap',1)
    need(bridge,'spatialReconstructionZoom * renderResidualZoom','SR geometry identity')
    need(bridge,'parameters.motionV2SuperResOutputEnabled) 2f else 1f','fixed 2x output toggle',1)
    need(bridge,'superResWriteLinearRaw = produceNormalStackedDng','DNG-request-only LinearRaw stream',1)
    forbid(bridge,'coerceAtMost(2.0f)','stale 2x reconstruction cap')

    render=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
    need(render,'basePipeline.mParameters.motionV2RenderResidualZoom','render residual zoom authority',1)
    need(render,'IRIS_26532_FINAL_FOV_IDENTITY','final FOV identity marker',1)

    saver=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
    need(saver,'dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);','26531 normal DNG crop authority',1)
    need(saver,'MotionV2Jpeg444Encoder.writeSuperRes(','SR JPEG handoff',1)

    dng=read(cand,NEW)
    for tok,label in [
        ('PHOTOMETRIC_LINEAR_RAW = 34892','LinearRaw photometric'),
        ('SAMPLES_PER_PIXEL = 3','LinearRaw RGB samples'),
        ('new int[]{16, 16, 16}','16-bit RGB'),
        ('rationalArray(TAG_DEFAULT_SCALE, new double[]{1.0, 1.0})','DNG DefaultScale 1:1'),
        ('p.motionV2RenderResidualZoom','residual-only SR DNG crop'),
        ('Files.copy(linearRawRgb16, out);','streamed DNG payload'),
    ]: need(dng,tok,label)

    stack=read(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    for tok,label in [
        ('IRIS_26532_MEMORY_SAFE_STREAMED_2X','memory-safe 2x owner'),
        ('private val resultOutputWidth = if (iris26532StreamingOutput2x) width else outputWidth','native post-chain width'),
        ('IRIS_26532_MEMORY_SAFE_STREAMED_2X onlineFullAccumulator=false','full 2x accumulator disabled'),
        ('maximumBandHeight <= 256','2x band cap'),
        ('IRIS_26532_STREAMED_2X_BANDS','streamed output proof'),
        ('fullHighResPostTexture=false','no whole-image 50mp post texture proof'),
    ]: need(stack,tok,label)

    shaders=read(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt')
    for tok,label in [
        ('IRIS_26532_REJECTION_REAL_SENSOR_SUPPORT','rejection support'),
        ('IRIS_26532_PHYSICAL_SENSOR_SUPPORT','physical auxiliary support'),
        ('IRIS_26532_CONTINUOUS_GEOMETRY_CONFIDENCE','continuous alignment confidence'),
        ('if (!rawInside(p)) continue;','real sample support'),
        ('frameWeight *= clamp(flowAndConfidence.z, 0.0, 1.0);','confidence consumes contribution'),
        ('uReconstructionZoom','crop-aware SR shader'),
    ]: need(shaders,tok,label)

    chroma=read(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
    for tok,label in [
        ('IRIS_26532_FOLIAGE_STRUCTURE_GUIDANCE','foliage structure guidance'),
        ('IRIS_26532_FOLIAGE_LOCAL_MEDIAN_EDGE_GATE','median edge protection'),
        ('IRIS_26532_NO_EDGE_DESATURATION','edge desaturation protection'),
        ('IRIS_26532_IIR_CHROMA_EDGE_RESET','IIR edge reset'),
        ('IRIS_26532_BLEND_EDGE_CHROMA_PROTECT','final blend edge protection'),
    ]: need(chroma,tok,label,1)
    forbid(chroma,'IRIS_26530_V1_3_RGB_DIRECTION_ONLY','regressed RGB-only direction authority')

    prefs=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
    need(prefs,'settingsManager.setInitial(SCOPE_GLOBAL, Key.KEY_IRIS_SUPER_RES, false);','SR default off',1)
    ui=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
    need(ui,'R.string.super_res','Super Res gear label')
    strings=read(cand,'app/src/main/res/values/strings.xml'); need(strings,'<string name="super_res">Super Res</string>','Super Res label',1)

    zoom=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java')
    activity=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java')
    need(activity,'if (savedInstanceState == null)','new activity session guard',1)
    need(activity,'resetForNewCameraActivitySession();','fresh launch 1x reset',1)
    need(zoom,'selected = findClosestToOne();','physical lens closest to 1x')

    hdrx=read(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    need(hdrx,'processingParameters.motionV2SuperResOutputEnabled =','capture-time SR snapshot',1)
    need(hdrx,'IrisMotionSuperResDngWriter.write(','SR DNG writer uses',2)
    need(hdrx,'saveNormalized16StackedRaw(','normal 26531 DNG path retained',2)

    cpp=read(cand,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
    need(cpp,'writeSuperResNative','native streaming JPEG owner')
    need(cpp,'std::vector<uint8_t>row((size_t)outW*3)','row-only high-res JPEG buffer',1)
    cmake=read(cand,'app/src/main/cpp/CMakeLists.txt'); need(cmake,'turbojpeg-static jpeg-static','libjpeg link',1)

    # Freeze important inherited 26531 IQ/runtime contracts.
    need(bridge,'IRIS_26530_V1_3_ZERO_MGC_LUMA','26531 inherited zero-luma freeze')
    need(bridge,'val lumaScale = 0f','zero luma strength',1)
    need(bridge,'MgcMergeMethod.SPATIAL_RGB','Spatial RGB active route')
    forbid(bridge,'MgcMergeMethod.SABRE','Sabre runtime route')
    # No exposure-policy owner enters the 26532 patch.
    exposure_owners = ('CaptureController.java','ExposureSelector.java','IsoExpoSelector.java','IrisMotionSettings.java')
    for rel in changed:
        if rel.endswith(exposure_owners): raise RuntimeError('exposure/ISO policy owner changed in 26532: '+rel)

    geom=geometry_tests()
    report={'status':'PASS','changedFiles':changed,'forwardPatchSha256':sha(a.patch),'rollbackPatchSha256':sha(a.rollback),'geometryCases':geom,
            'contracts':['20x_total_sr','fixed_2x_toggle','normal_dng_26531_crop','sr_linearraw_dng','jpeg_dng_fov_parity','streamed_memory_safe_2x','pink_support_geometry','foliage_edge_chroma','fresh_launch_1x','26531_zero_luma','sabre_dormant','no_exposure_policy_change']}
    if a.json_out: Path(a.json_out).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS: 26532 scope + SR/DNG/JPEG + memory + pink/foliage + inherited IQ contracts')
    print('PASS: 23-file allowlist exact; normal 26531 DNG path retained; exposure/ISO policy untouched')
    print('PASS: geometry cases',len(geom),'DNG=JPEG through 30x with SR cap 20x')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr); raise
