#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,os
if len(sys.argv)!=3: raise SystemExit('usage: verify_26670_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
def pm(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
# 1. Successful-26660 IQ/motion/render behavior is byte authority, not a tuning approximation.
beh=pm(root/'R1_26670_26660_BEHAVIOR_AUTHORITY.sha256')
for p,h in beh.items(): assert sh(cand,p)==h,p
# 2. Live Camera2 owner and bracket isolation.
cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
clean=re.sub(r'/\*.*?\*/',' ',cap,flags=re.S); clean=re.sub(r'//.*',' ',clean)
for bad in ['updateMotion26662GoogleReferenceExposureAuthority','MOTION_26666_LONG_EXTRA_MAX_EV','motionV2ReferenceProtectionEv','motionV2ReconstructionSupport']:
 assert bad not in clean,bad
# Short/long are submitted through independent still builders and raw-only target paths.
assert clean.count('createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE)')>=3
assert clean.count('addTarget(mImageReaderRaw.getSurface())')>=3
for t in ['captureLocalResultsComplete()','restoreMotion26670LivePreviewAfterCaptureLocalRequests(plan)','mCaptureSession.capture(liveRequest, mCaptureCallback, mBackgroundHandler)','mCaptureSession.setRepeatingRequest(','plan.livePreviewRestoredAfterCaptureLocalRequests = true','beforeProcessing=true','bracketSensorValuesCopiedToPreview=false']:
 assert t in cap,t
# Restoration must be hard-gated before finalize/processing.
restore_call=cap.index('restoreMotion26670LivePreviewAfterCaptureLocalRequests(plan)')
finalize=cap.index('finalizeMotionZslCapture(plan)')
assert restore_call<finalize
# Successful-26660 fixed LONG policy retained and adaptive post-26660 policy absent.
assert 'MOTION_26505_LONG_TARGET_EV = 2.5' in cap
assert 'adaptiveLong=false' in cap
# 3. NORMAL owns temporal structure/motion/noise; SHORT is last auxiliary and excluded ordinary count.
bridge=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'shortTemporalOwner=false' in bridge
l='longFrame?.let { orderedPhysical += it to RawBurstFrameRole.SHADOW_LONG }'; s='shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }'
assert l in bridge and s in bridge and bridge.index(l)<bridge.index(s)
stack=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue','val mergedFrameCount = normalFrameCount + shadowLongFrameCount','IRIS_26651_NORMAL_MASTER_SHORT_FUSION','26648 HIGHLIGHT_SHORT must remain the final scheduled auxiliary frame']:
 assert t in stack,t
# Prevent later Hmart/worm/body-support owners from returning.
for p in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']:
 text=rd(cand,p)
 for bad in ['IRIS_26661_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','IRIS_26666_HIGH_DR_BODY','IRIS_26668_DEFORMING_SUBJECT_GEOMETRY_REJECTION','IRIS_26668_MOTION_SAFE_LONG_AND_NORMAL_CHROMA_OWNER','reconstructionSupport26668']:
  assert bad not in text,(p,bad)
# 4. Manual wheel has no active view/presentation path.
palette=rd(cand,'app/src/main/res/layout/manual_palette.xml'); active_xml=re.sub(r'<!--.*?-->','',palette,flags=re.S)
assert 'KnobView' not in active_xml and 'iris_manual_slider' in active_xml
frag=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
assert frag.count('manualModeConsole.onResume()')==0
assert frag.count('manualModeConsole.onPause()')==1
for t in ['legacyKnobView=false legacyViewObserver=false','modes=FOCUS,SHUTTER,ISO,EV','iris26670EnsureManualPresentationBound()']:
 assert t in frag,t
slider=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java')
assert 'ManualModeConsoleImpl.getInstance()' not in slider
for t in ['sliderStartRect.contains(event.getX(), event.getY())','continuationBounds=FULL_SCREEN','MotionEvent.ACTION_MOVE','MotionEvent.ACTION_UP','MotionEvent.ACTION_CANCEL','requestDisallowInterceptTouchEvent(true)']:
 assert t in slider,t
# 5. 26669 accepted UI geometry/histogram/flip remain protected.
for p in ['app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/layout_bottombuttons.xml','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java','app/src/main/res/drawable-nodpi/iris_flip_arrows.png','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
 assert sh(base,p)==sh(cand,p),p
# 6. Added-file rollback-completeness regression remains permanent.
def run(cmd,cwd,**kw): return subprocess.run(cmd,cwd=cwd,check=True,**kw)
with tempfile.TemporaryDirectory(prefix='iris26670_added_file_reg_') as td:
 t=Path(td); (t/'app').mkdir(); (t/'app/a.txt').write_text('a\n'); run(['git','init','-q'],t); run(['git','config','user.email','iris@example.invalid'],t); run(['git','config','user.name','Iris Handoff'],t); run(['git','add','app'],t)
 env=os.environ.copy(); env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}); run(['git','commit','-q','-m','base'],t,env=env)
 (t/'app/new.txt').write_text('new\n'); p=run(['git','ls-files','--others','--exclude-standard','-z','--','app'],t,stdout=subprocess.PIPE); un=[x.decode() for x in p.stdout.split(b'\0') if x]; assert un==['app/new.txt']; run(['git','add','-N','--',*un],t); d=run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout; assert d.count(b'new file mode 100644')==1
print('PASS 26670 regressions: 26660 IQ byte authority; HAL/user repeating preview owner restored; isolated SHORT/LONG restored before processing; NORMAL temporal/motion/noise owner; Hmart/worm/post-26660 body owners absent; legacy wheel inactive/removed; 4-mode full-screen held drag; 26669 UI geometry preserved; added-file patch regression retained')
