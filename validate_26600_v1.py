#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[x for x in """app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/version.properties""".splitlines() if x]
def fail(m):raise SystemExit('FAIL: '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):sha(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s:fail(label+' missing '+t)
def forbid(s,t,label):
 if t in s:fail(label+' stale '+t)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]); bh,ch=allh(b),allh(c); diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726600','version');need(v,'VERSION_BUILD=26600','version')
 # Every non-geometry owner from successful 26599 stays byte-identical.
 inherited=[
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
  'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
  'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
 for rel in inherited:
  if (b/rel).read_bytes()!=(c/rel).read_bytes():fail('successful-26599 inherited authority changed '+rel)
 sh=(c/CHANGED[0]).read_text(); st=(c/CHANGED[1]).read_text()
 # New boundary-consensus owner and unchanged safety tolerance.
 for t in ['IRIS_26600_BOUNDARY_CONSENSUS_SHORT_GEOMETRY','shortBoundaryGeometrySeed26600','shortBoundaryGeometryPropagate26600','shortBoundaryGeometryProbe26600',
           'if (bestSupport < 5) return false;','if (bestSupport - secondSupport < 2) return false;','return maximumDeviation <= uConsensusPixels;',
           'quadEvidence >= 3 && phaseEvidence >= 6 && meanError < uConsistencyThreshold','boundaryGeometry.z < 0.99','boundaryGeometry.w < 0.99']:
  need(sh,t,'26600 SHORT geometry')
 # Exact literal clip and 26599 effective-loss/headroom owners remain in the final mask.
 for t in ['sensorClippedPhaseCount(referenceP) >= 1','everyClippedReferencePhaseExplained(','max(predicted - reference, 0.0) / max(predicted, 0.05)',
           'secondHighestVec4(headroomLossEvidence)','severeSingleLossWeight(','oMask = clamp(effectiveHandoff, 0.0, 1.0)']:
  need(sh,t,'SHORT mask')
 # Old poisoned flow.w criterion must not survive in the active final mask body.
 mask=sh[sh.index('val shortRestoreMask26596 = """'):]
 forbid(mask,'if (flow.w > uFlowVariationPixelsThreshold) return;','active SHORT mask')
 forbid(mask,'uniform float uFlowVariationPixelsThreshold;','active SHORT mask')
 # Old fixed-radius region owner can remain historical shader text, but cannot be linked/invoked by active stacker.
 for t in ['sabreShortBoundaryGeometrySeedProgram26600','sabreShortBoundaryGeometryPropagateProgram26600','sabreShortBoundaryGeometryProbeProgram26600',
           'createSabreShortBoundaryGeometry26600(','uConsensusPixels", 2.0f','val passes = Math.addExact(gridWidth, gridHeight)',
           'IRIS_26600_SHORT_BOUNDARY_GEOMETRY','robustBoundaryGeometry=true','dng=false srEvidence=false']:
  need(st,t,'SHORT stacker')
 for t in ['sabreShortRegionSeedProgram26595','sabreShortRegionPropagateProgram26594','renderSabreShortRegionSeed26595(','renderSabreShortRegionPropagate26594(','SHORT_REGION_PROPAGATION_PASSES_26594']:
  forbid(st,t,'active stacker')
 # Whole-RGB restoration and true2x final mask consumer remain present.
 need(sh,'oColor = vec4(mix(normalRgb.rgb, restoredShort, confidence), normalRgb.a);','whole-RGB restore')
 need(st,'boundaryGeometry = shortBoundaryGeometry26600.texture','mask geometry binding')
 print('PASS exact 3-file scope; successful-26599 capture/tone/color/SR/DNG/native authorities inherited byte-identical')
 print('PASS boundary-consensus SHORT geometry replaces poisoned max-range gate without relaxing 2 RAW-pixel tolerance')
 print('PASS literal clipping + effective-loss/headroom + whole-RGB/fail-closed ownership preserved')
if __name__=='__main__':main()
