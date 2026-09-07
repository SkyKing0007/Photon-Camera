#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_26608_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
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
def shader(s,name): return section(s,'    val '+name+' = """','    """.trimIndent()')
def method(s,start,next_start): return section(s,start,next_start)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c);diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726608','version');need(v,'VERSION_BUILD=26608','version')
 # No unrelated publication/tone/UHDR/VGN/SR/DNG owner changes in this build.
 untouched=[
  'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
  'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
  'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
  'app/src/main/assets/shaders/motionv2/render.glsl',
  'app/src/main/assets/shaders/motionv2/gainmap.glsl',
  'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
  'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
 ]
 for r in untouched:
  if (b/r).read_bytes()!=(c/r).read_bytes():fail('successful-26607 untouched owner changed '+r)
 # Capture: existing AE sampler must remain byte-identical; dynamic HDR evidence lives only in separate dithered read-only pass.
 bc=(b/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();cc=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
 ae_start='    private void sampleMotion26380RawCaptureQuality(@NonNull Image image) {'; dyn_start='    private void sampleMotion26496SpatialHighlightEvidence('
 if method(bc,ae_start,dyn_start)!=method(cc,ae_start,dyn_start):fail('26380 AE/readiness sampler changed')
 dyn=method(cc,dyn_start,'    /*\n     * IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY')
 for t in [
  'Math.floorMod(\n                    mMotion26496SparseDitherCounter.getAndIncrement(), 9)',
  'int[] hdrHistogram = new int[MOTION_26608_HISTOGRAM_BINS];',
  'float structuredPeakSecond = 0.0f;',
  'if (cellSecond >= 0.18f) structuredBrightCells++;',
  'if (cellSecond >= 0.32f) structuredStrongBrightCells++;',
  'rawP90 >= 0.10f && rawP99 >= 0.18f',
  'dynamicRangeEv >= 1.50f',
  'shadowFraction >= 0.05f && rawP99 >= 0.16f',
  'dynamicRangeEv >= 1.75f',
  'structuredPeakSecond >= 0.25f',
  'compactDynamicRangeEv >= 2.25f',
  'structuredStrongBrightCells >= 2',
  'mMotion26608RecentHdrConflictTimestampNs = image.getTimestamp();',
  'mMotion26608CurrentHdrConflict = false;',
 ]:need(dyn,t,'26608 dithered universal HDR sampler')
 # Preserve literal physical-clipping trigger as independent reason; universal conflict augments it.
 for t in ['signal >= 0.980f','quadPhases >= 2','MOTION_26496_MIN_HIGHLIGHT_SAMPLES']:need(cc,t,'literal clipping trigger')
 trigger=section(cc,'        long hdrConflictAgeNs =','        if (!sceneRequiresShort')
 for t in [
  'boolean currentDynamicRangeTrigger = mMotion26608CurrentHdrConflict;',
  'hdrConflictAgeNs <= MOTION_26608_HDR_CONFLICT_HOLD_NS',
  'boolean universalHdrTrigger = highlightTrigger',
  '|| currentDynamicRangeTrigger',
  '|| recentDynamicRangeTrigger',
  'rawAgeNs <= 180_000_000L && universalHdrTrigger',
  'universalHdrExposureDecision=true',
  'broadHdrConflict=', 'mixedHdrConflict=', 'compactHdrConflict=',
 ]:need(trigger,t,'26608 universal SHORT decision')
 # No semantic object classifier is allowed in the new decision equations.
 decision_code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',dyn+'\n'+trigger,flags=re.S).lower()
 for word in ['cloud','window','bulb','reflection','snow','curtain']:
  if re.search(r'\b'+word+r'\b',decision_code):fail('scene-semantic classifier '+word)
 # Preview: exact current Fragment view owns the controller; detached synthetic fallback is forbidden.
 cf=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text();gl=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text();bgl=(b/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text()
 for t in ['public void bindPreviewTextureView(@NonNull GLPreview previewView)','final GLPreview previewView = mTextureView;','IRIS_26608_PREVIEW_START_ABORTED reason=no_current_fragment_view','previewView.setSurfaceTextureListener(mSurfaceTextureListener)']:need(cc,t,'current preview owner')
 forbid(cc,'mTextureView = new GLPreview(activity);','detached synthetic GLPreview')
 for t in ['this.captureController.bindPreviewTextureView(textureView);','PhotonCamera.getCaptureController() == retiringController','IRIS_26608_STALE_FRAGMENT_DESTROY_PRESERVED_CURRENT_CONTROLLER']:need(cf,t,'fragment lifecycle ownership')
 if gl!=bgl:fail('GLPreview replay implementation changed unexpectedly')
 for t in ['deliveredSurfaceTextureGeneration == replayGeneration','IRIS_26548_PREVIEW_SURFACE_REPLAY','replay=true']:need(gl,t,'inherited late-listener replay/exact-once generation')
 # Sabre: preserve common merge/coverage/normal rejection/HDR transport exactly; only SHORT component/rescue boundary shaders change.
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();bsh=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 for nm in ['rejection','merge','copyMaskShadowLong26558','convertAlignmentSparse','outputTransformFloat','restoreExtendedHdrAfterVgn']:
  if shader(bsh,nm)!=shader(sh,nm):fail('successful-26607 inherited shader changed '+nm)
 anchor=shader(sh,'shortComponentAnchor26607')
 for t in ['float connectivityFlowProof = max(','float boundaryLocalFlowProof = localResidualConfidence * mix(','geometryForComponent = max(','connectivityFlowProof, 0.85 * literalLossSeen','boundaryLocalFlowProof > 0.0','min(boundaryLocalFlowProof, radiometricConfidence)']:need(anchor,t,'protected SHORT component boundary')
 rescue=shader(sh,'shortRescueWeight26607')
 for t in ['float targetLoss = clamp(max(literalLoss, effectiveLoss), 0.0, 1.0);','float literalCore = step(','uSourceClippingPoint, secondHighest4(referenceRaw)','float localGeometry = mix(localResidualConfidence, 1.0, literalCore);','shortHeadroom, min(componentTrust, localGeometry)','oWeight = clamp(mix(ordinaryWeight, rescueConfidence, targetLoss), 0.0, 1.0);']:need(rescue,t,'protected SHORT rescue boundary')
 # Deep censored core retains 26607 component trust; non-core boundary can never be rescued above local flow residual confidence.
 forbid(rescue,'min(ordinaryWeight, rescueConfidence)','global clipped-reference veto')
 # Common one-tunnel ownership, old private owners dormant, DNG/SR detail remain NORMAL-only.
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 for t in ['frameWeight = rescuedWeight','sourceClipGuard = highlightShortOneTunnel26604 || frame.role == RawBurstFrameRole.SHADOW_LONG','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','boundaryLocalResidualRequired=true','predictorCannotOverrideLocalBoundary=true','literalCoreTwoPhaseClipBypass=true']:need(active,t,'26608 common one-tunnel ownership')
 for t in ['sabreShortBoundaryAnchorProgram26606 = 0','sabreShortBoundaryPropagateProgram26606 = 0','sabreShortRescueWeightProgram26606 = 0','sabreShortProtectedAccumulatorFuseProgram26602 = 0','sabreShortRestoreRgba16fProgram26587 = 0']:need(st,t,'dormant legacy SHORT owner')
 print('PASS exact 5-file runtime scope from successful-26607 V1 authority; version 0.9726608/26608')
 print('PASS existing 26380 AE sampler byte-identical; universal HDR SHORT decision uses separate proven 3x3 dithered RAW evidence + literal clipping fallback, no scene classifier')
 print('PASS common one-tunnel SHORT path preserved; measurable boundaries require local residual proof while two-phase censored cores retain 26607 component rescue')
 print('PASS current Fragment GLPreview ownership + inherited late-listener surface replay; detached synthetic preview and stale-controller teardown blocked')
 print('PASS tone/UHDR/VGN/Resolve/SR/DNG publication owners unchanged in 26608')
if __name__=='__main__':main()
