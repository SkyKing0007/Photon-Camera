#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[x for x in """app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/assets/shaders/motionv2/display_exposure.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/src/main/cpp/motionv2_jpeg444_jni.cpp
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
 b,c=map(Path,sys.argv[1:]); bh,ch=allh(b),allh(c)
 diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726599','version');need(v,'VERSION_BUILD=26599','version')
 # 26598 capture/scene-white authorities are deliberately untouched.
 for rel in [
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
  'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']:
  if (b/rel).read_bytes()!=(c/rel).read_bytes():fail('26598 inherited authority changed '+rel)
 # SHORT: exact clip owner preserved; effective loss is raw-linear, same-phase, region-trusted, whole RGB.
 sh=(c/CHANGED[0]).read_text()
 for t in ['IRIS_26599_EFFECTIVE_SENSOR_LOSS_SHORT_MASK','uEffectiveSignalFloor','uEffectiveLossStart','uEffectiveLossFull',
           'sensorClippedPhaseCount(referenceP) >= 1','everyClippedReferencePhaseExplained(',
           'max(predicted - reference, 0.0) / max(predicted, 0.05)',
           'secondHighestVec4(headroomLossEvidence)','severeSingleLossWeight(',
           'texture(uRegionTrust, referenceUv).r < 0.5','oMask = clamp(effectiveHandoff, 0.0, 1.0)',
           'if (supportPeak >= 0.995) return false;','IRIS_26599_PHASE_SCOPED_REGION_MEASURABILITY']:
  need(sh,t,'SHORT shader')
 # Do not resurrect old nonliteral bright-only handoff.
 forbid(sh,'if (referenceSecond < handoffStart || shortSecondNormalized < handoffStart)','SHORT shader')
 stack=(c/CHANGED[1]).read_text()
 for t in ['uEffectiveSignalFloor", 0.72f','uEffectiveLossStart", 0.05f','uEffectiveLossFull", 0.12f',
           'uSevereSingleReferenceFloor", 0.94f','uSevereSingleLossStart", 0.12f','uSevereSingleLossFull", 0.22f',
           'IRIS_26599_SHORT_GATE_PROBE','gateProbe=$shortGateProbe26599','fullActive=$fullActiveText26595']:
  need(stack,t,'SHORT stacker')
 # Presentation map: whole-RGB scalar, exact lower body, Motion only. No channel-specific tone.
 ds=(c/CHANGED[2]).read_text(); dj=(c/CHANGED[3]).read_text(); mat=(c/CHANGED[4]).read_text(); enc=(c/CHANGED[5]).read_text(); cpp=(c/CHANGED[6]).read_text()
 for t in ['IRIS_26599_SHARED_HDR_PRESENTATION_NORMALIZATION','motionToneNormalization == 0 || dg <= 1.0 || g <= presentationLinearAnchor',
           '(dg - 1.0) * knee * log(1.0 + x / knee)','Output = c * (mapped / guide);']:
  need(ds,t,'display shader')
 for t in ['PRESENTATION_LINEAR_ANCHOR_26599 = 0.18f','PRESENTATION_KNEE_26599 = 0.18f','iris26599MapPresentationGuide(',
           'motionV2Active','!basePipeline.mParameters.irisNightActive','wholeRgbScalar=true perChannelTone=false']:
  need(dj,t,'display owner')
 need(mat,'motionToneNormalization26599 = !iris26550Night','matcher')
 need(mat,'iris26599MapPresentationGuide(','matcher')
 for t in ['MotionV2DisplayExposure.PRESENTATION_LINEAR_ANCHOR_26599','MotionV2DisplayExposure.PRESENTATION_KNEE_26599']:
  need(enc,t,'true2x Java')
 for t in ['iris26599PresentationNormalize','!p.motionHdrHandoff||dg<=1.f','(dg-1.f)*k*std::log(1.f+x/k)',
           'irisTone(irisPresentationNormalize(irisAdaptive(p)))','uPresentationLinearAnchor','uPresentationKnee',
           'if(uMotionHdrHandoff==0||dg<=1.0)return c*dg;']:
  need(cpp,t,'true2x native')
 # Manual controls remain downstream and sceneWhite final render remains inherited.
 # Scope the proof to the Motion branch: Night intentionally has its own earlier
 # MotionV2DisplayExposure -> MotionV2Render pair and no Iris manual node.
 post=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 motion_marker=post.find('/* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */')
 motion_anchor=post.find('if (mParameters.motionV2Active) {', motion_marker)
 motion_end=post.find('add(new Bayer2Float());', motion_anchor)
 if motion_anchor < 0 or motion_end < 0: fail('Motion post-graph branch anchor missing')
 motion_post=post[motion_anchor:motion_end]
 a=motion_post.find('add(new MotionV2DisplayExposure());')
 m=motion_post.find('add(new IrisMotionToneControls(irisMotionSettings));')
 r=motion_post.find('add(new MotionV2Render());')
 if not (a>=0 and m>a and r>m):fail('Motion automatic presentation/manual/render ordering changed')
 night_anchor=post.find('if(mParameters.irisNightActive){')
 night_end=post.find('/* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */', night_anchor)
 night_post=post[night_anchor:night_end]
 na=night_post.find('add(new MotionV2DisplayExposure());'); nr=night_post.find('add(new MotionV2Render());')
 if not (na>=0 and nr>na and 'IrisMotionToneControls' not in night_post):fail('Night scalar presentation/render ordering changed')
 print('PASS exact 8-file scope + 26598 capture/scene-white authorities inherited byte-identical')
 print('PASS effective SHORT loss + phase-scoped headroom + whole-RGB region trust semantics')
 print('PASS Motion-only shared presentation normalization + manual ordering + true2x parity wiring')
if __name__=='__main__':main()
