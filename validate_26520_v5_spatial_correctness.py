#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, re
from pathlib import Path

CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
FUSION='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'
CONTRACTS='app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'
MATCHER='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
PREFS='app/src/main/res/xml/preferences.xml'
VERSION='app/version.properties'
CHANGED={CAPTURE,SAVER,HDRX,MERGER,BRIDGE,FUSION,STACK,SHADERS,CONTRACTS}
FROZEN={MATCHER,PREFS}
EXCLUDED_RUNTIME={
 'app/src/main/java/com/hinnka/mycamera/raw/RawDemosaicProcessor.kt',
 'app/src/main/java/com/hinnka/mycamera/raw/RawTilePlanner.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcSpatialRgbChromaPostprocessor.kt',
}

def norm(s:str)->str: return s.replace('\r\n','\n').replace('\r','\n')
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root:Path): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
def load(p:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m); return m

def shader_block(text:str,name:str,next_name:str)->str:
    start=f'    val {name} = """\n'
    end=f'    val {next_name} = """\n'
    a=text.find(start); b=text.find(end,a+len(start))
    assert a>=0 and b>a, f'{name} shader block missing/ambiguous'
    return text[a:b]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--apply-v5',required=True,type=Path)
    ap.add_argument('--apply-v4',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    ns=ap.parse_args()
    base=ns.base.resolve(); cand=ns.candidate.resolve()
    v5=load(ns.apply_v5.resolve(),'a26520v5'); v4=load(ns.apply_v4.resolve(),'a26520v4')
    bf,cf=files(base),files(cand)
    changed={r for r in set(bf)|set(cf) if r not in bf or r not in cf or sha(bf[r])!=sha(cf[r])}
    assert changed==CHANGED, f'26520 V5 runtime delta drift extra={sorted(changed-CHANGED)} missing={sorted(CHANGED-changed)}'
    assert bf[VERSION].read_bytes()==cf[VERSION].read_bytes()
    assert 'VERSION_NAME=0.9726519' in bf[VERSION].read_text() and 'VERSION_BUILD=26519' in bf[VERSION].read_text()

    v4_expected=v4.expected_map(base)
    v5_expected=v5.expected_map(base,ns.apply_v4.resolve())
    assert set(v5_expected)==CHANGED, f'V5 expected-map cardinality drift {sorted(set(v5_expected)^CHANGED)}'
    assert set(v4_expected)==CHANGED-{SHADERS}, 'V4 eight-path baseline drift'
    for rel,new in v5_expected.items():
        assert norm(cf[rel].read_text())==new, 'V5 transform drift '+rel
    for rel,new in v4_expected.items():
        if rel==STACK: continue
        assert norm(cf[rel].read_text())==new, 'non-Spatial V4 behavior changed in V5: '+rel
    print('PASS: candidate = exact 26520 V4 transform plus only released Spatial stacker/shader correctness amendments')

    for rel in FROZEN:
        assert bf[rel].read_bytes()==cf[rel].read_bytes(), 'frozen 26519 path drift '+rel
    assert 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' in cf[MATCHER].read_text()
    assert 'pref_motion_viewfinder_match_strength' in cf[PREFS].read_text()
    print('PASS: 26519 viewfinder response matcher/slider remain byte-for-byte frozen')

    # V4 capture/DNG behavior must survive unchanged.
    cap=cf[CAPTURE].read_text(); saver=cf[SAVER].read_text(); hdrx=cf[HDRX].read_text()
    bridge=cf[BRIDGE].read_text(); fusion=cf[FUSION].read_text(); stack=cf[STACK].read_text()
    shaders=cf[SHADERS].read_text(); contracts=cf[CONTRACTS].read_text(); merger=cf[MERGER].read_text()
    assert 'MOTION_26520_FROZEN_METADATA_GRACE_MS = 180L' in cap
    assert 'iris26486ReadyNow < mMotionTopUpMinimumFrames' in cap and 'actualCount < mMotionTopUpMinimumFrames' in cap
    assert 'if (iris26486ReadyNow < 2)' not in cap and 'if (actualCount < 2)' not in cap
    assert 'postShutterNormalAdmission=false' in cap and 'neighborFallback=false' in cap
    assert 'batch.frames.isEmpty()' in saver and 'requires at least two normal RAW frames' not in saver
    assert len(re.findall(r'PhotonMotionMgc1271Bridge\.reconstruct\s*\(',hdrx))==1
    assert not re.search(r'MotionV2CfaReconstruction\.reconstruct\s*\(',hdrx)
    assert 'saveRAW >= 1' in hdrx and 'iris26520ExpectedNormalFrames = images.size()' in hdrx
    assert 'iris26409V2.dngStackFrames != iris26520ExpectedNormalFrames' in hdrx
    assert 'sameAdmittedNormalPopulation=true' in hdrx
    assert 'outputMode = MgcSpatialOutputMode.RGB' in bridge and 'mergeMethod = MgcMergeMethod.SPATIAL_RGB' in bridge
    assert 'exportNormalStackedDng = produceNormalStackedDng' in bridge
    assert 'stacked.normalStackedDngFrameCount == inputImages.size' in bridge
    assert 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in fusion
    assert 'exportNormalStackedDng = exportNormalStackedDng' in fusion
    assert 'IRIS_26520_V4_NORMAL_ONLY_REFERENCE_CONTRIBUTION' in stack
    assert 'IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION' in stack
    assert 'frame.role == RawBurstFrameRole.NORMAL' in stack
    assert 'weightTexture = prepared.weightTexture' in stack
    assert 'IRIS_26520_V4_NORMAL_ONLY_DNG_FINALIZE' in stack
    assert 'outputExposureScale = 1f' in stack and 'convertNormalizedBayer16ToSensorCode' in stack
    assert 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' in stack
    assert 'normalStackedDngRaw16' in contracts and 'normalStackedDngFrameCount' in contracts
    assert 'stackedDngRaw16' in merger and 'dngStackFrames' in merger
    print('PASS: V4 Frame Count/metadata grace/NORMAL-only live-MGC DNG semantics survived the V5 amendment')

    # Final b0d4 -> 1b84 Spatial alignment semantics.
    assert stack.count('IRIS_26520_V5_FINAL_FINEST_LK_OWNER')==1
    assert stack.count('IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW')>=3
    assert 'targetGridMin = MERGE_ALIGNMENT_GRID_MIN' not in stack
    assert 'MERGE_ALIGNMENT_GRID_MIN' not in stack
    assert 'upsampleL1=level-transitions-only/3-candidate' in stack
    assert stack.count('renderMergeDomainFlow(bayerAlignment, flow)')==2
    assert 'renderConvertedAlignment(alignment, flow)' not in stack
    assert 'alignment.gridWidth > 0' in stack and '"uTargetTileStride"' in stack
    assert 'alignment.tileStride * alignment.scaleToBayerQuads' in stack
    assert 'alignment.gridMin.toFloat()' in stack
    assert shaders.count('IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT')==1
    cb=shader_block(shaders,'convertBayerAlignment','strengthAlignment')
    for tok in ('vec2 resampledFlow(vec2 sourceGrid)','vec2 flow = resampledFlow(sourceGrid)','mix(flow00, flow10, fraction.x)','uTargetTileStride'):
        assert tok in cb, 'continuous finest-LK transport token missing '+tok
    for tok in ('cancelInterpolation','uInterpolationFlowTolerance','uAlignmentToBayerQuads'):
        assert tok not in cb, 'coarse-grid gate/legacy transport survived in convertBayerAlignment: '+tok
    mb=shader_block(shaders,'mergeBayer','normalizeBayer')
    assert 'cancelInterpolation' in mb and 'uInterpolationFlowTolerance' in mb
    assert 'cancelInterpolation' in shaders, 'merge-domain discontinuity protection was removed'
    print('PASS: finest LK is continuously resampled; rejection derives from the exact merge-domain flow; native merge gate remains')

    # 0cecf089 Spatial RGB RAW lifetime correction.
    for tok in (
        'IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME',
        'val rawSlots: IntArray', 'val passWindow: GlesGpuScheduler.PassWindow', 'var nextRawSlot: Int',
        'reusableRawTexture = currentRaw', 'val secondRawTexture = createTexture(',
        'rawSlots = intArrayOf(reusableRawTexture, secondRawTexture)',
        'online.passWindow.awaitResources(', 'GlesGpuScheduler.textureResource(texture)',
        'accumulator.passWindow.beginPass(', 'reads = longArrayOf(rawResource)',
        'online?.passWindow?.clearAfterCheckpoint()',
        'onlineRgbAccumulator?.passWindow?.drain("MGC Spatial merge failure")',
    ):
        assert tok in stack, 'two-slot RAW lifetime token missing '+tok
    assert 'drawBandHeight=$RGB_ONLINE_DRAW_BAND_HEIGHT rawSlots=2' in stack
    dng_pos=stack.find('IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION')
    rgb_pos=stack.find('submitOrRetainRgbFrame(',dng_pos)
    wait_pos=stack.find('online.passWindow.awaitResources(',dng_pos)
    upload_pos=stack.find('uploadRaw(images[index], texture, "frame $index")',wait_pos)
    assert dng_pos>=0 and rgb_pos>dng_pos, 'temporal DNG read must precede tracked RGB contribution in the same GL command stream'
    assert wait_pos>=0 and upload_pos>wait_pos, 'RAW slot must be awaited before overwrite upload'
    assert 'online != null -> online.rawSlots.size' in stack
    assert 'maxInFlight=$RGB_MAX_IN_FLIGHT_PASSES' in stack
    print('PASS: online Spatial RGB uses two resource-tracked RAW slots and cannot overwrite an in-flight RAW texture')

    # No post-c4ff Sabre architecture or deferred color pipeline may enter the released owner.
    released_combined=stack+'\n'+shaders
    for tok in ('MgcRawProcessorPipeline','GlesMgcRawSabre','GlesMgcRawSabreProcessor','GlesMgcRawSabreShaders','MgcSabre','ResolveSabre','MgcSpatialMergeTuning'):
        assert tok not in released_combined, 'Sabre/post-c4ff architecture leaked into released Spatial owner: '+tok
    active_start=fusion.find('IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER')
    active_end=fusion.find('        return GlesMgcRawSpatialStacker(',active_start)
    assert active_start>=0 and active_end>active_start
    active=fusion[active_start:active_end]
    assert active.count('GlesMgc1271ReleasedSpatialStacker(')==1
    assert 'SABRE' not in active and 'MgcSabre' not in active
    for rel in EXCLUDED_RUNTIME:
        assert rel not in changed, 'explicitly excluded runtime path changed: '+rel
    for tok in ('GlesMgcSpatialRgbChromaPostprocessor','IRIS_26521_V4_DIRECTIONAL_GREEN','greenDirectionMoment'):
        assert tok not in released_combined, 'deferred chroma/IIR change entered 26520 V5: '+tok
    print('PASS: released JPEG owner remains Spatial-RGB-only; Sabre, RawTilePlanner and deferred chroma/IIR work are excluded')

    patch=ns.patch.resolve(); words=ns.patch_sha.read_text().strip().split(); assert words and words[0]==sha(patch)
    pt=patch.read_text()
    for rel in CHANGED: assert rel in pt, 'patch missing '+rel
    for rel in FROZEN|EXCLUDED_RUNTIME: assert rel not in pt, 'frozen/excluded path leaked into patch '+rel
    print('PASS: rollback/audit patch covers exactly nine approved 26520 V5 runtime paths')

if __name__=='__main__': main()
