#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26668.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])

def rd(root,r): return (root/r).read_text()
def sh(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}

a,b=H(base),H(cand)
assert len(a)==1721 and len(b)==1725,(len(a),len(b))
changed=[
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/res/drawable-nodpi/iris_flip_arrows.png',
'app/src/main/res/layout/camera_fragment.xml',
'app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/layout/manual_palette.xml',
'app/version.properties']
actual=sorted(r for r in set(a)|set(b) if a.get(r)!=b.get(r))
assert actual==sorted(changed),(actual,sorted(changed))
assert sorted(r for r in changed if r not in a)==sorted([
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/src/main/res/drawable-nodpi/iris_flip_arrows.png',
'app/src/main/res/layout/manual_palette.xml'])
ver=rd(cand,'app/version.properties')
assert 'VERSION_NAME=0.9726668' in ver and 'VERSION_BUILD=26668' in ver

# True 26660 visible-preview bytes, while capture-time HDR remains a separate shutter owner.
main='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'
preview='app/src/main/assets/shaders/preview/main_fs.glsl'
assert sh(cand,main)=='ee82562ec481fb781319710c1180c8e70f049924d334d1255d673a5ffca518c0'
assert sh(cand,preview)=='f7e2c265804d3d9ecaa176e076a15ce6fddee493cb956212b9d79a355248ee08'
cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
clean=re.sub(r'/\*.*?\*/',' ',cap,flags=re.S); clean=re.sub(r'//.*',' ',clean)
assert len(re.findall(r'\bupdateMotion26662GoogleReferenceExposureAuthority\s*\(',clean))==1 # definition only
for t in ['IRIS_26668_TRUE_26660_PREVIEW_AE_OWNER','IRIS_26668_CAPTURE_TIME_GOOGLE_HDR_BRACKET_OWNER','livePreviewHalAe26660=true','shortTemporalAccumulator=false','frame.motionV2ReferenceProtectionEv = 0.0f']:
    assert t in cap,t
assert 'iris26593ShortBudgetAllows = false' not in cap
assert len(re.findall(r'\bapplyMotion26486ExplicitShortCaptureIfNeeded\s*\(',clean))==2 # definition + shutter call

# Motion robustness: independent geometry rejection + hard LONG admission + NORMAL chroma authority.
sabre=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
stack=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26668_DEFORMING_SUBJECT_GEOMETRY_REJECTION','smoothstep(0.75, 2.25, max(flow.w, 0.0))','IRIS_26668_MOTION_SAFE_LONG_AND_NORMAL_CHROMA_OWNER','uLongFrameRole26668','uNormalReferenceGuide26668','smoothstep(0.60, 0.82, iris26668BaseWeight)','smoothstep(0.97, 0.999, iris26668AllChannelSourceConfidence)','iris26668NormalChromaticity','smoothstep(0.82, 0.96, iris26668BaseWeight)','min(iris26668BaseWeight * iris26668AppliedBoost, 1.25)']:
    assert t in sabre,t
for t in ['longEvidencePolicy26668=MOTION_SAFE_HARD_ADMISSION_NORMAL_CHROMA','longAdmissionStart26668=0.60 longAdmissionFull26668=0.82','longBoostStart26668=0.82 longBoostFull26668=0.96','longFinalWeightCap26668=1.25','longFrameRole26668 = frame.role == RawBurstFrameRole.SHADOW_LONG','normalReferenceGuide26668 = referenceGuide']:
    assert t in stack,t

# Dedicated reconstruction support is separate from denoise strength and wired end-to-end.
contracts=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt')
bridge=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
params=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
renderjava=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
render=rd(cand,'app/src/main/assets/shaders/motionv2/render.glsl')
gain=rd(cand,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
for t in ['mgcReconstructionSupportMap']:
    assert t in contracts and t in bridge,t
for t in ['motionV2ReconstructionSupportQ8','motionV2ReconstructionSupportWidth','motionV2ReconstructionSupportHeight']:
    assert t in params and t in bridge,t
for t in ['IRIS_26668_RECONSTRUCTION_SUPPORT_BINDING','safeExtraBodyLiftEv','failClosed=','iris26668ReconstructionSupportTexture','iris26668ReconstructionSupportEnabled']:
    assert t in renderjava,t
for s in [render,gain]:
    for t in ['iris26668ReconstructionSupport','iris26668ReconstructionSupportEnabled','iris26668ReconstructionSupportAt']:
        assert t in s,t
    assert 'liftEv*=iris26668ReconstructionSupportAt' in s
assert 'IRIS_26668_EVIDENCE_AWARE_HIGH_DR_BODY_RECOVERY' in render

# UI exact contract.
frag=rd(cand,'app/src/main/res/layout/camera_fragment.xml')
palette=rd(cand,'app/src/main/res/layout/manual_palette.xml')
bottom=rd(cand,'app/src/main/res/layout/layout_bottombuttons.xml')
hist=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java')
slider=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java')
assert 'android:id="@+id/format_selector_pill"' in frag and 'android:layout_width="wrap_content"' in frag
assert re.search(r'android:id="@\+id/format_selector_pill"[\s\S]{0,300}?android:layout_height="38dp"',frag)
for t in ['android:id="@+id/iris_live_histogram"','android:layout_width="108dp"','android:layout_height="38dp"','android:layout_marginTop="12dp"','app:layout_constraintTop_toBottomOf="@id/top_black_shell"','app:layout_constraintEnd_toEndOf="parent"','android:translationY="12px"']:
    assert t in frag,t
for t in ['IRIS_26668_LIVE_VIEWFINDER_RGB_HISTOGRAM','COPY_W = 96','COPY_H = 54','BINS = 64','boolean inFlight','PixelCopy.request(preview, copyBitmap','pixelScratch','if (inFlight) return','mainHandler.post(this::ensurePreviewAndRequest)']:
    assert t in hist,t
for forbidden in ['CaptureRequest','CONTROL_AE','CONTROL_AF','CONTROL_AWB']:
    assert forbidden not in hist,forbidden
for t in ['IRIS_26668_EXACT_VALUE_MANUAL_SLIDER','all.size() - 1','item zero is AUTO and never consumes a slider tick','selectedYellow=true fullScreenDragOwner=true','requestDisallowInterceptTouchEvent(true)','MotionEvent.ACTION_MOVE','MotionEvent.ACTION_UP','commitTrueAuto(model)','autoButtonHiddenAfterCommit=true','paint.setColor(autoPressed ? YELLOW : WHITE)','canvas.drawText(current.text','paint.setColor(YELLOW)']:
    assert t in slider,t
assert 'android:textSize="0sp"' in palette and 'android:alpha="0"' in palette
assert '@drawable/iris_flip_arrows' in bottom
assert (cand/'app/src/main/res/drawable-nodpi/iris_flip_arrows.png').is_file()

# Existing core owners that are deliberately outside 26668 scope remain byte-identical.
for r in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java']:
    assert sh(base,r)==sh(cand,r),r
matcher=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
assert 'MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65.0f' in matcher
print('PASS 26668 semantic/ownership: true 26660 preview bytes + capture-time HDR SHORT; NORMAL master with deforming-subject rejection; LONG hard admission/NORMAL chroma; dedicated spatial support gates only extra body recovery in SDR/UHDR; exact-value live UI contract; 65%/DNG/ImageFrame owners protected')
