#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,re
from pathlib import Path

CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
FUSION='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
CONTRACTS='app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'
RELEASE_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
RELEASE_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'
IRIS_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
IRIS_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
MATCHER='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
PREFS='app/src/main/res/xml/preferences.xml'
VERSION='app/version.properties'
EXPECTED_CHANGED={CAPTURE,SAVER,HDRX,MERGER,BRIDGE,FUSION,CONTRACTS,IRIS_STACK,IRIS_SHADER}
FROZEN={RELEASE_STACK,RELEASE_SHADER,MATCHER,PREFS}
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
    a=fusion.find(marker); assert a>=0, '26521 V5 active owner marker missing'
    b=fusion.find('        return GlesMgcRawSpatialStacker(',a); assert b>a, 'Spatial fallback boundary missing'
    return fusion[a:b]

def shader_block(text:str,name:str,next_name:str)->str:
    a=text.find(f'    val {name} = """\n'); b=text.find(f'    val {next_name} = """\n',a+1)
    assert a>=0 and b>a, name+' shader block missing'
    return text[a:b]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True,type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--apply26520-v4',required=True,type=Path); ap.add_argument('--apply26520-v5',required=True,type=Path)
    ap.add_argument('--apply26521-v4',required=True,type=Path); ap.add_argument('--apply26521-v5',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path); ap.add_argument('--patch-sha',required=True,type=Path); ns=ap.parse_args()
    base=ns.base.resolve(); cand=ns.candidate.resolve(); bf,cf=files(base),files(cand)
    m21=load('a26521v5',ns.apply26521_v5.resolve())
    expected=m21.expected_map(base,ns.apply26520_v5.resolve(),ns.apply26520_v4.resolve(),ns.apply26521_v4.resolve())
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])}
    assert changed==EXPECTED_CHANGED, f'26521 V5 runtime delta drift extra={sorted(changed-EXPECTED_CHANGED)} missing={sorted(EXPECTED_CHANGED-changed)}'
    assert set(expected)==EXPECTED_CHANGED, f'expected-map drift {sorted(set(expected)^EXPECTED_CHANGED)}'
    for rel,new in expected.items(): assert norm(cf[rel].read_text())==new, 'transform drift '+rel
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes() and 'VERSION_BUILD=26519' in bf[VERSION].read_text()
    print('PASS: candidate exactly matches nine-path 26521 V5 transform from successful 26519')

    for rel in FROZEN:
        assert bf[rel].read_bytes()==cf[rel].read_bytes(), 'frozen control drift '+rel
    assert 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' in cf[RELEASE_STACK].read_text()
    assert 'IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR' not in cf[RELEASE_STACK].read_text()
    assert 'IRIS_26520_V5_FINAL_FINEST_LK_OWNER' not in cf[RELEASE_STACK].read_text()
    assert 'IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT' not in cf[RELEASE_SHADER].read_text()
    assert 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' in cf[MATCHER].read_text()
    print('PASS: original successful-26519 released c4ff stacker/shaders remain byte-for-byte frozen as dormant A/B control')

    cap=cf[CAPTURE].read_text(); saver=cf[SAVER].read_text(); hdrx=cf[HDRX].read_text(); bridge=cf[BRIDGE].read_text(); fusion=cf[FUSION].read_text()
    assert 'MOTION_26520_FROZEN_METADATA_GRACE_MS = 180L' in cap
    assert 'iris26486ReadyNow < mMotionTopUpMinimumFrames' in cap and 'actualCount < mMotionTopUpMinimumFrames' in cap
    assert 'batch.frames.isEmpty()' in saver
    assert len(re.findall(r'PhotonMotionMgc1271Bridge\.reconstruct\s*\(',hdrx))==1 and not re.search(r'MotionV2CfaReconstruction\.reconstruct\s*\(',hdrx)
    assert 'iris26520ExpectedNormalFrames = images.size()' in hdrx and 'sameAdmittedNormalPopulation=true' in hdrx
    assert 'outputMode = MgcSpatialOutputMode.RGB' in bridge and 'mergeMethod = MgcMergeMethod.SPATIAL_RGB' in bridge
    active=active_spatial_block(fusion)
    assert active.count('GlesIris26521SpatialRgbStacker(')==1 and 'GlesMgc1271ReleasedSpatialStacker(' not in active
    assert 'SABRE' not in active and 'MgcSabre' not in active
    print('PASS: V4 capture/DNG policy survives; active SPATIAL_RGB route is uniquely the Iris V5 owner')

    iris=cf[IRIS_STACK].read_text(); shader=cf[IRIS_SHADER].read_text(); contracts=cf[CONTRACTS].read_text(); merger=cf[MERGER].read_text()
    for tok in ('IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER','IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE','IRIS_26520_V5_FINAL_FINEST_LK_OWNER','IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW','IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME','IRIS_26520_V4_NORMAL_ONLY_REFERENCE_CONTRIBUTION','IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION','IRIS_26520_V4_NORMAL_ONLY_DNG_READY'):
        assert tok in iris, 'Iris stack missing inherited semantic '+tok
    assert iris.count('renderMergeDomainFlow(bayerAlignment, flow)')==2
    assert 'renderConvertedAlignment(alignment, flow)' not in iris
    assert 'targetGridMin = MERGE_ALIGNMENT_GRID_MIN' not in iris and 'MERGE_ALIGNMENT_GRID_MIN' not in iris
    for tok in ('val rawSlots: IntArray','val passWindow: GlesGpuScheduler.PassWindow','rawSlots = intArrayOf(reusableRawTexture, secondRawTexture)','online.passWindow.awaitResources(','reads = longArrayOf(rawResource)'):
        assert tok in iris, 'Iris two-slot RAW lifetime missing '+tok
    assert 'frame.role == RawBurstFrameRole.NORMAL' in iris and 'weightTexture = prepared.weightTexture' in iris and 'outputExposureScale = 1f' in iris
    loop_start=iris.find('            for (index in temporalFrameRange) {')
    loop_end=iris.find('            val readyStrengthCapture',loop_start)
    assert loop_start>=0 and loop_end>loop_start, 'Iris temporal merge loop missing/ambiguous'
    temporal=iris[loop_start:loop_end]
    wait_pos=temporal.find('online.passWindow.awaitResources(')
    upload_pos=temporal.find('uploadRaw(images[index], texture, "frame $index")')
    prepare_pos=temporal.find('val prepared = prepareTemporalFrame(')
    dng_pos=temporal.find('IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION')
    rgb_pos=temporal.find('submitOrRetainRgbFrame(',dng_pos)
    assert 0 <= wait_pos < upload_pos < prepare_pos < dng_pos < rgb_pos, (
        'Iris temporal RAW lifetime order must be wait -> upload -> prepare -> DNG -> RGB; '
        f'got wait={wait_pos} upload={upload_pos} prepare={prepare_pos} dng={dng_pos} rgb={rgb_pos}'
    )
    contribute_start=iris.find('    private fun contributeOnlineRgbFrame(')
    contribute_end=iris.find('    private fun finishOnlineRgbMerge(',contribute_start)
    assert contribute_start>=0 and contribute_end>contribute_start, 'Iris online RGB contribution function missing'
    contribute=iris[contribute_start:contribute_end]
    begin_pos=contribute.find('accumulator.passWindow.beginPass(')
    draw_pos=contribute.find('renderRgbFrameContribution(',begin_pos)
    end_pos=contribute.find('accumulator.passWindow.endPass()',draw_pos)
    assert 0 <= begin_pos < draw_pos < end_pos, 'Iris RAW resource fence must wrap each online RGB band draw'
    assert 'normalStackedDngRaw16' in contracts and 'stackedDngRaw16' in merger
    print('PASS: Iris owner inherits identical corrected alignment/rejection/two-slot lifecycle and NORMAL-only DNG sidecar')

    for tok in ('IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_MATH','IRIS_26521_V4_DIRECTIONAL_GREEN','IRIS_26521_V4_ROBUST_SPATIAL_KERNEL','IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE','IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT','IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE'):
        assert tok in shader, 'Iris shader semantic missing '+tok
    cb=shader_block(shader,'convertBayerAlignment','strengthAlignment')
    assert 'vec2 flow = resampledFlow(sourceGrid)' in cb and 'mix(flow00, flow10, fraction.x)' in cb
    assert 'cancelInterpolation' not in cb and 'uInterpolationFlowTolerance' not in cb and 'uAlignmentToBayerQuads' not in cb
    mb=shader_block(shader,'mergeBayer','normalizeBayer'); assert 'cancelInterpolation' in mb
    print('PASS: Iris RGB math remains the only A/B imaging fork; continuous alignment transport and native merge gate are shared with 26520 V5')

    combined=iris+'\n'+shader
    for tok in ('MgcRawProcessorPipeline','GlesMgcRawSabre','GlesMgcRawSabreProcessor','GlesMgcRawSabreShaders','MgcSabre','ResolveSabre','MgcSpatialMergeTuning'):
        assert tok not in combined, 'Sabre/post-c4ff architecture leaked into Iris owner '+tok
    for tok in ('GlesMgcSpatialRgbChromaPostprocessor','greenDirectionMoment'):
        assert tok not in combined, 'deferred later chroma/IIR work leaked into 26521 V5 '+tok
    for rel in EXCLUDED: assert rel not in changed, 'excluded runtime path changed '+rel
    for tok in ('dng_cfa_to_raw16_26520','iris_fused_bayer_rgb_26521','PyramidAlignment'):
        assert tok not in '\n'.join(cf[r].read_text(errors='ignore') for r in EXPECTED_CHANGED), 'legacy/V3 token '+tok
    print('PASS: no Sabre, later RawTilePlanner/chroma-IIR, old CFA/Wronski hybrid, or PyramidAlignment entered V5')

    patch=ns.patch.resolve(); words=ns.patch_sha.read_text().strip().split(); assert words and words[0]==sha(patch)
    pt=patch.read_text()
    for rel in EXPECTED_CHANGED: assert rel in pt, 'patch missing '+rel
    for rel in FROZEN|EXCLUDED: assert rel not in pt, 'frozen/excluded path leaked into patch '+rel
    print('PASS: rollback/audit patch covers exactly nine approved 26521 V5 runtime paths')

if __name__=='__main__': main()
