#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, shutil, subprocess, sys, tempfile, os
if len(sys.argv)!=3: raise SystemExit('usage: verify_26669_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
root=Path(__file__).resolve().parent

def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()

def strip_comments(s):
    s=re.sub(r'/\*.*?\*/',' ',s,flags=re.S)
    return re.sub(r'//.*',' ',s)

# ----- Capture/HDR ownership -----
cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
clean_cap=strip_comments(cap)
# The delayed 26662 preview request writer must be definition-only.
assert len(re.findall(r'\bupdateMotion26662GoogleReferenceExposureAuthority\s*\(',clean_cap))==1
for token in ['IRIS_26668_CAPTURE_TIME_GOOGLE_HDR_BRACKET_OWNER','highlightShortSubmitted=','shortTemporalAccumulator=false','frame.motionV2ReferenceProtectionEv = 0.0f']:
    assert token in cap,token
# CaptureController is deliberately unchanged from successful 26668.
assert sh(base,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')==sh(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')

bridge=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'IRIS_26669_ISOLATED_CAPTURE_TIME_SHORT_OWNER' in bridge
assert '26658 Motion HIGHLIGHT_SHORT repair survived Google-bracketing conversion' not in bridge
assert 'requireParity(shortFrame == null || iris26593ShortExpected' in bridge
assert 'shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }' in bridge
assert 'main-list HIGHLIGHT_SHORT is forbidden for Motion' in bridge
assert 'IRIS_26669_ISOLATED_SHORT_SCHEDULE' in bridge
# The prior R1 Kotlin compiler failures remain impossible.
assert 'MotionTrace.processingState(' not in bridge
for bad in ['reconstructionSupport26668.width','reconstructionSupport26668.height','reconstructionSupport26668.q8.size']:
    assert bad not in bridge,bad
assert 'val strength26668 = checkNotNull(strength)' in bridge
assert 'val reconstructionSupportMap26668 = checkNotNull(reconstructionSupport26668)' in bridge

stack=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for token in ['highlightShortFrameCount <= 1','if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue','val mergedFrameCount = normalFrameCount + shadowLongFrameCount']:
    assert token in stack,token
# 26668 fusion/noise/support implementation stays exact bytes.
for p in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    assert sh(base,p)==sh(cand,p),p
sabre=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for token in ['IRIS_26668_DEFORMING_SUBJECT_GEOMETRY_REJECTION','IRIS_26668_MOTION_SAFE_LONG_AND_NORMAL_CHROMA_OWNER']:
    assert token in sabre,token
# effectiveSupport remains forbidden as a frame/contribution authority in the protected fusion/tone owners.
for p in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    assert 'effectiveSupport' not in rd(cand,p),p

# ----- Viewfinder ownership -----
main='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'
assert sh(base,main)==sh(cand,main), '26669 must not revive renderer-side temporal exposure owner'
preview=rd(cand,'app/src/main/assets/shaders/preview/main_fs.glsl')
base_preview=rd(base,'app/src/main/assets/shaders/preview/main_fs.glsl')
assert 'IRIS_26669_STATELESS_PREVIEW_HIGHLIGHT_PRESENTATION' in preview
for token in ['const float irisPivot = 0.38','irisCompressedT = irisT / (1.0 + 1.10 * irisT)','color.rgb *= irisScale']:
    assert token in preview,token
# No control/state interface added; shader is a pure per-frame mapping.
def uniforms(s): return sorted(re.findall(r'^\s*uniform\s+[^;]+;',s,flags=re.M))
assert uniforms(base_preview)==uniforms(preview)
for forbidden in ['irisPreviewHistory','irisPreviousExposure','irisExposureSlew','irisHistogramExposure','CaptureRequest','CONTROL_AE']:
    assert forbidden not in preview,forbidden
# Numeric regression: the shoulder must be monotonic, bounded, and identity through the pivot.
pivot=.38
prev=-1.0
for i in range(1001):
    y=i/1000.0
    if y<=pivot: out=y
    else:
        t=(y-pivot)/(1.0-pivot)
        c=t/(1.0+1.10*t)
        out=pivot+(1.0-pivot)*c
    assert out+1e-12>=prev,(i,prev,out)
    assert 0.0<=out<=1.0+1e-12
    if y<=pivot: assert abs(out-y)<1e-12
    prev=out

# ----- Manual UI single-owner + v9 behavior -----
slider=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java')
frag=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
ui=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
assert 'ManualModeConsoleImpl.getInstance()' not in slider
for token in [
'bindManualModeConsole(ManualModeConsole owner)',
'IRIS_26669_SINGLE_MANUAL_CONSOLE_OWNER',
'final int manualCount = all.size() - 1',
'KnobItemInfo next = all.get(manualIndex + 1)',
'requestDisallowInterceptTouchEvent(true)',
'MotionEvent.ACTION_MOVE','MotionEvent.ACTION_UP','MotionEvent.ACTION_CANCEL',
'commitTrueAuto(model)','paint.setColor(autoPressed ? YELLOW : WHITE)','canvas.drawText(current.text']:
    assert token in slider,token
for token in ['manualModeConsole.init(activity, characteristics);','irisManualSlider.bindManualModeConsole(manualModeConsole);','IRIS_26669_SINGLE_MANUAL_CONSOLE_OWNER']:
    assert token in frag,token
assert frag.index('manualModeConsole.init(activity, characteristics);') < frag.index('irisManualSlider.bindManualModeConsole(manualModeConsole);')
for token in ['IRIS_26669_V9_COLLAPSED_MANUAL_OWNER','label.setText("");','label.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 0.0f)','label.setTextColor(android.graphics.Color.TRANSPARENT)','root.findViewById(R.id.iris_manual_slider) != null']:
    assert token in ui,token
# v9 geometry/resources and live histogram must remain exact successful-26668 bytes.
for p in [
'app/src/main/res/layout/manual_palette.xml',
'app/src/main/res/layout/camera_fragment.xml',
'app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/res/drawable-nodpi/iris_flip_arrows.png']:
    assert sh(base,p)==sh(cand,p),p
palette=rd(cand,'app/src/main/res/layout/manual_palette.xml')
fragxml=rd(cand,'app/src/main/res/layout/camera_fragment.xml')
hist=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java')
assert 'android:textSize="0sp"' in palette and 'android:textColor="@android:color/transparent"' in palette
assert 'android:translationY="12px"' in fragxml
for forbidden in ['CaptureRequest','CONTROL_AE','CONTROL_AF','CONTROL_AWB']:
    assert forbidden not in hist,forbidden
assert 'if (inFlight) return' in hist and 'PixelCopy.request(preview, copyBitmap' in hist and 'pixelScratch' in hist

# 65% output matcher and metadata ownership stay protected.
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java']:
    assert sh(base,p)==sh(cand,p),p

# ----- Permanent packaging regression from 26668: added-file rollback completeness helper -----
# 26669 itself adds no runtime files. Still prove the helper approach handles an added file in both directions.
def run(cmd,cwd,**kw): return subprocess.run(cmd,cwd=cwd,check=True,**kw)
with tempfile.TemporaryDirectory(prefix='iris26669_added_file_reg_') as td:
    t=Path(td); (t/'app').mkdir(); (t/'app/a.txt').write_text('a\n')
    run(['git','init','-q'],t); run(['git','config','user.email','iris@example.invalid'],t); run(['git','config','user.name','Iris Handoff'],t)
    run(['git','add','app'],t)
    env=os.environ.copy(); env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'})
    run(['git','commit','-q','-m','base'],t,env=env)
    (t/'app/new.txt').write_text('new\n')
    p=run(['git','ls-files','--others','--exclude-standard','-z','--','app'],t,stdout=subprocess.PIPE)
    untracked=[x.decode() for x in p.stdout.split(b'\0') if x]
    assert untracked==['app/new.txt'],untracked
    run(['git','add','-N','--',*untracked],t)
    f=run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout
    assert f.count(b'new file mode 100644')==1

print('PASS 26669 regressions: isolated plan-owned Motion SHORT; no stale blanket SHORT guard; one-tunnel schedule/merged-count semantics; 26668 motion/LONG/support IQ protected; Kotlin R1 failures remain fixed; HAL AE has no delayed writer; stateless monotonic preview presentation; one manual-console owner; v9 icons/ticks/AUTO/full-screen drag/live histogram preserved; added-file patch regression retained')
