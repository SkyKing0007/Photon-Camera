#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_26606_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
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
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726606','version');need(v,'VERSION_BUILD=26606','version')
 # Critical successful-26605 owners that 26606 is forbidden to change.
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
  if (b/r).read_bytes()!=(c/r).read_bytes():fail('successful-26605 untouched owner changed '+r)
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 rej=section(sh,'    val rejection = """','    """.trimIndent()')
 need(rej,'float localFlowVariation = flow.z;','measurable NORMAL rejection normalized flow owner')
 forbid(rej,'flow.w','measurable NORMAL rejection must not consume SHORT residual')
 forbid(rej,'uBracketAwareClipping','retired duplicate clipped-reference rejection owner')
 need(rej,'float weight = min(1.0 - unblocker, frameWeight);','ordinary Sabre rejection')
 conv=section(sh,'    val convertAlignmentSparse = """','    """.trimIndent()')
 for t in ['vec2 flowRangeBayerQuads = maximumFlow - minimumFlow;','float localFlowVariation = length(normalizedRange);','float localAffineResidualRawPixels = 4.0;','horizontalPrediction','verticalPrediction','diagonalPredictionA','diagonalPredictionB','secondResidualBayerQuads','localAffineResidualRawPixels = 2.0 * secondResidualBayerQuads;','oFlow = vec4(uvFlow, localFlowVariation, localAffineResidualRawPixels);']:
  need(conv,t,'flow domain contract')
 anchor=section(sh,'    val shortBoundaryAnchor26606 = """','    """.trimIndent()')
 for t in ['float residualConfidence = 1.0 - smoothstep(0.50, 2.00, max(flow.w, 0.0));','float sourceConfidence = shortQuadConfidence','float referenceSecond = secondHighestReference','quadEvidence >= 3 && phaseEvidence >= 6','uConsistencyLow','uConsistencyHigh','anchorConfidence = min(regionConfidence, radiometricConfidence);']:
  need(anchor,t,'SHORT boundary anchor')
 prop=section(sh,'    val shortBoundaryPropagate26606 = """','    """.trimIndent()')
 for t in ['trust = max(trust, min(regionConfidence, trustAt','oTrust = trust;']:need(prop,t,'bottleneck propagation')
 forbid(prop,'* trustAt','multiplicative propagation')
 rescue=section(sh,'    val shortRescueWeight26606 = """','    """.trimIndent()')
 for t in ['float ordinaryWeight = texture(uOrdinaryWeight, referenceUv).r;','float referenceLoss = 1.0 - referenceHeadroom;','float rescueConfidence = min(','shortHeadroom, min(residualConfidence, boundaryTrust)','oWeight = clamp(mix(ordinaryWeight, rescueConfidence, referenceLoss), 0.0, 1.0);','oRescueOnlyWeight = clamp(rescueConfidence * referenceLoss, 0.0, 1.0);']:
  need(rescue,t,'single SHORT rescue weight owner')
 # 26605 HDR transport remains inside changed shader/stacker and must not be accidentally removed.
 for t in ['IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE','vec3 normalizedProxy = clamp(physical, 0.0, 1.0);','vec3 restored = physical + (vgn - normalizedProxy);']:
  need(sh,t,'26605 extended HDR transport')
 flt=section(sh,'    val outputTransformFloat = """','    """.trimIndent()');forbid(flt,'clamp(transformOutput(p)','physical HDR float carrier clamp')
 # Existing final exact source footprint must remain structurally identical to successful 26605 shader section.
 bsh=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 bm=section(bsh,'    val merge = """','    """.trimIndent()');cm=section(sh,'    val merge = """','    """.trimIndent()')
 if bm!=cm:fail('26605 common RBF merge/source-clipping shader changed')
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 for t in ['frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT','createSabreShortBoundaryTrust26606(','renderSabreShortRescueWeight26606(','IRIS_26606_SHORT_EFFECTIVE_COVERAGE','IRIS_26606_SHORT_CLIPPED_RESCUE_COVERAGE','highlightShortEffectiveEvidence26606','mergedFrameCount + highlightShortEffectiveEvidence26606','sourceClippedRescueCoverageCells=','actualHighlightRescue=','sourceClipGuard = highlightShortOneTunnel26604 || frame.role == RawBurstFrameRole.SHADOW_LONG']:
  need(active,t,'26606 active SHORT ownership')
 need(active,'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','SR detail NORMAL-only')
 need(active,'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','DNG NORMAL-only')
 need(st,'sabreShortBoundaryGeometrySeedProgram26600 = 0','dormant 26600 seed')
 need(st,'sabreShortProtectedAccumulatorFuseProgram26602 = 0','dormant 26602 fuse')
 need(st,'sabreShortRestoreRgba16fProgram26587 = 0','dormant late SHORT compositor')
 for t in ['sabreShortBoundaryAnchorProgram26606 = linkProgram(','sabreShortBoundaryPropagateProgram26606 = linkProgram(','sabreShortRescueWeightProgram26606 = linkProgram(']:need(st,t,'26606 active program init')
 # Motion Long / Night isolation and 26605 physical HDR carrier remain.
 for t in ['private val preserveExtendedHdrThroughVgn: Boolean = false','FLOAT_HDR_HANDOFF_PRE_VGN','POST_VGN_HDR_MASTER','val nativeHdrAuthority26601 = exportedTexture']:
  need(st,t,'26605 HDR authority')
 br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 for t in ['allowSabreShadowLong = parameters.irisNightActive','CAPTURED_BUT_EXCLUDED_FROM_NORMAL_MOTION_SABRE','COMMON_SABRE_NIGHT_SHADOW_EVIDENCE','IRIS_26606_SHORT_BRIDGE_SCHEDULE_PROOF','actualContributionOwnedBy=IRIS_26606_SHORT_EFFECTIVE_PROOF']:
  need(br,t,'bridge ownership')
 forbid(br,'IRIS_26604_SHORT_ONE_TUNNEL_ADMITTED','misleading admission proof')
 # No stale bodyGain or active legacy hue/chroma camouflage anywhere.
 for p in (c/'app/src/main').rglob('*'):
  if not p.is_file():continue
  try:s=p.read_text()
  except UnicodeDecodeError:continue
  if 'bodyGainUnity' in s:fail('stale bodyGainUnity '+str(p.relative_to(c)))
 print('PASS exact 4-file runtime scope from successful-26605 V1.1 authority; version 0.9726606/26606')
 print('PASS measurable NORMAL rejection separated from HIGHLIGHT_SHORT clipped-reference rescue; Night/NORMAL/DNG/SR/tone/HDR transport owners preserved')
 print('PASS SHORT geometry uses local affine residual + independent measurable-boundary radiometry + bottleneck propagation; exact common 3x3 source-CFA RBF veto unchanged')
 print('PASS telemetry distinguishes total source-clipped SHORT participation from clipped-reference rescue contribution')
if __name__=='__main__':main()
