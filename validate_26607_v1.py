#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_26607_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):H(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def forbid(s,t,l):
 if t in s:fail(l+' stale '+t)
def section(s,a,b):
 i=s.find(a);j=s.find(b,i+len(a))
 if i<0 or j<0:fail('section '+a)
 return s[i:j]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c);diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726607','version');need(v,'VERSION_BUILD=26607','version')
 # Successful-26606 owners outside exact 4-file scope must remain byte-identical.
 untouched=[
  'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
  'app/src/main/assets/shaders/motionv2/render.glsl',
  'app/src/main/assets/shaders/motionv2/gainmap.glsl',
  'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
  'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
 ]
 for r in untouched:
  if (b/r).read_bytes()!=(c/r).read_bytes():fail('successful-26606 untouched owner changed '+r)
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();bsh=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 # NORMAL rejection and exact production merge/source-clip owner must remain inherited from 26606.
 for nm in ['rejection','merge','copyMaskShadowLong26558','convertAlignmentSparse','outputTransformFloat','restoreExtendedHdrAfterVgn']:
  a='    val '+nm+' = """';x=section(bsh,a,'    """.trimIndent()');y=section(sh,a,'    """.trimIndent()')
  if x!=y:fail('successful-26606 inherited shader changed '+nm)
 rej=section(sh,'    val rejection = """','    """.trimIndent()')
 need(rej,'float localFlowVariation = flow.z;','measurable NORMAL rejection owner');forbid(rej,'flow.w','NORMAL rejection must not consume SHORT residual')
 # 26607 component anchor: full sparse-cell footprint, physical source headroom, effective loss, independent radiometry.
 anchor=section(sh,'    val shortComponentAnchor26607 = """','    """.trimIndent()')
 for t in [
  'vec2(float(px), float(py)) * (0.25 * cellSpanRaw);',
  'float headroomStart = max(1.0, uSourceClippingPoint * 0.9925);',
  'effectiveLossWeight(referenceNormalized, scaledShort)',
  'float signalGate = smoothstep(0.72, 0.92, predicted);',
  'smoothstep(0.05, 0.12, relativeLoss)',
  'nr >= uBoundaryCeiling',
  'float relativeError = abs(ns - nr) / max(max(nr, ns), 0.05);',
  'anchorQuadEvidence >= 4 && anchorPhaseEvidence >= 8',
  'anchorConfidence = min(',
  'componentSourceConfidence',
  'flowProof, radiometricConfidence',
 ]:need(anchor,t,'26607 component anchor')
 forbid(anchor,'uShortHeadroomThreshold','26606 premature 90-percent SHORT veto')
 # Connected propagation uses bottleneck confidence and an explicit flow discontinuity barrier.
 prop=section(sh,'    val shortComponentPropagate26607 = """','    """.trimIndent()')
 for t in ['smoothstep(4.0, 16.0, delta)','trust = max(trust, min(componentConfidence,','min(trustAt(n0), compatibleFlow(p, n0))','oTrust = trust;']:need(prop,t,'26607 component propagation')
 forbid(prop,'componentConfidence *','multiplicative component decay')
 # Rescue target combines literal sensor loss + effective near-saturation loss, then uses scalar common-path weight.
 rescue=section(sh,'    val shortRescueWeight26607 = """','    """.trimIndent()')
 for t in [
  'float literalLoss = literalLossWeight(referenceRaw, scaledShort, shortPeakRaw);',
  'float effectiveLoss = effectiveLossWeight(referenceNormalized, scaledShort);',
  'float targetLoss = clamp(max(literalLoss, effectiveLoss), 0.0, 1.0);',
  'float shortHeadroom = wholeShortHeadroom(shortPeakRaw);',
  'float componentTrust = clamp(texture(uComponentTrust, flowUv).r, 0.0, 1.0);',
  'float rescueConfidence = min(shortHeadroom, componentTrust);',
  'oWeight = clamp(mix(ordinaryWeight, rescueConfidence, targetLoss), 0.0, 1.0);',
  'oRescueOnlyWeight = clamp(rescueConfidence * targetLoss, 0.0, 1.0);',
  'oLossCandidate = targetLoss;',
 ]:need(rescue,t,'26607 rescue weight')
 forbid(rescue,'uShortHeadroomThreshold','premature SHORT veto in rescue')
 # Exact common RBF/source clipping is unchanged and remains final physical protection.
 bm=section(bsh,'    val merge = """','    """.trimIndent()');cm=section(sh,'    val merge = """','    """.trimIndent()')
 if bm!=cm:fail('26606 common RBF merge/source-clipping shader changed')
 for t in ['sourceNeighborhoodConfidence=min(','frameWeight *= mix(','uSourceClippedWeight','oColorAndRWeight','oWeightsGb']:need(cm,t,'whole-RGB final source clipping')
 # 26605/26606 extended HDR transport must remain inside changed source.
 for t in ['IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE','vec3 normalizedProxy = clamp(physical, 0.0, 1.0);','vec3 restored = physical + (vgn - normalizedProxy);']:need(sh,t,'extended HDR transport')
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 for t in [
  'frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT',
  'createSabreShortComponentTrust26607(',
  'renderSabreShortRescueWeight26607(',
  'IRIS_26607_SHORT_NORMAL_LOSS_CANDIDATES',
  'IRIS_26607_SHORT_COMPONENT_WEIGHT',
  'IRIS_26607_SHORT_TOTAL_ACCUMULATOR_ELIGIBLE_COVERAGE',
  'IRIS_26607_SHORT_TARGET_ACCUMULATOR_ELIGIBLE_COVERAGE',
  'IRIS_26607_SHORT_SEMANTIC_FUNNEL',
  'highlightShortScheduled26607',
  'highlightShortConfidenceFieldGenerated26607',
  'highlightShortTargetAccumulatorEligibleCells26607',
  'highlightShortTotalAccumulatorEligibleCells26607',
  'resolveEffective=NOT_DIRECTLY_MEASURED',
  'outputPreserved=DEVICE_IMAGE_REQUIRED',
  'sourceClipGuard = highlightShortOneTunnel26604 || frame.role == RawBurstFrameRole.SHADOW_LONG',
 ]:need(active,t,'26607 active SHORT ownership/telemetry')
 # Old 26606 rescue programs remain present only as dormant historical code; active program handles must be zero.
 for t in ['sabreShortBoundaryAnchorProgram26606 = 0','sabreShortBoundaryPropagateProgram26606 = 0','sabreShortRescueWeightProgram26606 = 0','sabreShortProtectedAccumulatorFuseProgram26602 = 0','sabreShortRestoreRgba16fProgram26587 = 0']:need(st,t,'dormant legacy SHORT owner')
 for t in ['sabreShortComponentAnchorProgram26607 = linkProgram(','sabreShortComponentPropagateProgram26607 = linkProgram(','sabreShortRescueWeightProgram26607 = linkProgram(']:need(st,t,'26607 active program init')
 need(active,'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','SR detail NORMAL-only');need(active,'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','DNG NORMAL-only')
 # Do not allow telemetry to overclaim direct accumulator/Resolve/output proof.
 forbid(active,'targetAccumulatorContributionCells=','semantic overclaim target contribution')
 forbid(active,'actualHighlightRescue=','semantic overclaim highlight rescue')
 br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 for t in ['allowSabreShadowLong = parameters.irisNightActive','CAPTURED_BUT_EXCLUDED_FROM_NORMAL_MOTION_SABRE','COMMON_SABRE_NIGHT_SHADOW_EVIDENCE','IRIS_26607_SHORT_BRIDGE_SCHEDULE_STATE','targetAccumulatorEligibilityOwnedBy=IRIS_26607_SHORT_SEMANTIC_FUNNEL','accumulatorContribution=NOT_DIRECTLY_MEASURED','resolveEffective=NOT_DIRECTLY_MEASURED','outputPreserved=DEVICE_IMAGE_REQUIRED']:need(br,t,'bridge ownership/semantic contract')
 forbid(br,'actualContributionOwnedBy=','stale contribution overclaim')
 print('PASS exact 4-file runtime scope from successful-26606 V1 authority; version 0.9726607/26607')
 print('PASS universal RAW highlight loss = literal + effective near-saturation; full flow-cell boundary radiometry + connected component trust; no scene-semantic special case')
 print('PASS common Sabre RBF/Resolve/VGN/tone/DNG/SR/Night owners preserved; old 26606/private SHORT owners dormant')
 print('PASS telemetry distinguishes scheduled/generated/accumulator-eligible from unmeasured accumulator contribution, Resolve effect and final output preservation')
if __name__=='__main__':main()
