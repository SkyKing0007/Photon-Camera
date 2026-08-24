#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path

FILES = [
'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
]

def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
def text(root,rel):
    p=root/rel; req(p.is_file(),'missing '+rel); return p.read_text(encoding='utf-8')
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):
    out={}
    for top in ('app/src/main',):
        p=root/top
        for f in p.rglob('*'):
            if f.is_file(): out[str(f.relative_to(root))]=h(f)
    return out

def ordered(s,tokens,label):
    pos=-1
    for t in tokens:
        n=s.find(t,pos+1); req(n>=0,f'{label}: missing {t}'); req(n>pos,f'{label}: order drift at {t}'); pos=n

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        req(len(FILES)==8 and len(set(FILES))==8,'allowlist malformed'); print('PASS: 26535 validator self-test'); return
    req(a.base and a.candidate,'--base and --candidate required')
    b=Path(a.base); c=Path(a.candidate)
    mb,mc=manifest(b),manifest(c)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    req(changed==sorted(FILES),'26535 changed-file allowlist mismatch: '+repr(changed))
    req(len(mb)==960 and len(mc)==962,f'app/src file counts base={len(mb)} candidate={len(mc)}')
    req((b/'app/build.gradle').read_bytes()==(c/'app/build.gradle').read_bytes(),'build.gradle changed')
    bv=text(b,'app/version.properties'); cv=text(c,'app/version.properties')
    req('VERSION_NAME=0.9726534' in bv and 'VERSION_BUILD=26534' in bv,'base version drift')
    req((('VERSION_NAME=0.9726534' in cv and 'VERSION_BUILD=26534' in cv) or
         ('VERSION_NAME=0.9726535' in cv and 'VERSION_BUILD=26535' in cv)), 'candidate version is neither preversion nor target')

    hdr=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    start=hdr.find('private void ApplyIrisNight26533()'); end=hdr.find('private void ApplyHdrX()',start)
    req(start>=0 and end>start,'Night method boundaries missing'); night=hdr[start:end]
    req(night.count('PhotonMotionMgc1271Bridge.reconstruct(')==1,'Night must execute exactly one shared Spatial-RGB MGC pass')
    req('IrisNightMgc1271Bridge.reconstruct(' not in hdr,'legacy Night Spatial-Bayer bridge still active')
    req('IRIS_26535_NIGHT_SHARED_SPATIAL_RGB_SOLE_OWNER' in hdr,'Night shared Spatial-RGB owner marker missing')
    for t in ('RunIrisNightRgb(rgb,p)',
              'IrisNightNeuralEnhancer.enhanceInPlace(img)','secondMgcPass=false',
              'jpegCarrier=MGC_SPATIAL_RGB_RGBA32F','spatialBayer=false rcd=false'):
        req(t in night,'Night Spatial-RGB contract missing '+t)
    req('RunIrisNightBayer' not in night,'Night Bayer post entry survived active Night method')
    req('r.stackedDngRaw16' in night and 'production RGB aliases DNG sidecar' in night,
        'Night DNG sidecar separation invariant missing')

    post=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    n0=post.find('if(mParameters.irisNightActive){'); n1=post.find('/* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */',n0)
    req(n0>=0 and n1>n0,'Night post graph boundaries missing'); ng=post[n0:n1]
    ordered(ng,['new MotionV2CfaInput()','new MotionV2MgcSourceExposure()','new MotionV2HighlightChromaReliability()',
                'new MotionV2ColorTransform()','new MotionV2DisplayExposure()','new MotionV2Render()'], 'Night post graph')
    req('IrisRcd' not in ng and 'Demosaic' not in ng,'Night active graph contains Bayer/RCD/demosaic consumer')
    req('26535 architecture guard: Night production must use shared Spatial RGB' in post,'Night Bayer hard guard missing')
    req('Motion JPEG cannot consume fused/DNG Bayer through RCD' in post,'Motion DNG-as-JPEG hard guard missing')
    m0=post.find('if (mParameters.motionV2Active)'); req(m0>=0,'Motion graph missing'); mg=post[m0:]
    ordered(mg,['new MotionV2MgcSourceExposure()','new MotionV2HighlightChromaReliability()',
                'new MotionV2ColorTransform()','new MotionV2ViewfinderExposureMatcher()','new MotionV2DisplayExposure()'], 'Motion post graph')

    bridge=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    for t in ('outputMode = MgcSpatialOutputMode.RGB','mergeMethod = MgcMergeMethod.SPATIAL_RGB',
              'exportGpuLinearRgbSource = true','gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F',
              'publishSpatialReliability(parameters','gateSuperResDetailByNativeReliability(',
              'baseCarrierUntouched=true','source=MGC_AOT_REJECTION_NOISE_VARIANCE notFrameCount=true',
              'grid8x6=','IRIS_26535_SPATIAL_RGB_TIMING'):
        req(t in bridge,'shared MGC/support contract missing '+t)
    req('val weight = conf * conf' in bridge and 'val delta = code - 128' in bridge,
        'SR reliability gate no longer attenuates only detail residual')

    node=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java')
    req('(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)' in node,
        'chroma guard is not shared Motion/Night')
    req('stage=beforeProfileColor' in node and 'hueTargeting=false' in node,'chroma guard telemetry drift')
    shader=text(c,'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl')
    for t in ('clipGate*edgeGate*outlierGate','med5(','Output=c+delta*safeAmount;','gamutSafe'):
        req(t in shader,'highlight chroma shader contract missing '+t)
    req('Output=max(' not in shader,'post-correction clamp can violate luminance preservation')
    low=shader.lower(); req(all(x not in low for x in ('magenta','orange','purple','huegate')),'shader contains hue-targeted correction')

    params=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
    for t in ('motionV2SpatialReliability','IrisSpatialReliabilityMean','IrisSpatialReliabilityLowFraction'):
        req(t in params,'reliability metadata missing '+t)
    enc=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
    req(enc.count('IRIS_26535_SUPER_RES_TIMING')>=2,'SR encode timing telemetry missing')

    # Base-protected owners must remain byte-exact by allowlist; assert key legacy metadata owner still exists.
    capture=text(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    req('IRIS_26533_V16_NIGHT_EXACT_METADATA_READY' in capture,'V1.6 exact Night metadata owner lost')
    req('prepareIrisNight26533ExactMetadata' in capture,'Night exact metadata population missing')
    print('PASS: 26535 exact 8-file allowlist')
    print('PASS: Motion + Night share one Spatial-RGB production core; Bayer DNG remains export-only')
    print('PASS: SR detail is native-reliability-gated without modifying base carrier')
    print('PASS: highlight correction is pre-profile, hue-independent, chroma-only/luma-preserving')

if __name__=='__main__': main()
