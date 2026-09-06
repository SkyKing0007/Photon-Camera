#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_26604_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):H(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def forbid(s,t,l):
 if t in s:fail(l+' stale '+t)
def section(s,a,b):
 i=s.find(a);j=s.find(b,i)
 if i<0 or j<0:fail('section '+a)
 return s[i:j]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c);diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726604','version');need(v,'VERSION_BUILD=26604','version')
 # Untouched high-risk owners must remain exact 26603 bytes.
 untouched=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/assets/shaders/motionv2/display_exposure.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java']
 for r in untouched:
  if (b/r).read_bytes()!=(c/r).read_bytes():fail('successful-26603 untouched owner changed '+r)
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();rej=section(sh,'    val rejection = """','    """.trimIndent()');merge=section(sh,'    val merge = """','    """.trimIndent()');nightmerge=section(sh,'    val mergeShadowLong26558 = """','    """.trimIndent()')
 for t in ['IRIS_26604_ONE_TUNNEL_EVIDENCE_COUNT','IRIS_26604_CONTINUOUS_ONE_TUNNEL_NORMAL_SHORT_LONG','renderSabreRejection(','renderSabreMerge(','IRIS_26604_ONE_TUNNEL_RESOLVE_AUTHORITY','temporalSupportOwner=NORMAL_SHORT_LONG dngOwner=NORMAL srDetailOwner=NORMAL']:
  need(active,t,'common tunnel')
 for stale in ['renderSabreShortProtectedAccumulatorFuse26602(','renderSabreShortAccumulatorOwnership26601(','renderSabreShortRestoreRgba16f26587(','highlightShortAccumulatedColor26601','shortNormalProtectionCoverage26602']:
  forbid(active,stale,'split SHORT owner')
 for t in ['sourceQuadHeadroomConfidence','boundaryRadiometricConfidence','flowConfidence','boundaryRisk','boundaryRadiometry','currentHeadroom','smoothstep(0.03,0.08,relativeError)','supportGate=smoothstep(1.0,3.0,supportSum)']:
  need(rej.replace(' ',''),t.replace(' ',''),'continuous bracket rejection')
 forbid(rej.replace(' ',''),'frameWeight=flow.z<=2.0?1.0:0.0','clipped reference auto trust')
 for t in ['sourceNeighborhoodConfidence','uSourceClippingPoint*0.9925','smoothstep(','frameWeight *= mix(']:need(merge,t,'continuous common RBF headroom')
 forbid(merge,'step(uSourceClippingPoint','hard common RBF clipping')
 # Night-only merge retains inherited binary guard and is deliberately not converted.
 need(nightmerge,'sourceNeighborhoodClipped','Night inherited source clip')
 for t in ['if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:need(active,t,'DNG/SR NORMAL-only')
 # Motion multiplier owner neutralized; Night path preserved after Motion return.
 de=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java').read_text();motion=section(de,'if (basePipeline.mParameters.motionV2Active) {','if (Math.abs(displayGain - 1.0f)')
 need(motion,'WorkingTexture = previousNode.WorkingTexture;','Motion display pass-through');need(motion,'imageMultiplier=false passThrough=true','Motion multiplier telemetry');forbid(motion,'useAssetProgram','Motion multiplier')
 need(de,'glProg.useAssetProgram("motionv2/display_exposure")','Night display path')
 # Manual controls consume virtual presented brightness then return to source space.
 mt=(c/'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl').read_text();mj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java').read_text()
 for t in ['brightnessTargetGain','virtualRgb=rgb*targetGain','Output = max(virtualRgb/targetGain']:need(mt,t,'manual virtual-domain parity')
 need(mj,'brightnessTargetGain','manual brightness target binding')
 # Gain map uses master target rather than forcing SDR body unity.
 gm=(c/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text();need(gm,'hdrExposureScale*(motionHdrHandoff!=0?max(displayGain,1.0e-6):1.0)','UHDR master target')
 rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();need(rj,'bodyGainUnityRequired=false','UHDR SDR ownership')
 print('PASS exact 12-file runtime scope from successful-26603 authority; untouched capture/encoder/display shader owners invariant')
 print('PASS one NORMAL+SHORT+LONG reconstruction tunnel; clipped reference cannot auto-trust SHORT; continuous whole-observation headroom + boundary radiometry active')
 print('PASS Motion display multiplier inactive; Night preserved; manual controls retain virtual presented-domain behavior; DNG/SR detail NORMAL-only')
if __name__=='__main__':main()
