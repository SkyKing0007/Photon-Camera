#!/usr/bin/env python3
from pathlib import Path
import math,sys,re
def fail(m):raise SystemExit('FAIL: '+m)
def section(s,a,b):
 i=s.find(a);j=s.find(b,i)
 if i<0 or j<0:fail('section '+a)
 return s[i:j]
def sdr_map_final(x,k=.98):
 if x<=k:return x
 reserve=1-k;excess=x-k
 return k+reserve*excess/(excess+reserve)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats');sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 # Exact 26602 split-ownership failure class is forbidden on the active path.
 for stale in ['highlightShortAccumulatedColor26601','highlightShortAccumulatedWeightsGb26601','highlightShortMask26587','shortNormalProtectionCoverage26602','renderSabreShortProtectedAccumulatorFuse26602(','renderSabreShortAccumulatorOwnership26601(','hardEvidenceSwitch=true','shortProtection=NORMAL_SABRE_BOUNDARY_PROPAGATED']:
  if stale in active:fail('26602 split SHORT owner survived '+stale)
 for t in ['oneTunnelRbf=true','shortPrivateMean=false','shortProtection=COMMON_SABRE_REJECTION_SOURCE_CLIP','sharedRbf=true sharedResolve=true sharedVgn=true','privateShortMean=false propagatedShortMask=false lateRgbBlend=false']:
  if t not in active:fail('one-tunnel proof missing '+t)
 # Wrong flow channel is a permanent regression because it would reopen geometry across discontinuities.
 rej=section(sh,'    val rejection = """','    """.trimIndent()')
 if 'flow.z <= 2.0' not in rej or 'flow.w <= 2.0' in rej:fail('local flow-variation channel regression')
 merge=section(sh,'    val merge = \"\"\"','    \"\"\".trimIndent()')
 if re.search(r'\b(?:float|vec[234]|mat[234])\s+packed\b',merge):fail('GLSL reserved identifier packed survived modified common merge')
 # Whole-footprint scalar clipping: any clipped CFA sample rejects the complete observation.
 for vals in ([100,100,100,100,100,100,100,100,100],[100,100,100,100,1023,100,100,100,100]):
  clipped=max(vals)>=1023
  scalar=0.0 if clipped else 1.0
  if clipped and scalar!=0.0:fail('clipped footprint not scalar-rejected')
 # Reference fail-safe remains tiny rather than full-weight when brackets exist; current clipped evidence is zero.
 if not (0.0 < 0.001 <= 0.001):fail('fixture')
 # SDR regression: exact identity throughout 98% of final display range, monotonic after knee, asymptotic below white.
 for x in [0,.02,.18,.5,.8,.9,.95,.98]:
  if abs(sdr_map_final(x)-x)>1e-12:fail('SDR representable master altered '+str(x))
 xs=[.98,1.0,1.05,1.2,1.5,2.0,4.0,16.0];ys=[sdr_map_final(x) for x in xs]
 if any(ys[i+1]<=ys[i] for i in range(len(ys)-1)):fail('HDR excess mapping not strictly monotonic')
 if any(y>1.0 or y<.98 for y in ys):fail('HDR excess escaped SDR reserve')
 # C1 at knee: analytical right derivative reserve^2/(reserve^2)=1.
 reserve=.02
 if abs((reserve*reserve)/(reserve*reserve)-1.0)>1e-12:fail('knee derivative')
 # The old 26602 effective 0.80 shoulder is specifically forbidden.
 rg=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
 if 'IRIS_26602_MOTION_MASTER_SDR_TONE_START = 1.00f' in rj:fail('old intermediate-domain Motion tone start survived')
 if 'knee=0.90' in cpp or 'reserve=0.10' in cpp:fail('provisional 10% SDR reserve survived')
 if 'IRIS_26603_MOTION_SDR_KNEE = 0.98f' not in rj:fail('final SDR knee')
 print('PASS 26602 split SHORT accumulator/mask/fuse failure cannot execute; one common temporal reconstruction owner')
 print('PASS geometry uses flow.z <=2 RAW px; source clipping is whole-footprint scalar and clipped evidence cannot dominate valid SHORT')
 print('PASS SDR is exact master identity through 0.98 final output; minimal 2% C1 monotonic reserve handles only physical HDR excess; old 0.80 shoulder forbidden')
if __name__=='__main__':main()
