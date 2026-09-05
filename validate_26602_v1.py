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
 i=s.index(a);return s[i:s.index(b,i)]
def function_section(s,name,next_name):return section(s,'    private fun '+name,'    private fun '+next_name)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c);diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726602','version');need(v,'VERSION_BUILD=26602','version')
 # Untouched architecture must remain exact successful 26601 authority.
 inherited=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/assets/shaders/motionv2/display_exposure.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']
 for rel in inherited:
  if (b/rel).read_bytes()!=(c/rel).read_bytes():fail('successful-26601 inherited authority changed '+rel)
 bs=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();cs=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 # Exact successful 26600 geometry/effective-loss authority retained.
 pairs=[('val shortBoundaryGeometrySeed26600','val shortBoundaryGeometryPropagate26600'),('val shortBoundaryGeometryPropagate26600','val shortBoundaryGeometryProbe26600'),('val shortBoundaryGeometryProbe26600','val shortRestoreMask26596'),('val shortRestoreMask26596','val shortRestoreMaskProbe26590')]
 for a,z in pairs:
  if section(bs,a,z)!=section(cs,a,z):fail('successful-26600 geometry/effective-loss bytes changed '+a)
 bst=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 # LONG already had NORMAL protection. Preserve the actual implementation, not only telemetry.
 for fn,nxt in [('renderSabreShadowLongCoverage','maxSabreAccumulatedWeight'),('sabreExposureDurationRobustness','renderSabreRejection')]:
  if function_section(bst,fn,nxt)!=function_section(st,fn,nxt):fail('LONG protected owner changed '+fn)
 for t in ['renderSabreRejection(','renderDilation(reverseWeight, frameWeight)','shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG','IRIS_26602_LONG_FULL_NORMAL_PROTECTION photometric=true unblocker=true','durationRobustness']:
  need(active,t,'LONG full protection')
 # SHORT must consume NORMAL-equivalent Sabre protection and cannot use identity/hard switch.
 for t in ['IRIS_26602_SHORT_FULL_NORMAL_SABRE_PROTECTION','createSabreShortProtection26602(','frameWeight = frameWeight','normalCoverage = shortNormalProtectionCoverage26602','renderSabreShortProtectedMask26602(','weight = highlightShortMask26587','useFrameWeight = true','renderSabreShortProtectedAccumulatorFuse26602(','hardEvidenceSwitch=false','sabrePhotometricGate=true','unblockerGate=true','dilationFrameWeight=true','normalCoverageGate=true','bayerQuadCoherent=true','sharedResolve=true sharedVgn=true lateRgbBlend=false']:
  need(active,t,'26602 SHORT protected owner')
 short_block=section(active,'if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) {','} else {')
 forbid(short_block,'identityWeight','SHORT identity protection')
 forbid(active,'renderSabreShortAccumulatorOwnership26601(','SHORT hard accumulator owner')
 for stale in ['resolveSabreShortNativeExposure26587(','renderSabreShortRestoreRgba16f26587(','highlightShortTexture26587']:
  forbid(active,stale,'late SHORT RGB authority')
 need(st,'sabreShortAccumulatorOwnershipProgram26601 = 0','hard owner unlinked')
 # New shaders enforce non-invented boundary protection + Bayer-quad coherence + whole-RGB scalar fusion.
 for name in ['shortProtectionSeed26602','shortProtectionPropagate26602','shortProtectedMask26602','shortProtectedAccumulatorFuse26602']:
  need(cs,'val '+name,'26602 shader owner')
 prop=section(cs,'val shortProtectionPropagate26602','val shortProtectedMask26602');need(prop,'weakest = min(weakest, w);','non-increasing protection');need(prop,'support >= 1 ? weakest : 0.0','propagation requires measured trust');need(prop,'length(rawFlow(g) - centerFlow) > uConsensusPixels','2px coherent geometry')
 mask=section(cs,'val shortProtectedMask26602','val shortProtectedAccumulatorFuse26602')
 for t in ['min(candidateAt(q), candidateAt(q + ivec2(1, 0)))','min(candidateAt(q + ivec2(0, 1)), candidateAt(q + ivec2(1, 1)))','oMask = clamp(candidate * protectionGate, 0.0, 1.0);']:
  need(mask,t,'Bayer-quad coherent mask')
 fuse=section(cs,'val shortProtectedAccumulatorFuse26602','val shortRestoreRgba16f26587')
 for t in ['vec3 fusedMean = mix(normalMean, shortMean, clamp(confidence, 0.0, 1.0));','oColorAndRWeight = vec4(fusedMean * normalWeight, normalColor.a);','oWeightsGb = normalGb;']:
  need(fuse,t,'single whole-RGB protected fusion')
 # SR/DNG physical ownership remains NORMAL-only; bracket radiometry shares pre-Resolve result.
 for t in ['if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','dngOwner=NORMAL srDetailOwner=NORMAL']:
  need(active,t,'SR/DNG invariance')
 # UHDR master rendition -> SDR parity: body untouched for Motion in 1x and true2x CPU/GPU.
 rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();rg=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
 for t in ['IRIS_26602_MOTION_MASTER_SDR_TONE_START = 1.00f','HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE','IRIS_26602_SDR_UHDR_MASTER_PARITY','bodyGainUnity=true','oneMasterRendition=true']:
  need(rj,t,'1x SDR/UHDR master parity')
 for t in ['iris26592MotionHdrHandoff!=0 ? iris26602MotionMasterToneStart : 0.50','float start=iris26592MotionHdrHandoff!=0 ? iris26602MotionMasterToneStart : 0.50;']:
  # tolerate spacing by stripping once below
  if t.replace(' ','') not in rg.replace(' ',''):fail('render tone start missing '+t)
 for t in ['const float start=p.motionHdrHandoff?1.0f:0.50f;','float start=uMotionHdrHandoff!=0?1.0:0.50;']:
  need(cpp,t,'true2x SDR/UHDR master parity')
 # Night must still use the 0.50 shoulder, and no capture/exposure policy changed.
 need(rg,': 0.50','Night tone start');need(cpp,':0.50f','Night true2x tone start')
 print('PASS exact six-file scope; successful-26601 capture/exposure/color/DNG owners preserved')
 print('PASS SHORT consumes NORMAL Sabre rejection/unblocker/dilation + NORMAL-only coverage, propagates trust only through frozen 26600 geometry, Bayer-quad coherent, no identity/hard-switch owner')
 print('PASS LONG full NORMAL protection implementation preserved; DNG and true2x detail remain NORMAL-only')
 print('PASS Motion SDR derives from UHDR master grade through body/midtones in 1x + true2x CPU/GPU; Night tone path preserved')
if __name__=='__main__':main()
