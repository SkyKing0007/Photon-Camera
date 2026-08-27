#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, sys

REQ_FILES = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRejectionGeometry.kt',
]

def fail(msg): raise SystemExit('ERROR: '+msg)
def req(text, token, label):
    if token not in text: fail(f'{label}: missing {token!r}')
def forbid(text, token, label):
    if token in text: fail(f'{label}: forbidden {token!r}')

def audited_manifest(root: Path):
    files=[]
    src=root/'app/src/main'
    for p in src.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
        if rel.startswith('app/src/main/cpp/deps/') and rel!='app/src/main/cpp/deps/.gitignore': continue
        files.append(rel)
    for rel in ('app/version.properties','app/build.gradle'):
        if (root/rel).is_file(): files.append(rel)
    out=[]
    for rel in sorted(set(files)):
        out.append(f'{hashlib.sha256((root/rel).read_bytes()).hexdigest()}  {rel}')
    return '\n'.join(out)+'\n'

def changed(base: Path, cand: Path):
    def m(root):
        d={}
        for line in audited_manifest(root).splitlines():
            h,rel=line.split('  ',1); d[rel]=h
        return d
    a,b=m(base),m(cand)
    return sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))

def validate(base: Path, cand: Path, base_pin: Path|None=None):
    for rel in REQ_FILES:
        if not (cand/rel).is_file(): fail('candidate missing '+rel)
    actual=changed(base,cand)
    if actual != REQ_FILES:
        fail('runtime scope mismatch expected='+repr(REQ_FILES)+' actual='+repr(actual))
    if base_pin:
        if audited_manifest(base) != base_pin.read_text(): fail('base is not exact pinned V1.2 runtime authority')

    shaders=(cand/REQ_FILES[0]).read_text()
    stacker=(cand/REQ_FILES[1]).read_text()
    vgn=(cand/REQ_FILES[2]).read_text()
    sabre=(cand/REQ_FILES[3]).read_text()
    tuning=(cand/REQ_FILES[4]).read_text()
    geometry=(cand/REQ_FILES[5]).read_text()

    # Spatial merge current-MGC semantics.
    req(shaders,'bool cancelInterpolation =','Spatial merge')
    req(shaders,'if (cancelInterpolation) return baseFlow;','Spatial merge')
    forbid(shaders,'float confidence = 1.0 - smoothstep','Spatial merge')
    req(shaders,'globalPixel = clampRawPixelToPhase(globalPixel);','Spatial RAW boundary')
    forbid(shaders,'if (!rawInside(p)) continue;','Spatial RAW boundary')
    req(shaders,'vec2 warpedUv = mirrorUv(uv + flow.xy);','Spatial rejection')
    req(shaders,'outputPixel * 4 + ivec2(2)','aligned clipping geometry')
    req(shaders,'referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw','aligned clipping flow')
    req(shaders,'ivec2 tile = ivec2(gl_FragCoord.xy);','ConvertAlignment sparse transport')
    forbid(shaders,'uOutputToAlignmentScale','ConvertAlignment sparse transport')
    req(shaders,'nativeValue - localGreen','green/opponent reconstruction')
    req(shaders,'greenSum += gainedRaw(p)','green/opponent reconstruction')

    # V25 geometry centralization: RAW/4 guide/rejection, RAW/8 merge weight, covariance untouched.
    req(geometry,'ceilDivMgcV25(imageWidth, 4)','V25 geometry')
    req(geometry,'rejectionWidth = guideWidth','V25 geometry')
    req(geometry,'mergeWeightWidth = guideWidth / 2','V25 geometry')
    req(stacker,'private val rejectionGeometry = mgcSpatialRejectionGeometry(','Spatial stacker geometry')
    req(stacker,'private val guideWidth = rejectionGeometry.guideWidth','Spatial stacker geometry')
    req(stacker,'private val rejectionWidth = rejectionGeometry.rejectionWidth','Spatial stacker geometry')
    req(stacker,'private val mergeWeightWidth = rejectionGeometry.mergeWeightWidth','Spatial stacker geometry')
    req(stacker,'private val covarianceWidth = bayerQuadWidth','Figure-7 covariance stays RAW/2')

    # Current-MGC VGN semantic owner: RGB-gradient direction, no 26532 edge policy.
    req(vgn,'float rgbGradient=abs(center-first)+0.5*abs(first-second);','VGN seed')
    req(vgn,'g[i]=rgbGradient','VGN seed')
    forbid(vgn,'directionMomentAt','VGN seed')
    for marker in (
        'IRIS_26532_FOLIAGE_STRUCTURE_GUIDANCE',
        'IRIS_26532_FOLIAGE_LOCAL_MEDIAN_EDGE_GATE',
        'IRIS_26532_NO_EDGE_DESATURATION',
        'IRIS_26532_IIR_CHROMA_EDGE_RESET',
        'IRIS_26532_BLEND_EDGE_CHROMA_PROTECT',
    ): forbid(vgn,marker,'VGN old Iris policy')
    req(vgn,'dispatchSeed(assembledRgb, workA)','VGN stage order')
    req(vgn,'dispatchLocal(localClampProgram, workA, workB, "local clamp")','VGN stage order')
    req(vgn,'dispatchLocal(localMedianProgram, workB, assembledRgb, "local median")','VGN stage order')
    req(vgn,'dispatchDirectional(workB, assembledRgb, workA)','VGN stage order')
    req(vgn,'dispatchRestoreDirection(workA, workB, assembledRgb)','VGN stage order')
    req(vgn,'runIirRgb(smoothYccd, scratchYccd, coefficients.pass1, filterLuma = true, "IIR1")','VGN stage order')
    req(vgn,'runIirError(filteredError, spare, coefficients.pass1.a10, coefficients.pass1.b10)','VGN stage order')
    req(vgn,'runIirRgb(filteredYccd, finalScratch, coefficients.pass3, filterLuma = false, "IIR3")','VGN stage order')
    req(vgn,'/max(uCalculationGains,vec3(1e-6))','VGN WB inverse')
    for coeff in ('0.0674552768f','-1.14298046f','0.00580812711f','-1.86380053f','0.0331984349f','-1.61172712f'):
        req(vgn, coeff, 'VGN current coefficients')

    # Sabre must complete camera RGB through the same VGN owner before any float carrier export.
    req(sabre,'private var sabreRgbChromaPostprocessor: GlesIris26529SpatialRgbChromaPostprocessor? = null','Sabre VGN owner')
    req(sabre,'sabreRgbChromaPostprocessor = createSabreRgbChromaPostprocessor().also','Sabre VGN init')
    req(sabre,'output = chromaPostprocessor.normalizationTargetTexture()','Sabre output transform target')
    req(sabre,'chromaPostprocessor.markBandWritten(fullOutputTile)','Sabre VGN assembly')
    req(sabre,'val chromaResult = chromaPostprocessor.process(','Sabre VGN process')
    req(sabre,'renderSabreRgb16ToFloat(postprocessedUi, target)','Sabre post-VGN float carrier')
    if sabre.find('renderSabreRgb16ToFloat(postprocessedUi, target)') < sabre.find('val chromaResult = chromaPostprocessor.process('):
        fail('Sabre RGBA16F conversion occurs before VGN process')
    req(sabre,'sabreRgbChromaPostprocessor?.release()','Sabre VGN release')

    # Optional current-MGC Sabre gradient authority, preserving adaptive default.
    req(tuning,'mergeGradientThreshold: Float? = null','Sabre tuning')
    req(tuning,'resolvedGradientThreshold ?: interpolate(','Sabre tuning')
    req(sabre,'mergeGradientThreshold = coreImagingTuning.fusion.mergeGradientThreshold','Sabre tuning call')
    req(sabre,'forceReferenceColorRgb=${sabreKernelParameters.forceReferenceColorRgb}','Sabre reference-color preservation')

    print('PASS: V1.3 exact six-file scope')
    print('PASS: current-MGC Spatial merge/rejection/geometry semantics')
    print('PASS: Iris-owned current-MGC VGN semantics and stage order')
    print('PASS: Sabre Resolve -> RGBA16UI -> shared VGN -> camera RGB -> optional RGBA16F')
    print('PASS: optional Sabre mergeGradientThreshold authority with adaptive default')

def self_test():
    # Ensure scope list is stable and no duplicate paths.
    assert len(REQ_FILES)==6 and len(set(REQ_FILES))==6
    print('PASS: 26545 V1.3 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--base-pin'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.base or not a.candidate: ap.error('--base and --candidate required')
        validate(Path(a.base),Path(a.candidate),Path(a.base_pin) if a.base_pin else None)
