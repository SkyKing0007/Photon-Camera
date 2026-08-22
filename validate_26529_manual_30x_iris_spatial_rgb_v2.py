#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, json, re, sys
from pathlib import Path

BASE_VERSION='0.9726528'; BASE_BUILD='26528'
TARGET_VERSION='0.9726529'; TARGET_BUILD='26529'
BJZHOU_POST_BLOB='5f29df5461cb50b199a6b19eea096127bf4af35c'
IRIS_TEMPLATE_SHA256='5e112314f0795e4294e3af9e8b127d7d86cdfa494cd8df042fd5c6ba9d7949a4'
ZOOM='app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java'
SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
STACKER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
PACKER='app/src/main/java/com/hinnka/mycamera/utils/DirectBufferPixelPacker.kt'
ALLOWED=(ZOOM,SHADER,STACKER,POST,PACKER)
PROTECTED=(
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
)

class ValidationError(RuntimeError): pass

def req(ok,msg):
    if not ok: raise ValidationError(msg)

def text(root,rel): return (Path(root)/rel).read_text()
def data(root,rel):
    p=Path(root)/rel
    return p.read_bytes() if p.exists() else None

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def git_blob_sha1(b):
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def all_runtime_files(root):
    root=Path(root); out=[]
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file(): out.append(p.relative_to(root).as_posix())
    return sorted(out)

def changed_files(base,cand):
    names=sorted(set(all_runtime_files(base))|set(all_runtime_files(cand)))
    return [n for n in names if data(base,n)!=data(cand,n)]

def method_body(s, signature):
    start=s.find(signature); req(start>=0, f'method signature missing: {signature}')
    brace=s.find('{',start); req(brace>=0, f'opening brace missing: {signature}')
    depth=0; i=brace; line=block=instr=inchr=False; esc=False
    while i<len(s):
        c=s[i]; d=s[i+1] if i+1<len(s) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and d=='/': block=False; i+=1
        elif instr:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': instr=False
        elif inchr:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=="'": inchr=False
        else:
            if c=='/' and d=='/': line=True; i+=1
            elif c=='/' and d=='*': block=True; i+=1
            elif c=='"': instr=True
            elif c=="'": inchr=True
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0: return s[start:i+1]
        i+=1
    raise ValidationError(f'unterminated method: {signature}')

def make_patch(base,cand,reverse=False):
    chunks=[]
    for rel in ALLOWED:
        a=data(base,rel); b=data(cand,rel)
        if reverse: a,b=b,a
        if a==b: continue
        aa=[] if a is None else a.decode().splitlines(keepends=True)
        bb=[] if b is None else b.decode().splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(
            aa,bb,
            fromfile='/dev/null' if a is None else f'a/{rel}',
            tofile='/dev/null' if b is None else f'b/{rel}',n=3,
        ))
    return ''.join(chunks)

def validate(base,cand,patch,rollback,postbuild=False):
    base=Path(base); cand=Path(cand)
    changed=changed_files(base,cand)
    req(changed==sorted(ALLOWED), f'runtime changed-file allowlist mismatch: {changed}')
    bv=text(base,'app/version.properties'); cv=text(cand,'app/version.properties')
    req(f'VERSION_NAME={BASE_VERSION}' in bv and f'VERSION_BUILD={BASE_BUILD}' in bv, 'base is not exact 26528 version')
    if postbuild:
        req(f'VERSION_NAME={TARGET_VERSION}' in cv and f'VERSION_BUILD={TARGET_BUILD}' in cv, 'postbuild candidate version is not 26529')
    else:
        req(f'VERSION_NAME={BASE_VERSION}' in cv and f'VERSION_BUILD={BASE_BUILD}' in cv, 'candidate version changed before guarded build block')
        req(TARGET_VERSION not in cv and f'VERSION_BUILD={TARGET_BUILD}' not in cv, '26529 version applied too early')
    for rel in PROTECTED:
        req(data(base,rel)==data(cand,rel), f'protected runtime changed: {rel}')

    z=text(cand,ZOOM)
    req('IRIS_26529_MANUAL_PHYSICAL_LENS_30X_OWNER' in z, 'manual zoom owner marker missing')
    req('public static final float LOCAL_MAX_ZOOM = 30.0f;' in z, '30x local ceiling missing')
    req('TELE_MAX_GLOBAL_ZOOM' not in z and 'NO_TELE_MAX_GLOBAL_ZOOM' not in z, 'old global zoom caps survived')
    req('LENS_HANDOFF_HYSTERESIS_FRACTION' not in z, 'pinch handoff hysteresis survived')
    req('ownerWithHysteresis' not in z and 'ownerFor(float globalZoom)' not in z, 'automatic physical owner helpers survived')
    pinch=method_body(z,'    public void onPinchScale(float scaleFactor)')
    for forbidden in ('PreferenceKeys.setCameraID','restartCameraForIrisHandoff','sOwnerCameraId =','sPendingOwnerCameraId = next'):
        req(forbidden not in pinch, f'pinch still changes physical route: {forbidden}')
    req('float nextLocal = clamp(currentLocal * scaleFactor, 1.0f, LOCAL_MAX_ZOOM);' in pinch, 'pinch local 1..30 clamp missing')
    req('sRequestedGlobalZoom = anchor * nextLocal;' in pinch, 'equivalent/global display mapping missing')
    lens=method_body(z,'    public void onLensButtonSelected(String cameraId)')
    for tok in ('sGlobalZoom = sOpticalAnchor;','sRequestedGlobalZoom = sOpticalAnchor;','sHardwareLocalZoom = 1.0f;','sResidualSoftwareZoom = 1.0f;'):
        req(tok in lens, f'explicit lens local-1x reset missing: {tok}')
    req('float maximum = anchor * LOCAL_MAX_ZOOM;' in z, 'per-lens equivalent maximum missing')
    snap=re.search(r'this\.outputLocalZoom\s*=\s*Float\.isFinite\(requestedLocal\).*?LOCAL_MAX_ZOOM\)\s*:\s*1\.0f;',z,re.S)
    req(bool(snap), 'snapshot local zoom is not finite-clamped 1..30')
    apply=method_body(z,'    public static float applyToRequest(CaptureRequest.Builder builder,')
    for tok in ('CONTROL_ZOOM_RATIO_RANGE','SCALER_AVAILABLE_MAX_DIGITAL_ZOOM','clamp(localZoom, 1.0f, supportedHardwareMax)','localZoom / hardwareZoom','IRIS_26529_SAFE_30X_REQUEST'):
        req(tok in apply, f'safe HAL/residual zoom token missing: {tok}')
    req(apply.count('catch (Throwable')>=2, 'HAL zoom paths are not exception-guarded')
    upd=method_body(z,'    public static CaptureZoomUpdate updateFromCaptureResult(')
    req('IRIS_26529_HAL_TELEMETRY_ONLY' in upd, 'CaptureResult telemetry-only marker missing')
    req('return new CaptureZoomUpdate(residual, false, null, false, false);' in upd, 'CaptureResult must not commit physical handoff')
    for tok in ('sGlobalZoom =','sRequestedGlobalZoom =','sOwnerCameraId =','sPendingOwnerCameraId ='):
        req(tok not in upd, f'CaptureResult still owns zoom/physical state: {tok}')

    # Existing DNG local authority must remain intact and byte-identical.
    im=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
    prm=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
    req('dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);' in im, 'DNG local zoom authority changed')
    req('motionV2OutputZoom' in prm, 'Parameters Motion local zoom carrier missing')
    cap=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    req('IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART' in cap and 'activity.runOnUiThread' in cap, '26528 UI-thread restart repair lost')

    sh=text(cand,SHADER)
    req('return exp2(-0.5 * max(distance, 0.0)) + 0.00005;' in sh, 'c317 spatial kernel missing')
    req('float rational =' not in sh and 'ROBUST_SPATIAL_KERNEL' not in sh, 'pre-c317 robust kernel survived')
    for tok in ('uniform float uGlobalFrameWeight;','frameWeight *= uGlobalFrameWeight;','vec2 greenDirectionMoment','directionMoment * weights.r * frameWeight','packDirectionMoment(directionMoment)','IRIS_26529_C317_RGB16UI_TO_RGBA16F'):
        req(tok in sh, f'c317 RGB fusion semantic missing: {tok}')
    st=text(cand,STACKER)
    for tok in ('"uGlobalFrameWeight",','frame.calibration.globalFrameWeight','GlesIris26529SpatialRgbChromaPostprocessor','normalizationTargetTexture()','markBandWritten','colorNoiseIir=','renderRgb16ToFloat','rgbChromaPostprocessor?.release()'):
        req(tok in st, f'c317 host integration missing: {tok}')
    req('GlesIris26521SpatialRgbShaders.normalizeRgbFloat' not in st, 'old direct float normalize bypass survived')

    post_bytes=data(cand,POST); req(post_bytes is not None, 'Iris Spatial-RGB chroma rewrite missing')
    req(sha256_bytes(post_bytes)==IRIS_TEMPLATE_SHA256, 'Iris Spatial-RGB rewrite template hash drift')
    req(git_blob_sha1(post_bytes)!=BJZHOU_POST_BLOB, 'Iris runtime must not be a verbatim bjzhou c317 blob')
    post=post_bytes.decode()
    for tok in (
        'IRIS_26529_SPATIAL_RGB_CHROMA_REWRITE_OWNER',
        'internal class GlesIris26529SpatialRgbChromaPostprocessor(',
        'internal object Iris26529SpatialRgbChromaShaders',
        'directionMomentAt(ivec2 p)',
        'count << 8',
        'float steadyOutput',
        '1.0+b[1]+b[2]',
        'State steadyState(float value)',
        'uimage2D uInput',
        'imageStore(uOutput,p,outputPixel)',
        'validateCoverage(newBands)',
        'normalizationTargetTexture()',
    ):
        req(tok in post, f'Iris c317-semantic rewrite token missing: {tok}')
    req('GlesMgcSpatialRgbChromaPostprocessor' not in post, 'bjzhou runtime owner leaked into Iris rewrite')
    req('uimage2DArray' not in post, 'tile-array postprocessing survived; full contiguous 2D required')
    pack=text(cand,PACKER)
    for tok in ('IRIS_26529_SAFE_CPU_RGBA16UI_RGB16_PACKER','destinationLeft + sourceWidth > destinationWidth','src.capacity().toLong() < srcNeeded'):
        req(tok in pack, f'safe compatibility packer token missing: {tok}')
    req('System.loadLibrary' not in pack and 'external fun' not in pack, 'new packer must not create unresolved JNI dependency')

    p=Path(patch).read_text(); r=Path(rollback).read_text()
    req(p==make_patch(base,cand,False), 'forward patch does not independently reproduce candidate delta')
    req(r==make_patch(base,cand,True), 'rollback patch does not independently reproduce base delta')
    return {
      'base_version':BASE_VERSION,'base_build':BASE_BUILD,'target_version':TARGET_VERSION,'target_build':TARGET_BUILD,
      'changed':changed,'protected_byte_identical':list(PROTECTED),
      'bjzhou_reference_post_blob':BJZHOU_POST_BLOB,
      'iris_rewrite_sha256':IRIS_TEMPLATE_SHA256,
      'forward_patch_sha256':sha256_bytes(Path(patch).read_bytes()),
      'rollback_patch_sha256':sha256_bytes(Path(rollback).read_bytes()),
      'dng_local_zoom_authority':'parameters.motionV2OutputZoom',
      'physical_lens_switching':'button-only','local_zoom_max':30.0,
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--candidate',required=True)
    ap.add_argument('--patch',required=True); ap.add_argument('--rollback',required=True); ap.add_argument('--json-out'); ap.add_argument('--postbuild',action='store_true')
    a=ap.parse_args(); result=validate(a.base,a.candidate,a.patch,a.rollback,a.postbuild)
    if a.json_out: Path(a.json_out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: 26529 V2 independent manual-30x + Iris-owned c317-semantic Spatial RGB validator')

if __name__=='__main__':
    try: main()
    except (ValidationError,AssertionError,OSError,UnicodeError) as e:
        print('ERROR:',e,file=sys.stderr); sys.exit(2)
