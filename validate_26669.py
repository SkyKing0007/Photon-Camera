#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26669.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def rd(root,r): return (root/r).read_text()
def sh(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
a,b=H(base),H(cand)
assert len(a)==len(b)==1725,(len(a),len(b))
changed=[
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/version.properties']
actual=sorted(r for r in set(a)|set(b) if a.get(r)!=b.get(r))
assert actual==sorted(changed),(actual,sorted(changed))
assert all(r in a and r in b for r in changed)
ver=rd(cand,'app/version.properties')
assert 'VERSION_NAME=0.9726669' in ver and 'VERSION_BUILD=26669' in ver

# Capture planner remains exact successful 26668 R1.1; only stale bridge ownership is corrected.
cap='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
assert sh(base,cap)==sh(cand,cap)
captext=rd(cand,cap); clean=re.sub(r'/\*.*?\*/',' ',captext,flags=re.S); clean=re.sub(r'//.*',' ',clean)
assert len(re.findall(r'\bupdateMotion26662GoogleReferenceExposureAuthority\s*\(',clean))==1 # definition only
for t in ['IRIS_26668_CAPTURE_TIME_GOOGLE_HDR_BRACKET_OWNER','highlightShortSubmitted=','shortTemporalAccumulator=false','frame.motionV2ReferenceProtectionEv = 0.0f']:
    assert t in captext,t
assert len(re.findall(r'\bapplyMotion26486ExplicitShortCaptureIfNeeded\s*\(',clean))==2 # definition + shutter call

bridge=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26669_ISOLATED_CAPTURE_TIME_SHORT_OWNER','shortFrame == null || iris26593ShortExpected','IRIS_26669_ISOLATED_SHORT_SCHEDULE','shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }','main-list HIGHLIGHT_SHORT is forbidden for Motion']:
    assert t in bridge,t
assert '26658 Motion HIGHLIGHT_SHORT repair survived Google-bracketing conversion' not in bridge
# R1 Kotlin compiler regression remains fixed after modifying this file again.
assert 'MotionTrace.processingState' not in bridge
for bad in ['reconstructionSupport26668.width','reconstructionSupport26668.height','reconstructionSupport26668.data']:
    assert bad not in bridge,bad

# Hardened one-tunnel SHORT and 26668 IQ work are protected exact bytes.
stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
sabre='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
for r in [stack,sabre,
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    assert sh(base,r)==sh(cand,r),r
stacktext=rd(cand,stack)
for t in ['highlightShortFrameCount <= 1','if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue','val mergedFrameCount = normalFrameCount + shadowLongFrameCount']:
    assert t in stacktext,t
sabret=rd(cand,sabre)
for t in ['IRIS_26668_DEFORMING_SUBJECT_GEOMETRY_REJECTION','IRIS_26668_MOTION_SAFE_LONG_AND_NORMAL_CHROMA_OWNER']:
    assert t in sabret,t

# Preview: sensor AE owner stays unchanged; only stateless display presentation changes.
main='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'
assert sh(base,main)==sh(cand,main)
preview=rd(cand,'app/src/main/assets/shaders/preview/main_fs.glsl')
for t in ['IRIS_26669_STATELESS_PREVIEW_HIGHLIGHT_PRESENTATION','const float irisPivot = 0.38','irisCompressedT = irisT / (1.0 + 1.10 * irisT)','color.rgb *= irisScale']:
    assert t in preview,t
# No new temporal/display control uniform was introduced by 26669.
base_preview=rd(base,'app/src/main/assets/shaders/preview/main_fs.glsl')
base_uniforms=sorted(re.findall(r'^\s*uniform\s+[^;]+;',base_preview,flags=re.M))
cand_uniforms=sorted(re.findall(r'^\s*uniform\s+[^;]+;',preview,flags=re.M))
assert base_uniforms==cand_uniforms,(base_uniforms,cand_uniforms)
for forbidden in ['irisPreviewHistory','irisExposureSlew','irisHistogramExposure','irisPreviousExposure']:
    assert forbidden not in preview

# Manual UI: exact v9 geometry stays protected; ownership is corrected in app runtime code.
palette='app/src/main/res/layout/manual_palette.xml'; fragxml='app/src/main/res/layout/camera_fragment.xml'; bottom='app/src/main/res/layout/layout_bottombuttons.xml'; hist='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java'
for r in [palette,fragxml,bottom,hist,'app/src/main/res/drawable-nodpi/iris_flip_arrows.png']:
    assert sh(base,r)==sh(cand,r),r
palette_t=rd(cand,palette); frag_t=rd(cand,fragxml); hist_t=rd(cand,hist)
assert 'android:textSize="0sp"' in palette_t and 'android:textColor="@android:color/transparent"' in palette_t
assert 'android:translationY="12px"' in frag_t
assert 'android:id="@+id/iris_live_histogram"' in frag_t
assert 'android:layout_width="wrap_content"' in frag_t and 'android:layout_height="38dp"' in frag_t
for forbidden in ['CaptureRequest','CONTROL_AE','CONTROL_AF','CONTROL_AWB']:
    assert forbidden not in hist_t,forbidden

slider=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java')
frag=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
ui=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
assert 'ManualModeConsoleImpl.getInstance()' not in slider
for t in ['bindManualModeConsole(ManualModeConsole owner)','IRIS_26669_SINGLE_MANUAL_CONSOLE_OWNER','all.size() - 1','KnobItemInfo next = all.get(manualIndex + 1)','requestDisallowInterceptTouchEvent(true)','MotionEvent.ACTION_MOVE','MotionEvent.ACTION_UP','MotionEvent.ACTION_CANCEL','commitTrueAuto(model)','paint.setColor(autoPressed ? YELLOW : WHITE)','canvas.drawText(current.text']:
    assert t in slider,t
for t in ['manualModeConsole.init(activity, characteristics);','irisManualSlider.bindManualModeConsole(manualModeConsole);','IRIS_26669_SINGLE_MANUAL_CONSOLE_OWNER']:
    assert t in frag,t
assert frag.index('manualModeConsole.init(activity, characteristics);') < frag.index('irisManualSlider.bindManualModeConsole(manualModeConsole);')
for t in ['IRIS_26669_V9_COLLAPSED_MANUAL_OWNER','label.setText("");','label.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 0.0f)','label.setTextColor(android.graphics.Color.TRANSPARENT)','root.findViewById(R.id.iris_manual_slider) != null']:
    assert t in ui,t

# Existing 65% output matcher, ImageFrame, DNG/Night/SR ownership protected.
for r in ['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java']:
    assert sh(base,r)==sh(cand,r),r
matcher=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
assert 'MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65.0f' in matcher
print('PASS 26669 semantic/ownership: successful-26668 capture planner + isolated one-tunnel SHORT schedule; HAL AE has no delayed writer call; stateless preview shoulder only; single manual-console owner; v9 geometry/tick/AUTO/drag/histogram preserved; 26668 IQ/65%/DNG/Night/SR owners protected')
