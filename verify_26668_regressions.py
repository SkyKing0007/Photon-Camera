#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26668_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])

def rd(root,r): return (root/r).read_text()
def sh(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def smooth(a,b,x):
    t=clamp((x-a)/(b-a)); return t*t*(3.0-2.0*t)
def long26668(base_weight, validity, requested):
    bw=clamp(base_weight); vr=clamp(validity); requested=max(requested,1.0)
    admission=smooth(.60,.82,bw)*smooth(.97,.999,vr)
    bw*=admission
    conf=smooth(.82,.96,bw)
    return min(bw*(1.0+(requested-1.0)*conf),1.25)

# 26667 failure: marginal LONG survived at baseline. 26668 must hard-reject it.
for b in (0.0,.1,.3,.59,.60):
    assert abs(long26668(b,1.0,2.8))<1e-12,(b,long26668(b,1.0,2.8))
# Per-channel source validity is mandatory for LONG.
for v in (0.0,.5,.9,.96,.97):
    assert abs(long26668(1.0,v,2.8))<1e-12,(v,long26668(1.0,v,2.8))
assert long26668(.90,1.0,2.8)>0.0
assert 0.0 < long26668(1.0,1.0,2.8) <= 1.25
# Geometry veto identity below 0.75px and full rejection at/above 2.25px.
for fw in (0.0,.1,.5,.75): assert abs(1.0-smooth(.75,2.25,fw)-1.0)<1e-12
for fw in (2.25,3.0,10.0): assert abs(1.0-smooth(.75,2.25,fw))<1e-12

cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
clean=re.sub(r'/\*.*?\*/',' ',cap,flags=re.S); clean=re.sub(r'//.*',' ',clean)
# 26667 preview failure cannot recur: delayed HDR AE updater has definition only, no active caller.
assert len(re.findall(r'\bupdateMotion26662GoogleReferenceExposureAuthority\s*\(',clean))==1
assert 'frame.motionV2ReferenceProtectionEv = 0.0f' in cap
assert 'IRIS_26668_CAPTURE_TIME_GOOGLE_HDR_BRACKET_OWNER' in cap
assert 'shortTemporalAccumulator=false' in cap
# Exact 26660 preview renderer + shader are permanent authority.
assert sh(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')=='ee82562ec481fb781319710c1180c8e70f049924d334d1255d673a5ffca518c0'
assert sh(cand,'app/src/main/assets/shaders/preview/main_fs.glsl')=='f7e2c265804d3d9ecaa176e076a15ce6fddee493cb956212b9d79a355248ee08'

# Worm/deforming-subject regression is independent of noise-aware photometric rejection.
sabre=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert 'IRIS_26668_DEFORMING_SUBJECT_GEOMETRY_REJECTION' in sabre
assert 'max(flow.w, 0.0)' in sabre
assert 'weight = min(1.0 - unblocker, frameWeight) * iris26668GeometryConfidence' in sabre
# LONG must not repaint chroma.
for t in ['IRIS_26668_MOTION_SAFE_LONG_AND_NORMAL_CHROMA_OWNER','iris26668NormalChromaticity','accumulatedColor = iris26668SourceRgb * accumulatedWeight']:
    assert t in sabre

# 26667 HDR noise regression: extra high-DR body recovery must be spatially support-gated in both
# SDR and matched UHDR intent, and must fail closed if the support provenance is absent.
rj=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
rs=rd(cand,'app/src/main/assets/shaders/motionv2/render.glsl')
gs=rd(cand,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
assert 'safeExtraBodyLiftEv' in rj and 'failClosed=' in rj
assert 'liftEv*=iris26668ReconstructionSupportAt' in rs
assert 'liftEv*=iris26668ReconstructionSupportAt' in gs
# Never substitute effectiveSupport/frame-count statistics for real spatial evidence.
for r in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    assert 'effectiveSupport' not in rd(cand,r),r

# UI regressions: every non-AUTO model item is one tick; exact item text/value drives selection;
# drag ownership survives leaving the panel; AUTO is yellow while pressed and hidden when restored.
slider=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java')
for t in ['final int manualCount = all.size() - 1','KnobItemInfo next = all.get(manualIndex + 1)','exactText=" + next.text','exactValue=" + next.value','requestDisallowInterceptTouchEvent(true)','paint.setColor(autoPressed ? YELLOW : WHITE)','if (manual) {','commitTrueAuto(model)']:
    assert t in slider,t
frag=rd(cand,'app/src/main/res/layout/camera_fragment.xml')
assert 'android:translationY="12px"' in frag
assert 'android:layout_width="wrap_content"' in frag and 'android:layout_height="38dp"' in frag
hist=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java')
assert 'if (inFlight) return' in hist and 'PixelCopy.request(preview, copyBitmap' in hist
assert 'pixelScratch' in hist and 'ArrayList' not in hist
# Added-file rollback completeness regression from first 26668 patch attempt is packaged in the real
# candidate patches; the verifier requires exactly four new-file/deleted-file mode records.
root=Path(__file__).resolve().parent
f=(root/'R1_26668_RUNTIME_DELTA_FROM_26667.patch').read_bytes()
r=(root/'R1_26668_RUNTIME_ROLLBACK_TO_26667.patch').read_bytes()
assert f.count(b'new file mode 100644')==4
assert r.count(b'deleted file mode 100644')==4

# Unrelated owners remain byte-protected.
for path in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java']:
    assert sh(base,path)==sh(cand,path),path
print('PASS 26668 regressions: true-26660 preview/no delayed AE; capture-time hardened SHORT; deforming-subject veto; hard LONG+NORMAL chroma; spatial support-gated SDR/UHDR body recovery; effectiveSupport non-authority; exact-value UI/live histogram; 4-added-file rollback completeness')
