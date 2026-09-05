#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[x for x in """app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/assets/shaders/motionv2/display_exposure.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/version.properties""".splitlines() if x]
TONE=[
'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
TONE_26598={
TONE[0]:'cecbb02f659f115bb1e17bc1026f2dd4fd8177c5cfdea27dd31e2a7eaf5401ea',
TONE[1]:'84b7f003e0f1ba8ce2ab53f5f4a1bd41425046a6dfb1ff39a4e7a16114d5a7be',
TONE[2]:'0d69c007097262a5ef1a27719a9d0ea0723188460bc96e81dc69f6dc65d3faf4',
TONE[3]:'6726e025fd4dd0fe1aceab1063d9d846898d628eac26ec02b87d6f2ae814f38a',
TONE[4]:'f781ee8a8881d18b4db68c40e50ba45a89e4a8669a2cc44b3a009395f71dea7e'}
RENDER_26600={'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'24962321a78fde5c85f6f18a6e203ae4d5b3802cf76cde250647564a47146525','app/src/main/assets/shaders/motionv2/render.glsl':'5836e20496094b54d60e7806209ca866e166908f74a2e133e435ecb014d01959'}
def fail(m):raise SystemExit('FAIL: '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):sha(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s:fail(label+' missing '+t)
def forbid(s,t,label):
 if t in s:fail(label+' stale '+t)
def section(s,a,b): return s[s.index(a):s.index(b,s.index(a))]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]); bh,ch=allh(b),allh(c); diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726601','version');need(v,'VERSION_BUILD=26601','version')
 # 26600 capture/DNG/scene-white/true2x detail authority stays exact where not intentionally replaced.
 inherited=[
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/assets/shaders/motionv2/render.glsl',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
  'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']
 for rel in inherited:
  if (b/rel).read_bytes()!=(c/rel).read_bytes():fail('successful-26600 inherited authority changed '+rel)
 # Exact successful-26598 rendition is intentionally restored as one coordinated owner set.
 for rel,want in TONE_26598.items():
  if sha(c/rel)!=want:fail('successful-26598 presentation parity '+rel)
 for rel,want in RENDER_26600.items():
  if sha(c/rel)!=want:fail('common render owner changed '+rel)
 de=(c/TONE[0]).read_text(); need(de,'Output = c * max(displayGain, 1.0e-6);','26598 display scalar')
 for stale in ['presentationLinearAnchor','presentationKnee','motionToneNormalization','irisMappedGuide']:
  forbid(de,stale,'26598 display scalar')
 # Exact 26600 geometry/mask sections are byte-identical even though shader file gained one owner.
 bs=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); cs=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 pairs=[('val shortBoundaryGeometrySeed26600','val shortBoundaryGeometryPropagate26600'),('val shortBoundaryGeometryPropagate26600','val shortBoundaryGeometryProbe26600'),('val shortBoundaryGeometryProbe26600','val shortRestoreMask26596'),('val shortRestoreMask26596','val shortRestoreMaskProbe26590')]
 for a,z in pairs:
  if section(bs,a,z)!=section(cs,a,z):fail('successful-26600 geometry/mask bytes changed '+a)
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 # New single-reconstruction SHORT owner.
 for t in ['IRIS_26601_SHORT_COMMON_SABRE_PRE_RESOLVE','highlightShortAccumulatedColor26601','highlightShortAccumulatedWeightsGb26601','calibration = calibration,','IRIS_26601_SHORT_SINGLE_RECONSTRUCTION_AUTHORITY','renderSabreShortAccumulatorOwnership26601(','shortGuideOwner=COMMON_SABRE_PRE_RESOLVE_VGN','IRIS_26601_LATE_RGB_SHORT_OWNER_RETIRED','sabreShortRestoreRgba16fProgram26587 = 0']:
  need(st,t,'26601 common SHORT owner')
 owner=section(cs,'val shortAccumulatorOwnership26601','val shortRestoreRgba16f26587')
 for t in ['float shortOwner = (evidence > 0.0 && minimumShortWeight > 1.0e-7) ? 1.0 : 0.0;','oColorAndRWeight = mix(normalColor, shortColor, shortOwner);','oWeightsGb = mix(normalGb, shortGb, shortOwner);']:
  need(owner,t,'26601 homogeneous owner')
 # Active pipeline can no longer independently Resolve/VGN SHORT or blend NORMAL/SHORT RGB.
 active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 for stale in ['resolveSabreShortNativeExposure26587(','renderSabreShortRestoreRgba16f26587(','highlightShortTexture26587','EXACT_NATIVE_RGBA16F_RESTORE']:
  forbid(active,stale,'active 26601 pipeline')
 # SHORT still excluded from temporal support/DNG/high-frequency true2x detail; LONG remains common.
 for t in ['if (frame.role == RawBurstFrameRole.SHADOW_LONG) {','shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','shortEvidence=false shortUnifiedGuide=','srDetailOwner=NORMAL_ONLY']:
  need(active,t,'role invariance')
 # 26600 geometry safety/tolerance and final mask remain active.
 for t in ['createSabreShortBoundaryGeometry26600(','uConsensusPixels", 2.0f','boundaryGeometry = shortBoundaryGeometry26600.texture','actualSensorClipBypass=true','shortHeadroomThreshold=0.90']:
  need(st,t,'26600 geometry inherited')
 print('PASS exact 8-file scope; successful-26600 capture/DNG/sceneWhite/role ownership preserved')
 print('PASS SHORT joins homogeneous reference-exposure Sabre evidence before one Resolve/VGN; late two-RGB authority retired')
 print('PASS LONG remains common Sabre evidence; true2x high-frequency evidence remains NORMAL-only while 1x/2x share unified HDR guide')
 print('PASS exact successful-26598 SDR/UHDR presentation owner restored; successful common MotionV2Render bytes unchanged')
if __name__=='__main__':main()
