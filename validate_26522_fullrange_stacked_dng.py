#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,re
from pathlib import Path

HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
CONTRACTS='app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'
IRIS_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
IRIS_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
IMAGE_SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'
FUSION='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
RELEASE_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
RELEASE_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'
MATCHER='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
PREFS='app/src/main/res/xml/preferences.xml'
VERSION='app/version.properties'
EXPECTED_CHANGED={HDRX,MERGER,BRIDGE,CONTRACTS,IRIS_STACK,IRIS_SHADER,IMAGE_SAVER}
FROZEN={FUSION,CAPTURE,SAVER,RELEASE_STACK,RELEASE_SHADER,MATCHER,PREFS}
EXCLUDED={
 'app/src/main/java/com/hinnka/mycamera/raw/RawDemosaicProcessor.kt',
 'app/src/main/java/com/hinnka/mycamera/raw/RawTilePlanner.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcSpatialRgbChromaPostprocessor.kt',
}

def norm(s:str)->str: return s.replace('\r\n','\n').replace('\r','\n')
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root:Path): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
def load(name:str,p:Path):
    spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m); return m

def active_spatial_block(fusion:str)->str:
    marker='IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE'
    a=fusion.find(marker); assert a>=0, '26521 active Iris owner marker missing'
    b=fusion.find('        return GlesMgcRawSpatialStacker(',a); assert b>a, 'Spatial fallback boundary missing'
    return fusion[a:b]

def shader_block(text:str,name:str,next_name:str)->str:
    a=text.find(f'    val {name} = """\n'); b=text.find(f'    val {next_name} = """\n',a+1)
    assert a>=0 and b>a, name+' shader block missing'
    return text[a:b]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True,type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--apply',required=True,type=Path); ap.add_argument('--patch',required=True,type=Path); ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args(); base=ns.base.resolve(); cand=ns.candidate.resolve(); bf,cf=files(base),files(cand)
    mod=load('a26522',ns.apply.resolve()); expected=mod.expected_map(base)
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])}
    assert changed==EXPECTED_CHANGED, f'26522 runtime delta drift extra={sorted(changed-EXPECTED_CHANGED)} missing={sorted(EXPECTED_CHANGED-changed)}'
    assert set(expected)==EXPECTED_CHANGED
    for rel,new in expected.items(): assert norm(cf[rel].read_text())==new, 'transform drift '+rel
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes()
    assert 'VERSION_NAME=0.9726521' in bf[VERSION].read_text() and 'VERSION_BUILD=26521' in bf[VERSION].read_text()
    print('PASS: candidate exactly matches seven-path 26522 transform from successful 26521')

    for rel in FROZEN:
        assert bf[rel].read_bytes()==cf[rel].read_bytes(), 'frozen 26521 path drift '+rel
    for rel in EXCLUDED: assert rel not in changed, 'excluded runtime path changed '+rel
    fusion=cf[FUSION].read_text(); active=active_spatial_block(fusion)
    assert active.count('GlesIris26521SpatialRgbStacker(')==1
    assert 'GlesMgc1271ReleasedSpatialStacker(' not in active
    for tok in ('GlesMgcRawSabre','MgcSabre','ResolveSabre'):
        assert tok not in active
    print('PASS: capture, fusion routing, released c4ff control, viewfinder matcher and preferences remain byte-frozen from successful 26521')

    base_iris=bf[IRIS_STACK].read_text(); iris=cf[IRIS_STACK].read_text()
    base_shader=bf[IRIS_SHADER].read_text(); shader=cf[IRIS_SHADER].read_text()
    for tok in ('IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE','IRIS_26520_V5_FINAL_FINEST_LK_OWNER','IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW','IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME','IRIS_26520_V4_NORMAL_ONLY_REFERENCE_CONTRIBUTION','IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION'):
        assert tok in iris, 'inherited 26521 invariant missing '+tok
    assert iris.count('renderMergeDomainFlow(bayerAlignment, flow)')==2
    for tok in ('val rawSlots: IntArray','val passWindow: GlesGpuScheduler.PassWindow','online.passWindow.awaitResources(','reads = longArrayOf(rawResource)'):
        assert tok in iris, 'two-slot lifetime invariant missing '+tok
    loop_start=iris.find('            for (index in temporalFrameRange) {'); loop_end=iris.find('            val readyStrengthCapture',loop_start)
    assert loop_start>=0 and loop_end>loop_start
    temporal=iris[loop_start:loop_end]
    wait=temporal.find('online.passWindow.awaitResources('); upload=temporal.find('uploadRaw(images[index], texture, "frame $index")')
    prepare=temporal.find('val prepared = prepareTemporalFrame('); dng=temporal.find('IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION'); rgb=temporal.find('submitOrRetainRgbFrame(',dng)
    assert 0 <= wait < upload < prepare < dng < rgb, f'wait/upload/prepare/DNG/RGB order drift {wait}/{upload}/{prepare}/{dng}/{rgb}'
    print('PASS: successful-26521 alignment/rejection/two-slot RAW lifetime and same-alignment NORMAL DNG admission are preserved')

    assert 'normalStackedDngRaw16 = readBayer16(normalizedTexture)' in iris
    assert 'convertNormalizedBayer16ToSensorCode' not in iris
    assert 'sensorCodeDomain=true' not in iris
    assert 'fullRangeNormalized16=true blackLevel=0 whiteLevel=65535' in iris
    assert 'IRIS_26522_DNG_EFFECTIVE_SUPPORT_STATS' in iris
    assert 'noiseEquivalent = harmonic' in iris
    assert 'Camera2 SENSOR_NOISE_PROFILE is defined in normalized [0,1] signal units' in iris
    assert 'normalStackedDngNoiseProfile = createNormalDngNoiseProfile' in iris
    assert 'NORMAL_DNG_SUPPORT_GRID_LONG_EDGE = 128' in iris
    print('PASS: 26522 keeps the fused normalized Bayer16 result directly and measures NORMAL-only effective support')

    mb=shader_block(shader,'mergeBayer','normalDngSupportQ8')
    assert 'IRIS_26522_DNG_EFFECTIVE_SUPPORT_ACCUMULATOR' in mb
    assert 'contributionWeight * contributionWeight / 256.0' in mb
    support=shader_block(shader,'normalDngSupportQ8','normalizeBayer')
    assert 'sumW * sumW / sumW2' in support and 'accumulated.b * 256.0' in support
    # RGB reconstruction and continuous-flow geometry are not part of 26522.
    for name,next_name in (
        ('rgbChromaGuide','covariance'),
        ('convertBayerAlignment','strengthAlignment'),
        ('mergeRgb','normalizeRgb16'),
        ('normalizeRgb16','normalizeRgbFloat'),
    ):
        assert shader_block(base_shader,name,next_name)==shader_block(shader,name,next_name), '26522 illegally changed '+name
    assert 'IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT' in shader
    print('PASS: only Bayer-DNG support moments/new support shader changed; Iris RGB reconstruction and alignment shaders are byte-identical to 26521')

    saver=cf[IMAGE_SAVER].read_text()
    for tok in ('IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER','dngCreator.setBitsPerSample(16)','dngCreator.setBlackLevel(new short[]{0, 0, 0, 0})','dngCreator.setWhiteLevel(65535.0)','dngCreator.setNoiseProfile(noiseProfile)','NoiseProfileBasis=Camera2NormalizedPerFrame/HarmonicEffectiveSupport'):
        assert tok in saver, 'normalized16 writer invariant missing '+tok
    # Ordinary RAW writer stays present and source Parameters are not globally mutated.
    assert 'public static boolean saveSingleRaw(Path dngFilePath,' in saver
    assert 'parameters.whiteLevel = 65535' not in saver and 'parameters.blackLevel' not in saver[saver.find('IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER'):saver.find('public static boolean saveSingleRaw(Path dngFilePath,',saver.find('IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER'))]
    print('PASS: stacked-DNG-only writer advertises 16-bit/0/65535 and overrides NoiseProfile without changing ordinary RAW/JPEG Parameters')

    hdrx=cf[HDRX].read_text(); bridge=cf[BRIDGE].read_text(); merger=cf[MERGER].read_text(); contracts=cf[CONTRACTS].read_text()
    assert hdrx.count('ImageSaver.Util.saveNormalized16StackedRaw(')==2
    assert 'dngDomain=normalized16 blackLevel=0 whiteLevel=65535' in hdrx
    assert 'dngNoiseEquivalentSupport' in merger and 'normalStackedDngNoiseEquivalentSupport' in contracts
    assert 'stacked.normalStackedDngNoiseProfile?.size == 6' in bridge
    assert 'normalStackedDngNoiseEquivalentSupport <= inputImages.size.toFloat() + 0.01f' in bridge
    print('PASS: full-range/noise/support metadata is carried stacker -> RawStackResult -> bridge -> Hdrx -> DNG writer for RAW-only and RAW+JPEG')

    combined='\n'.join(cf[r].read_text(errors='ignore') for r in EXPECTED_CHANGED)
    for tok in ('GlesMgcRawSabre','MgcSabre','ResolveSabre','PyramidAlignment','dng_cfa_to_raw16_26520'):
        assert tok not in combined, 'forbidden architecture leaked into 26522 '+tok
    assert 'whiteLevel = 1023' not in combined and 'blackLevel = 64' not in combined
    print('PASS: 26522 introduces no Xiaomi/source-bit-depth constants, Sabre, PyramidAlignment, or old custom DNG shader')

    patch=ns.patch.resolve(); words=ns.patch_sha.read_text().strip().split(); assert words and words[0]==sha(patch)
    pt=patch.read_text()
    for rel in EXPECTED_CHANGED: assert rel in pt, 'patch missing '+rel
    for rel in FROZEN|EXCLUDED: assert rel not in pt, 'frozen/excluded path leaked into patch '+rel
    print('PASS: rollback/audit patch covers exactly seven approved 26522 runtime paths')

if __name__=='__main__': main()
