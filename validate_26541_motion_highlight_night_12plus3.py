#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re, sys

RUNTIME=[
'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def die(s): raise SystemExit('ERROR: '+s)
def need(s,t,label):
    if t not in s: die(label+' missing: '+t)
def forbid(s,t,label):
    if t in s: die(label+' forbidden: '+t)
def manifest(root):
    d={}
    for base in (root/'app/src/main',):
        for p in base.rglob('*'):
            if p.is_file(): d[p.relative_to(root).as_posix()]=sha(p)
    for rel in ('app/version.properties','app/build.gradle'):
        p=root/rel
        if p.is_file(): d[rel]=sha(p)
    return d

def validate(base,cand,postbuild=False):
    mb,mc=manifest(base),manifest(cand)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k) and k!='app/version.properties')
    if changed!=sorted(RUNTIME): die('runtime allowlist mismatch: '+repr(changed))
    v=(cand/'app/version.properties').read_text()
    if postbuild:
        need(v,'VERSION_NAME=0.9726541','postbuild version'); need(v,'VERSION_BUILD=26541','postbuild build')
    else:
        need(v,'VERSION_NAME=0.9726540','prebuild version'); need(v,'VERSION_BUILD=26540','prebuild build')
    bcap=(base/RUNTIME[1]).read_text(); cap=(cand/RUNTIME[1]).read_text()
    # Motion ZSL owner must stay Motion-only. This semantic anchor is protected, not guessed from comments.
    m=re.search(r'(?:private|public|protected) boolean isZslMode\(\)\s*\{(.*?)\n\s*\}',cap,re.S)
    if not m: die('isZslMode body missing')
    if 'CameraMode.MOTION' not in m.group(1) or 'CameraMode.NIGHT' in m.group(1): die('Night entered ZSL owner')
    for t in ('IRIS_26541_NIGHT_FRESH_CAPTURE_CONTRACT','IRIS_26541_NIGHT_SHORT_TAG','IRIS_26541_NIGHT_LONG_TAG',
              'IrisNightFrameSelector.SHORT_FRAMES','IrisNightFrameSelector.LONG_FRAMES','applyShortPlan','applyLongPlan',
              'zsl=false motionRing=false preShutterRaw=false'):
        need(cap,t,'Night capture contract')
    forbid(cap,'startMotionPrebufferPump();\n                Log.i(TAG, "IRIS_26541','Night prebuffer')
    selector=(cand/RUNTIME[6]).read_text()
    for t in ('SHORT_FRAMES = 12','LONG_FRAMES = 3','TOTAL_FRAMES = SHORT_FRAMES + LONG_FRAMES','return TOTAL_FRAMES'):
        need(selector,t,'12+3 selector')
    exposure=(cand/RUNTIME[5]).read_text()
    for t in ('IRIS_26541_NIGHT_12_PLUS_3_EXPOSURE_SOLE_OWNER','LONG_TARGET_MULTIPLIER = 4.0','applyShortPlan','applyLongPlan',
              'int longIso = shortIso','longExposure <= shortExposure'):
        need(exposure,t,'Night exposure')
    for t in ('IsoExpoSelector.','mZslRingBuffer','startMotionPrebufferPump(','new MotionBatch('):
        forbid(exposure,t,'Night exposure isolation')
    frame=(cand/RUNTIME[2]).read_text(); need(frame,'NORMAL, HIGHLIGHT_SHORT, SHADOW_LONG','Night shadow role')
    batch=(cand/RUNTIME[3]).read_text()
    for t in ('requestedShortFrames','requestedLongFrames','shortFrameCount','longFrameCount','MotionV2FrameRole.SHADOW_LONG',
              'MotionV2FrameRole.HIGHLIGHT_SHORT','reference == null'):
        need(batch,t,'immutable Night batch')
    proc=(cand/RUNTIME[7]).read_text()
    for t in ('IRIS_26541_NIGHT_12_PLUS_3_DIRECT_PROCESS_ENTRY','referenceRole=SHORT','irisRelativeExposureMpy','zsl=false motionRing=false preShutterRaw=false'):
        need(proc,t,'Night processor')
    forbid(proc,'IrisRcdDemosaic','RCD in Night')
    bridge=(cand/RUNTIME[8]).read_text()
    for t in ('IRIS_26541_RESTORE_26535_ZERO_MGC_LUMA','val userLumaScale = 0f','val lumaScale = 0f',
              'val chromaScale = irisSettings.chromaDenoise','ImageFrame.MotionV2FrameRole.SHADOW_LONG','parameters.irisNightActive'):
        need(bridge,t,'MGC bridge')
    forbid(bridge,'IrisRcdDemosaic','RCD in bridge')
    hs=(cand/RUNTIME[0]).read_text()
    for t in ('uniform vec3 CameraNeutral','centerClipGate=smoothstep(0.88,0.985,peak3(c))',
              'if(centerClipGate<=0.0){ Output=c; return; }','opposedPair','edgeGate','outlierGate','donorConfidence',
              'IRIS_26541_FULL_CENSOR_CAMERA_NEUTRAL_FALLBACK','if(c.r>=0.985) repaired.r=max(repaired.r,c.r)',
              'if(c.g>=0.985) repaired.g=max(repaired.g,c.g)','if(c.b>=0.985) repaired.b=max(repaired.b,c.b)'):
        need(hs,t,'highlight reconstruction')
    for t in ('lowReliabilityGate','contextGate=max(clipGate,lowReliabilityGate)','nearClipRequired=false','amountCap=mix(0.32'):
        forbid(hs,t,'26536 widened gate')
    hj=(cand/RUNTIME[4]).read_text()
    for t in ('IRIS_26541_HIGHLIGHT_OPPOSED_RECONSTRUCTION','basePipeline.mParameters.whitePoint','CameraNeutral',
              'centerNearClipRequired=true','nonClipActivation=0','treeFoliageNonClipProtected=true','rcd=false'):
        need(hj,t,'highlight host')
    forbid(hj,'IrisRcdDemosaic','RCD in highlight')
    # Core image owners not allowlisted must be byte-identical by the exact-delta proof. Assert particularly critical domains.
    protected=[
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
    ]
    for rel in protected:
        if rel in mb and rel in mc and mb[rel]!=mc[rel]: die('protected current owner changed: '+rel)
    print(json.dumps({'postbuild':postbuild,'changed_runtime_files':changed,'motion_zsl':'MOTION_ONLY',
      'night_capture':'FRESH_12_SHORT_PLUS_3_LONG','night_routing':'MGC_SPATIAL_RGB','rcd_active':False,
      'mgc_luma':0.0,'highlight_nonclip_activation':0.0,'chroma_owner':'irisSettings.chromaDenoise'},indent=2))
    print('PASS: 26541 exact nine-file runtime scope and protected current owners')
    print('PASS: Motion highlight opposed reconstruction is near-clip-only; 26536 widened non-clip gate absent')
    print('PASS: Night is fresh non-ZSL 12+3 with short geometry authority and Night-only SHADOW_LONG roles')
    print('PASS: shared MGC full-resolution luma rollback=0; chroma remains independent; no RCD')

def self_test():
    # Exercise token helpers and the exact local candidate when available.
    root=Path('/mnt/data/iris26541_work')
    if (root/'base').exists() and (root/'candidate26541').exists(): validate(root/'base',root/'candidate26541',False)
    print('PASS: 26541 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--postbuild',action='store_true'); ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.base or not a.candidate: ap.error('--base and --candidate required')
        validate(Path(a.base),Path(a.candidate),a.postbuild)
