#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math, tempfile, shutil, sys

ALLOWED = [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/SaverImplementation.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt',
]
PROTECTED = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdDemosaic.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionRcdShortChromaOverlay.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl',
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):
    out={}
    for top in ('app/src/main','app/version.properties','app/build.gradle'):
        p=root/top
        if p.is_file(): out[top]=sha(p)
        else:
            for f in p.rglob('*'):
                if not f.is_file(): continue
                rel=str(f.relative_to(root))
                if rel.startswith('app/src/main/cpp/third_party_26507/'):
                    continue
                if rel.startswith('app/src/main/cpp/deps/') and rel != 'app/src/main/cpp/deps/.gitignore':
                    continue
                out[rel]=sha(f)
    return out

def require(c,msg):
    if not c: raise SystemExit('FAIL: '+msg)
def text(root,rel): return (root/rel).read_text()
def once(s,needle,label): require(s.count(needle)==1, f'{label} count={s.count(needle)} expected=1')
def ordered(s, needles, label):
    pos=-1
    for n in needles:
        p=s.find(n,pos+1)
        require(p>=0, f'{label}: missing {n}')
        require(p>pos, f'{label}: order failure {n}')
        pos=p

def validate(base,cand):
    require(base.is_dir() and cand.is_dir(),'base/candidate directory missing')
    mb,mc=manifest(base),manifest(cand)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    require(changed==sorted(ALLOWED), f'changed-file allowlist mismatch: {changed}')
    require(len(mb)==962 and len(mc)==962, f'candidate file count drift base={len(mb)} candidate={len(mc)}')
    for rel in PROTECTED:
        require((base/rel).is_file() and (cand/rel).is_file(), f'protected path missing {rel}')
        require(sha(base/rel)==sha(cand/rel), f'protected owner drift {rel}')
    for rel in ('app/version.properties','app/build.gradle'):
        require(sha(base/rel)==sha(cand/rel), f'build/version file changed unexpectedly {rel}')
    vp=text(cand,'app/version.properties')
    require('VERSION_NAME=0.9726533' in vp and 'VERSION_BUILD=26533' in vp,'version/build drift')

    # V1.5 normalized16 fix must survive exactly.
    rcd=text(cand,ALLOWED[3])
    once(rcd,'IRIS_26533_V15_NORMALIZED16_RCD_DOMAIN','V1.5 normalized16 marker')
    require('glProg.setVar("blackLevel",new float[]{0f,0f,0f,0f})' in rcd,'normalized16 black=0 lost')
    require('glProg.setVar("whiteLevel",65535.0f)' in rcd,'normalized16 white=65535 lost')
    require('IRIS_26533_V16_GPU_CENSORED_PROVENANCE' in rcd,'GPU provenance classifier missing')
    require('useAssetProgram("motionv2/highlight_provenance_init",true)' in rcd,'provenance shader not reused')
    require('referenceExposureScale",1.0f' in rcd and 'physicalClipThreshold",250.0f/255.0f' in rcd,
            'normalized16 provenance domain constants drift')
    require('shortValidatedInvented=false cpuReadback=false' in rcd,'provenance non-invention contract missing')
    require('motionV2MgcSourceExposureGain=1.0f' in rcd,'normal-only Bayer source gain not neutralized')
    require('for(int i=0;i<packed.x*packed.y;i++) prov.putFloat(0f)' not in rcd,'null provenance still fabricated all NORMAL')
    require('textureBuffer(' not in rcd,'RCD input reintroduced CPU provenance readback')
    require('glProg.setTexture("normalCfa",WorkingTexture)' in rcd and
            'glProg.setTextureCompute("outProvenance",p.motionV2HighlightProvenanceTexture,true)' in rcd,
            'GPU provenance host bindings drift')
    sh=text(cand,'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl')
    for needle in ('uniform highp sampler2D normalCfa;',
                   'layout(r32f, binding = 0) uniform highp writeonly image2D outProvenance;',
                   'uniform float referenceExposureScale;', 'uniform float physicalClipThreshold;'):
        require(needle in sh, 'GPU provenance shader contract missing '+needle)
    legacy=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    require('useAssetProgram("motionv2/highlight_provenance_init", true)' in legacy and
            'setTextureCompute("outProvenance", iris26492BaseProvenance, true)' in legacy,
            'provenance shader no longer has proven legacy host usage')
    glp=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java')
    require('glMemoryBarrier(GL_ALL_BARRIER_BITS);' in glp,
            'deferred compute memory barrier missing')

    # Protected Motion presentation ordering.
    pp=text(cand,ALLOWED[4])
    once(pp,'IRIS_26533_V16_MOTION_RCD_PROTECTED_POST_ORDER','Motion protected post marker')
    ordered(pp,[
        'add(new IrisRcdBayerInput())', 'add(new IrisRcdDemosaic())',
        'add(new IrisMotionRcdShortChromaOverlay())', 'add(new MotionV2MgcSourceExposure())',
        'add(new MotionV2ColorTransform())', 'add(new MotionV2ViewfinderExposureMatcher())',
        'add(new MotionV2DisplayExposure())', 'add(new MotionV2Render())'], 'Motion RCD post graph')
    require('IrisMotionSettings.Snapshot irisMotionSettings = IrisMotionSettings.current()' in pp,
            'manual tone controls owner not restored')

    # Night RAW physical layout must be copied while Image exists.
    sav=text(cand,ALLOWED[2])
    once(sav,'IRIS_26533_V16_NIGHT_RAW_PLANE_LAYOUT_OWNER','Night plane-layout marker')
    require('image.getPlanes()[0].getRowStride()' in sav and 'image.getPlanes()[0].getPixelStride()' in sav,
            'physical RAW stride capture missing')
    require('image.getWidth(), height' in sav,'logical RAW geometry/crop capture missing')

    frame=text(cand,ALLOWED[1])
    require('TotalCaptureResult irisNightExactCaptureResult' in frame and 'CaptureRequest irisNightExactCaptureRequest' in frame,
            'Night exact metadata owners missing from ImageFrame')

    cc=text(cand,ALLOWED[0])
    once(cc,'IRIS_26533_V16_NIGHT_TIMESTAMP_METADATA_OWNER','Night timestamp owner marker')
    require('mIrisNight26533Results.get(imageTs)' in cc and 'mIrisNight26533Requests.get(imageTs)' in cc,
            'Night does not exact-match result/request by image timestamp')
    require('resultTs.longValue() != imageTs' in cc,'Night exact SENSOR_TIMESTAMP equality guard missing')
    require('populateMotion26480FrameMetadata(frame, exact, false)' in cc,'trusted per-frame metadata helper not reused')
    require('mIrisNight26533Results.size() != expectedFrames' in cc and 'mIrisNight26533Requests.size() != expectedFrames' in cc,
            'Night image/result/request cardinality invariant missing')
    require('prepareIrisNight26533ExactMetadata(finalFrameCount)' in cc,'Night metadata not sealed before runRaw')
    zsl=cc.find('if (isZslMode())')
    mode=cc.find('final CameraMode iris26533CaptureMode', zsl)
    require(zsl >= 0 and mode > zsl and cc.find('return;', zsl, mode) >= 0,
            'Night capture-mode bookkeeping leaked before Motion/ZSL early return')
    require('nearest' not in cc[cc.find('prepareIrisNight26533ExactMetadata'):cc.find('prepareIrisNight26533ExactMetadata')+5000].lower(),
            'Night helper appears to borrow neighboring metadata')

    hp=text(cand,ALLOWED[5])
    once(hp,'IRIS_26533_V16_NIGHT_BASE_REFERENCE_AUTHORITY','Night base-reference marker')
    require('final int width=irisNightBase.motionV2PlaneLogicalWidth' in hp,'Night still uses padded RAW width')
    require('p.FillDynamicParameters(irisNightBase.irisNightExactCaptureResult' in hp,
            'Night global parameters not owned by exact MGC base result')
    require('long ref=irisNightBase.getTimestamp()' in hp,'Night MGC reference not exact first/base frame')
    for needle in ['motionV2ActualExposureNs<=0L','motionV2ActualIso<=0','motionV2ExposureEnergy<=0.0',
                   '"CAMERA2_PER_FRAME".equals(f.motionV2NoiseProfileSource)','!f.motionV2BlackLevelValid',
                   '!f.motionV2WhiteLevelValid']:
        require(needle in hp, f'Night radiometric prevalidation missing {needle}')

    nb=text(cand,ALLOWED[6])
    require('Night reference must equal MGC first NORMAL base' in nb,'Night bridge reference/base invariant missing')
    require('Night exact base white level is missing' in nb,'Night exact white-level authority missing')
    require('sensorTimestampNs = frame.motionV2ResultSensorTimestampNs' in nb,'Night bridge timestamp fallback still present')
    require('frame.irisNightExactCaptureResult != null && frame.irisNightExactCaptureRequest != null' in nb,
            'Night bridge exact owner validation missing')
    require('dynamic/fixed white level invalid' in nb,'Night per-frame white validation missing')

    # Known no-go paths must remain absent from the V1.6 delta.
    for bad in ('ADRC','single-frame fallback','single frame fallback'):
        for rel in ALLOWED:
            delta_candidate=text(cand,rel)
            delta_base=text(base,rel)
            # New occurrences only are forbidden.
            require(delta_candidate.count(bad)<=delta_base.count(bad), f'new forbidden behavior marker {bad} in {rel}')

    print('PASS: 26533 V1.6 exact V1.5 lineage runtime validation')
    print('PASS: 7-file allowlist + normalized16 + GPU provenance + Motion post ownership + Night exact metadata')


def self_test():
    # Exercise helper invariants without pretending to validate Android source.
    require(sorted(ALLOWED)==sorted(set(ALLOWED)),'allowlist contains duplicates')
    require(len(ALLOWED)==7,'allowlist cardinality must remain 7')
    require(len(PROTECTED)==len(set(PROTECTED)),'protected list contains duplicates')
    print('PASS: V1.6 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test: self_test(); raise SystemExit(0)
    require(a.base and a.candidate,'--base and --candidate required')
    validate(Path(a.base),Path(a.candidate))
