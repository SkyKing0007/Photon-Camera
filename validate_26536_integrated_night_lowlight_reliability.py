#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib
from pathlib import Path

RUNTIME_FILES = [
    'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
]

def fail(msg: str): raise SystemExit('FAIL: '+msg)
def req(cond: bool, msg: str):
    if not cond: fail(msg)
def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest(root: Path):
    d={}
    for f in (root/'app/src/main').rglob('*'):
        if f.is_file(): d[str(f.relative_to(root))]=sha(f)
    return d

def validate(base: Path, cand: Path):
    mb,mc=manifest(base),manifest(cand)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    req(changed==sorted(RUNTIME_FILES), 'changed-file allowlist mismatch: '+repr(changed))

    def text(rel):
        p=cand/rel; req(p.is_file(),'missing '+rel); return p.read_text()

    bridge=text(RUNTIME_FILES[-1])
    for token in (
        'IRIS_26536_ADAPTIVE_MGC_LUMA_RECOVERY',
        'adaptiveLowLightFloor',
        'lumaSnrRisk',
        'textureClassifier=false',
        'structureAuthority=MGC_PECAN_OUTLIER_REVERT_SPATIAL_STRENGTH',
        'lumaStrengthScale = lumaScale',
        'chromaStrengthScale = chromaScale',
        'IRIS_26535_NATIVE_SPATIAL_RELIABILITY',
        'IRIS_26535_SR_RELIABILITY_GATE',
    ): req(token in bridge,'bridge contract missing '+token)
    req('val lumaScale = 0f' not in bridge,'forced-zero MGC luma survived')
    req('flatAreaGate' not in bridge and 'flatnessGate' not in bridge,'naive flat-area classifier code forbidden')
    req('MgcMergeMethod.SPATIAL_RGB' in bridge and 'MgcSpatialOutputMode.RGB' in bridge,
        'Spatial RGB production authority missing')

    shader=text(RUNTIME_FILES[0])
    for token in (
        'IRIS_26536_RT_FALSE_COLOR_CONTEXT',
        'lowReliabilityGate',
        'contextGate=max(clipGate,lowReliabilityGate);',
        'activation=edgeGate*outlierGate*contextGate;',
        'amountCap=mix(0.32,0.78,clipGate);',
        'Output=c+delta*safeAmount;',
    ): req(token in shader,'false-color shader contract missing '+token)
    req('clipGate*edgeGate*outlierGate' not in shader,'old mandatory clipping gate survived')
    low=shader.lower()
    for forbidden in ('magenta','purple','orange','huegate'):
        req(forbidden not in low,'hue-targeted false-color logic forbidden: '+forbidden)

    hjava=text('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java')
    req('nearClipRequired=false' in hjava and 'lowReliabilityContext=true' in hjava,
        'highlight reliability telemetry not updated')
    req('lumaPreserved=true hueTargeting=false' in hjava,'luma/hue invariant missing')

    jin=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java')
    for token in (
        'IRIS_26536_JIN_RESILIENT_NEURAL_OWNER',
        'ensureNnapiSession()', 'ensureCpuSession()', 'IRIS_26536_JIN_CPU_RETRY',
        'IRIS_26536_JIN_SKIPPED_SAVE_MGC_BASE',
        'photonFallback=false', 'adrcFallback=false', 'singleFrameFallback=false',
        'disableNnapiAfterFailure', 'Log.e(TAG,"IRIS_26536_JIN_RUN provider=NNAPI success=false',
    ): req(token in jin,'Jin resilience contract missing '+token)
    req('26533 Iris Night neural inference failed closed' not in jin,'old Jin fail-closed exception survived')
    req('throw new IllegalStateException("26533 Iris Night neural inference failed closed"' not in jin,
        'generic Jin fail-closed throw survived')

    hdr=text('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    for token in (
        'PhotonMotionMgc1271Bridge.reconstruct(',
        'pipeline.RunIrisNightRgb(rgb,p)',
        'IRIS_26536_JIN_OPTIONAL_FINISH_ONLY',
        'IRIS_26536_NIGHT photonNight=false mgcSpatialRgb=true spatialBayer=false rcd=false',
    ): req(token in hdr,'Night shared Spatial-RGB contract missing '+token)
    for forbidden in ('RunIrisNightBayer(rgb,p)', 'IrisNightMgc1271Bridge.reconstruct('):
        req(forbidden not in hdr,'forbidden Night reconstruction authority survived: '+forbidden)

    display=text('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java')
    req('duplicateHeadroomLimiter=false' in display,'presentation non-duplication telemetry missing')
    req('headroomOwner=MotionV2RenderCommonRgbScalar' in display,'render headroom ownership telemetry missing')

    # Lock the already-integrated bjzhou-derived Iris work against accidental duplicate/replacement.
    locked=[
        'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt',
        'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
        'app/src/main/assets/shaders/motionv2/render.glsl',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
    ]
    for rel in locked:
        req((base/rel).is_file() and (cand/rel).is_file(),'locked file missing '+rel)
        req(sha(base/rel)==sha(cand/rel),'locked prior feature changed unexpectedly: '+rel)

    vgn=(cand/locked[2]).read_text()
    for token in ('IRIS_26529_SPATIAL_RGB_CHROMA_REWRITE_OWNER','IIR1','IIR3','IRIS_26532_IIR_CHROMA_EDGE_RESET'):
        req(token in vgn,'existing VGN/IIR ownership missing '+token)
    stack=(cand/locked[0]).read_text()
    for token in ('IRIS_26530_V1_3_PROPAGATED_OUTPUT_SNR','alignmentTexture = prepared.bayerAlignmentTexture','MGC Spatial RGB IIR-to-float handoff'):
        req(token in stack,'already-integrated post-c317 Spatial behavior missing '+token)
    strength=(cand/locked[3]).read_text()
    req('REJECTED_DENOISE_MULTIPLIER = 1f' in strength,
        'already-integrated Spatial strength multiplier fix missing')
    render=(cand/locked[5]).read_text()
    for token in ('IRIS_26491_EXTENDED_LINEAR_CHROMA_PRESERVING_HIGHLIGHT_COMPRESSION','return rgb/max(peak,1.0e-6);'):
        req(token in render,'existing common-RGB headroom authority missing '+token)

    # Base/current version may be pre-increment or versioned inside Gate 4.
    bver=(base/'app/version.properties').read_text(); cver=(cand/'app/version.properties').read_text()
    req('VERSION_NAME=0.9726535' in bver and 'VERSION_BUILD=26535' in bver,'base is not exact 26535 version')
    req(('VERSION_NAME=0.9726535' in cver and 'VERSION_BUILD=26535' in cver) or
        ('VERSION_NAME=0.9726536' in cver and 'VERSION_BUILD=26536' in cver),
        'candidate version is neither preversion 26535 nor final 26536')

    print('PASS: 26536 exact six-file runtime allowlist')
    print('PASS: adaptive low-light luma uses MGC noise/structure authority; no flat-area classifier')
    print('PASS: RawTherapee-derived false-color correction broadens via low reliability without hue targeting')
    print('PASS: Night keeps one MGC Spatial-RGB reconstruction and Jin becomes resilient finishing only')
    print('PASS: existing VGN/IIR, post-c317 Spatial fixes, DNG/SR/UHDR and common-RGB headroom remain locked')

def self_test():
    req(len(RUNTIME_FILES)==6,'runtime file list drift')
    req(len(set(RUNTIME_FILES))==6,'runtime file duplicates')
    print('PASS: 26536 validator self-test')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test(); return
    req(a.base and a.candidate,'--base and --candidate required')
    validate(Path(a.base).resolve(),Path(a.candidate).resolve())
if __name__=='__main__': main()
