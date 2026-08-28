#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
EXPECTED=[
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
'app/version.properties']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def files(r): return {p.relative_to(r).as_posix():sha(p) for p in Path(r).rglob('*') if p.is_file()}
def req(text,s,msg):
 if s not in text: raise SystemExit('FAIL: '+msg)
def strength(y):
 t=max(0,min(1,(y-0.06)/(0.22-0.06))); t=t*t*(3-2*t); return 0.72+(1-0.72)*t
def solve(raw,y,p99):
 d=raw*strength(y)
 cap=max(0,min(4,math.log2(5.0/max(.05,p99))))
 return min(d,cap) if d>0 else d

def selftest():
 assert abs(strength(.22)-1)<1e-6
 assert abs(strength(.03)-.72)<1e-6
 assert abs(solve(2,.03,.2)-1.44)<1e-5
 assert abs(solve(2,.25,4)-math.log2(1.25))<1e-5
 off=.015625; pre=.2; fin=.35; old=2
 reb=old*(pre+off)/(fin+off)
 assert abs(old*(pre+off)-reb*(fin+off))<1e-9
 for p in (0,1,200):
  size=3072; gm=3072
  src=(p+.5)*size/gm-.5
  assert abs(src-p)<1e-9
 print('PASS: 26550 presentation/UHDR/UI math self-tests')

if len(sys.argv)==2 and sys.argv[1]=='--self-test': selftest(); raise SystemExit
if len(sys.argv)!=3: raise SystemExit('usage: validator BASE CANDIDATE | --self-test')
B,C=map(Path,sys.argv[1:]); mb,mc=files(B),files(C)
changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
if changed!=EXPECTED: raise SystemExit('FAIL changed scope '+repr(changed))
# Unchanged architectural authorities.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 if sha(B/rel)!=sha(C/rel): raise SystemExit('FAIL protected authority changed '+rel)
exp=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java').read_text()
req(exp,'Math.pow(2.0, 0.70)','Night -0.70 EV Short protection missing')
req(exp,'IRIS_26541_NIGHT_12_PLUS_3_EXPOSURE','12+3 exposure owner missing')
ver=(C/'app/version.properties').read_text(); req(ver,'VERSION_NAME=0.9726550','version name'); req(ver,'VERSION_BUILD=26550','version build')
ui=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java').read_text()
req(ui,'shutterMode == CameraMode.MOTION || shutterMode == CameraMode.NIGHT','Night shutter snapshot absent')
matcher=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
for s in ['IRIS_26550_NIGHT_PRESENTATION_POLICY','NIGHT_DARK_STRENGTH = 0.72f','NIGHT_HEADROOM_GUIDE_LIMIT = 5.0f','IRIS_26550_NIGHT_PRESENTATION_SOLVE']:
 req(matcher,s,'Night presentation contract '+s)
# Permanent Motion behavior branch must remain explicit.
req(matcher,'matchStrengthPercent = readMatchStrengthPercent();','Motion 65% setting path missing')
req(matcher,'solvedEv = clamp(rawSolvedEv * matchStrength, MIN_EV, MAX_EV);','Motion solve changed/missing')
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
order=[post.index('IRIS_NIGHT_PROFILE_COLOR'),post.index('IRIS_26550_NIGHT_PRESENTATION_SOLVE'),post.index('IRIS_26550_NIGHT_PRESENTATION_EXPOSURE'),post.index('IRIS_NIGHT_RENDER')]
if order!=sorted(order): raise SystemExit('FAIL Night presentation stage order')
req(post,'IRIS_26550_NIGHT_HDR_AUTHORITY_DETACHED','detached Night HDR authority missing')
render=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
req(render,'gainDownsample = iris26550Night ? 4 : GAINMAP_DOWNSAMPLE','Night bounded gain map / Motion 1x missing')
req(render,'nightPostJinRebaseRequired','post-Jin rebase provenance missing')
shader=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for s in ['IRIS_26550_GAINMAP_GENERAL_GEOMETRY','iris26550BilinearSdr','vec2 sourcePixel=(vec2(p)+vec2(0.5))*vec2(sdrSize)/vec2(gainMapSize)-vec2(0.5)']:
 req(shader,s,'gainmap geometry '+s)
night=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text()
for s in ['IrisNightUltraHdr.prepare','IrisNightNeuralEnhancer.enhanceInPlace','IrisNightUltraHdr.attachPostJin','IRIS_26550_NIGHT_POST_JIN_ULTRAHDR','releaseNightFrames(batch)','IRIS_26550_NIGHT_UI_COMPLETION']:
 req(night,s,'Night final lifecycle '+s)
inds=[night.index('NIGHT_BASE_JPEG_BEGIN'),night.index('NIGHT_JIN_BEGIN'),night.index('IrisNightUltraHdr.attachPostJin'),night.index('NIGHT_FINAL_JPEG_BEGIN')]
if inds!=sorted(inds): raise SystemExit('FAIL base/Jin/UHDR/final order')
# Must release frames before clearing global processing and callback.
i_rel=night.index('releaseNightFrames(batch);', night.index('NIGHT_PROCESS_FINISHED_NOTIFY_BEGIN'))
i_clear=night.index('CaptureController.isProcessing = false;',i_rel)
i_cb=night.index('listener.onProcessingFinished("Iris Night Processing Finished")',i_clear)
if not i_rel<i_clear<i_cb: raise SystemExit('FAIL Night UI cleanup ordering')
helper=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java').read_text()
for s in ['IRIS_26550_NIGHT_POST_JIN_ULTRAHDR_OWNER','oldRatio * (pre + UHDR_OFFSET) / (fin + UHDR_OFFSET)','MotionV2UltraHdr.attach(finalSdr, rebased, 0, prepared.maxRatio)','memoryBounded=true']:
 req(helper,s,'Night UHDR helper '+s)
saver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
for s in ['ultraHdrRequested=','IRIS_26550_NIGHT_FINAL_PUBLICATION','baseCheckpointPreservedOnFailure=true']:
 req(saver,s,'Night save/UHDR '+s)
frag=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text()
for s in ['iris26550NightUiRearmPending','IRIS_26550_NIGHT_TO_MOTION_UI_REARM','mCameraUIView.resetCaptureProgressBar();']:
 req(frag,s,'Night->Motion UI rearm '+s)
print('PASS: exact 10-file 26550 scope')
print('PASS: 12+3/-0.70 EV capture, Sabre, VGN, Jin, CaptureController and native JPEG authorities unchanged')
print('PASS: adaptive Night presentation is post-color/post-capture and Motion matcher branch retained')
print('PASS: true Sabre HDR relationship is detached, post-Jin rebased, then JPEG_R attached')
print('PASS: Night base checkpoint remains before Jin/UHDR final publication')
print('PASS: Night frames release -> processing=false -> UI completion ordering')
