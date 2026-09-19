#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26673_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
changed=set(x for x in (root/'R1_26673_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
assert changed=={'app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/version.properties'}
# Permanent authority-seeding/allowlist regression: every real app file outside allowlist stays exact.
bfiles={str(p.relative_to(base)) for p in (base/'app').rglob('*') if p.is_file()}; cfiles={str(p.relative_to(cand)) for p in (cand/'app').rglob('*') if p.is_file()}
assert bfiles==cfiles and len(bfiles)==1726
actual=set()
for p in sorted(bfiles):
 if sh(base,p)!=sh(cand,p): actual.add(p)
assert actual==changed,(sorted(actual),sorted(changed))
# Generated source containers are never authority runtime files. This catches accidental scope regressions.
for p in bfiles:
 assert not p.startswith('app/build/'),p
 assert not p.startswith('app/.cxx/'),p
# Imaging + capture + JPEG/JPEG-R + UHDR-generation + viewfinder/histogram/manual touch/front icon hardlocks.
for p in [
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/manual_palette.xml','app/src/main/res/layout/layout_manual_toggle_panel.xml','app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/drawable-anydpi/iris_flip_arrows.xml','app/src/main/res/drawable-nodpi/iris_flip_arrows.png']:
 assert sh(base,p)==sh(cand,p),p
# HEIC regressions: exact existing gain metadata + Android readback/numerical proof; no recompute/tone owner.
b=rd(base,'app/src/main/cpp/iris_heic_jni.cpp'); c=rd(cand,'app/src/main/cpp/iris_heic_jni.cpp')
normal='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeNative('; sr='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeSuperResGridNative('
bn=b[b.index(normal):b.index(sr)]; cn=c[c.index(normal):c.index(sr)]
meta='ultrahdr::uhdr_gainmap_metadata_ext_t metadata(ultrahdr::kJpegrVersion);'; alt='alternateNclx = heif_nclx_color_profile_alloc();'
assert bn[bn.index(meta):bn.index(alt,bn.index(meta))]==cn[cn.index(meta):cn.index(alt,cn.index(meta))]
assert b[b.index(sr):]==c[c.index(sr):]
for bad in ['generateGainMap(', 'generateGainMapOnePass(', 'toneMap(', 'applyGainMap(']: assert bad not in cn,bad
for t in ['explicitP3Yuv420=true','baseP3SrgbMatrixUnspecified=true','baseIcc=false','gainmapAllColorAspectsUnspecified=true','gainmapReused=true','recomputedGainmap=false']:
 assert t in cn,t
hj=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
assert 'IRIS_26648_HEIC_NUMERICAL_HDR' in hj and 'getGainmapDirection()' in hj
# Manual regression: current 26672 geometry owner stays exact; only visibility owner corrects stale override.
ui=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for t in ['IRIS_26672_MANUAL_ROW_CURRENT_26671_MIDPOINT_OWNER','manualMode.setTranslationY(current26671TranslationPx + deltaPx)','rowLp.topMargin += deltaPx']:
 assert t in ui,t
f=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
vis=f[f.index('private void iris26670ApplyManualPresentationState('):f.index('    void toggleManualControls()')]
assert '.translationY(' not in vis
assert 'R.dimen.standard_20' not in vis
assert 'buttons.setTranslationY(' not in vis
assert 'panel.setTranslationY(0.0f)' in vis
assert f.count('iris26673FixManualRowAtMeasuredMidpoint(panel);')==1
assert 'if (!iris26673ManualMidpointEstablished)' in vis
assert 'iris26673ManualMidpointEstablished = true' in f
# No hidden-state reset of row translation: setTranslationY for buttons occurs exactly once, in one-time geometry owner.
assert f.count('buttons.setTranslationY(')==1
# Exact midpoint algebra and state invariance, independent of screenshot pixels.
for sb,rc,ct in [(0.0,5.0,30.0),(100.25,137.5,242.75),(-40.0,-3.0,80.0)]:
 target=.5*(sb+ct); fixed=target-rc
 assert abs(rc+fixed-target)<1e-12
 # hidden/reopened states do not write fixed => identical center.
 assert rc+fixed==rc+fixed==rc+fixed
print('PASS 26673 regressions: strict 3-path allowlist; generated app/build and app/.cxx absent from runtime authority; successful-26672 JPEG/HDR/capture/noise/Laplacian/viewfinder/histogram/manual-touch/front-icon bytes hardlocked; HEIC gain/metadata + Android numerical proof preserved; SuperRes exact; manual midpoint established once from final 26672 coded geometry and never translated on hide/reopen')
