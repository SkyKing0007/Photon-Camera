#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
CHANGED=[x for x in """app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/version.properties""".splitlines() if x]
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):H(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s:fail(label+' missing '+t)
def forbid(s,t,label):
 if t in s:fail(label+' stale '+t)
def section(s,a,b):
 i=s.find(a)
 if i<0:fail('section start '+a)
 j=s.find(b,i)
 if j<0:fail('section end '+b)
 return s[i:j]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c);diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726603','version');need(v,'VERSION_BUILD=26603','version')
 # Untouched capture/color/UHDR bridge authority remains byte-identical to successful 26602.
 inherited=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/assets/shaders/motionv2/display_exposure.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']
 for rel in inherited:
  if (b/rel).read_bytes()!=(c/rel).read_bytes():fail('successful-26602 inherited authority changed '+rel)
 bst=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();bsh=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 # Frozen 26600 geometry/effective-loss shaders remain byte-identical; 26603 no longer makes them a second active owner.
 pairs=[('val shortBoundaryGeometrySeed26600','val shortBoundaryGeometryPropagate26600'),('val shortBoundaryGeometryPropagate26600','val shortBoundaryGeometryProbe26600'),('val shortBoundaryGeometryProbe26600','val shortRestoreMask26596'),('val shortRestoreMask26596','val shortRestoreMaskProbe26590')]
 for a,z in pairs:
  if section(bsh,a,z)!=section(sh,a,z):fail('successful-26600 geometry/effective-loss bytes changed '+a)
 # Single common NORMAL+SHORT+LONG tunnel.
 for t in ['IRIS_26603_ONE_TUNNEL_EVIDENCE_COUNT','val unifiedEvidenceCount26603 = mergedFrameCount + highlightShortFrameCount','renderSabreRejection(','renderDilation(reverseWeight, frameWeight)','IRIS_26603_ONE_TUNNEL_NORMAL_SHORT_LONG','renderSabreUnifiedBracketCoverage26603(','renderSabreMerge(','sourceClipGuard = highlightShortOneTunnel26603 || frame.role == RawBurstFrameRole.SHADOW_LONG','sourceClippedWeight = 0f','IRIS_26603_ONE_TUNNEL_RESOLVE_AUTHORITY','val resolveAccumulatedColor26603 = accumulatedColor','val resolveAccumulatedWeightsGb26603 = accumulatedWeightsGb','sharedRbf=true sharedResolve=true sharedVgn=true','temporalSupportOwner=NORMAL_SHORT_LONG']:
  need(active,t,'26603 one-tunnel owner')
 for stale in ['highlightShortAccumulatedColor26601','highlightShortAccumulatedWeightsGb26601','highlightShortMask26587','shortNormalProtectionCoverage26602','renderSabreShortProtectedAccumulatorFuse26602(','renderSabreShortAccumulatorOwnership26601(','renderSabreShortRestoreRgba16f26587(','renderSabreShortRestoreMask26595(']:
  forbid(active,stale,'retired split SHORT authority')
 # Common rejection is bracket-aware only through raw source clipping + existing Sabre geometry/unblocker.
 rej=section(sh,'    val rejection = """','    """.trimIndent()')
 for t in ['uBaseExtractedBayer','uAltExtractedBayer','uSourceClippingPoint','uBracketAwareClipping','referenceClipped','currentClipped','frameWeight=flow.z <= 2.0 ? 1.0 : 0.0;','float weight = min(1.0 - unblocker, frameWeight);']:
  need(rej,t,'common bracket-aware rejection')
 forbid(rej,'frameWeight=flow.w <= 2.0','wrong flow variation channel')
 # Common merge owns source clipping as one scalar over exact 3x3 consumed CFA footprint.
 merge=section(sh,'    val merge = """','    """.trimIndent()')
 for t in ['IRIS_26603_ONE_TUNNEL_SOURCE_CLIPPING','out float sourceNeighborhoodClipped','mat3 bayerValue = get3x3FromExtractedBayer(position);','sourceNeighborhoodClipped=max(','step(uSourceClippingPoint,bayerValue[sx][sy])','frameWeight *= uSourceClippedWeight;']:
  need(merge,t,'common source-clipped RBF')
 # DNG/SR detail remain NORMAL-only; the shared RGB support may include brackets but sidecars/detail do not.
 for t in ['if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','dngOwner=NORMAL srDetailOwner=NORMAL']:
  need(active,t,'DNG/SR ownership')
 # LONG still consumes the same common rejection+dilation and the exact inherited source-clipping coverage shader.
 need(active,'frame.role == RawBurstFrameRole.SHADOW_LONG','LONG role preserved');need(active,'durationRobustness = sabreExposureDurationRobustness','LONG duration robustness')
 if section(bsh,'    val copyMaskShadowLong26558 = """','    """.trimIndent()')!=section(sh,'    val copyMaskShadowLong26558 = """','    """.trimIndent()'):fail('inherited LONG source-clipping coverage shader changed')
 # SDR projection: preserve master through 98% of final SDR, then minimal C1 monotonic reserve for true HDR excess.
 rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();rg=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
 for t in ['IRIS_26603_MOTION_SDR_KNEE = 0.98f','HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE','IRIS_26603_MASTER_FAITHFUL_SDR','exactMasterThroughFinalSdr=']:
  need(rj,t,'1x master-faithful SDR')
 for t in ['displayGuide=y*scale','knee=clamp(iris26603MotionSdrKnee,0.50,0.98)','if(displayGuide<=knee) return y;','mappedDisplay=knee+reserve*excess/(excess+reserve)','return mappedDisplay/scale;']:
  need(rg.replace(' ',''),t.replace(' ',''),'1x final-display-domain SDR knee')
 for t in ['constexpr float scale=0.80f,knee=0.98f,reserve=0.02f;','const float scale=0.80,knee=0.98,reserve=0.02;']:
  need(cpp,t,'true2x CPU/GPU SDR parity')
 need(rg,'float start=0.50;','Night tone preserved')
 print('PASS exact six-file scope; successful-26602 capture/exposure/color/UHDR bridge owners preserved')
 print('PASS one common NORMAL+SHORT+LONG Sabre rejection/dilation/RBF/Resolve/VGN tunnel; private SHORT mask/mean/fuse inactive')
 print('PASS source clipping is exact 3x3 CFA-footprint scalar; flow.z <=2 RAW px fail-close; DNG/SR detail NORMAL-only; LONG protection retained')
 print('PASS Motion SDR preserves UHDR master through 0.98 final SDR then minimal C1 HDR-excess reserve in 1x + true2x CPU/GPU; Night preserved')
if __name__=='__main__':main()
