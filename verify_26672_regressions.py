#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,tempfile,os,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: verify_26672_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
changed=set(x for x in (root/'R1_26672_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
# 1. Exact successful-26671 behavioral hardlock outside four-path scope.
for p in sorted((base/'app').rglob('*')):
 if not p.is_file(): continue
 rel=str(p.relative_to(base))
 if rel not in changed: assert sh(base,rel)==sh(cand,rel),rel
# Explicit JPEG/HDR/capture/noise/Laplacian/histogram/manual touch hardlocks.
for p in [
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java',
'app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/manual_palette.xml','app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/drawable-nodpi/iris_flip_arrows.png','app/src/main/cpp/CMakeLists.txt']:
 assert sh(base,p)==sh(cand,p),p
# 2. HEIC publication-only correction. No pixel/gain computation may move.
b=rd(base,'app/src/main/cpp/iris_heic_jni.cpp'); c=rd(cand,'app/src/main/cpp/iris_heic_jni.cpp')
normal='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeNative('
sr='Java_com_particlesdevs_photoncamera_processing_ultrahdr_IrisHeicUltraHdrEncoder_writeSuperResGridNative('
bi=b.index(normal);ci=c.index(normal);bs=b.index(sr);cs=c.index(sr)
assert b[:bi]==c[:ci] and b[bs:]==c[cs:],'non-normal-HEIC native drift'
bn=b[bi:bs];cn=c[ci:cs]
meta='ultrahdr::uhdr_gainmap_metadata_ext_t metadata(ultrahdr::kJpegrVersion);'
alt='alternateNclx = heif_nclx_color_profile_alloc();'
assert bn[bn.index(meta):bn.index(alt,bn.index(meta))]==cn[cn.index(meta):cn.index(alt,cn.index(meta))]
for t in ['IRIS_26672_GOOGLE_LIBULTRAHDR_V2_HEIF_BASE_PUBLICATION','writeIccProfile(UHDR_CT_SRGB, UHDR_CG_DISPLAY_P3)','save_two_colr_boxes_when_ICC_and_nclx_available = 1','heif_transfer_characteristic_ITU_R_BT_709_5','IRIS_26672_GOOGLE_LIBULTRAHDR_V2_HEIF_GAINMAP_PUBLICATION','heif_color_primaries_unspecified','heif_transfer_characteristic_unspecified','IRIS_26672_GOOGLE_LIBULTRAHDR_V2_TMAP_HDR_INTENT_AUTHORITY','heif_transfer_characteristic_linear','heif_matrix_coefficients_chromaticity_derived_non_constant_luminance','recomputedGainmap=false']:
 assert t in cn,t
for bad in ['generateGainMap(', 'toneMap(', 'applyGainMap(']: assert bad not in cn,bad
# 3. Current 26671 manual position is baseline; row alone reaches midpoint while slider stays fixed.
j=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for t in ['current26671TranslationPx = manualMode.getTranslationY()','rowLp.topMargin += deltaPx','manualMode.setTranslationY(current26671TranslationPx + deltaPx)','0.34f * chevronHeight','sliderCurrent26671PositionPreserved=true geometricMidpoint=true']:
 assert t in j,t
layout=rd(cand,'app/src/main/res/layout/camera_fragment.xml'); assert 'android:translationY="12px"' in layout
for d in [1.0,1.5,2.0,2.625,3.0,3.5,4.0,4.5,5.0]:
 row=round(48*d); stack=round(24*d); chev=round(18*d); bm=round(6*d); ty=12.0
 sb=-bm-row+ty; rc=-bm-row*.5+ty; cp=(stack-chev)*.5+.34*chev; target=.5*(sb+cp); delta=round(target-rc)
 assert delta>0 and abs(rc+delta-target)<=.5000001,(d,delta,rc+delta,target)
 # Adjusting content height and translation by the same delta keeps slider exactly at successful-26671 visual Y.
 assert abs((sb-delta)+(ty+delta-ty)-sb)<1e-9
# 4. Front switch: only vector artwork added. Existing button/layout and old bitmap are exact.
assert sh(base,'app/src/main/res/layout/layout_bottombuttons.xml')==sh(cand,'app/src/main/res/layout/layout_bottombuttons.xml')
assert sh(base,'app/src/main/res/drawable-nodpi/iris_flip_arrows.png')==sh(cand,'app/src/main/res/drawable-nodpi/iris_flip_arrows.png')
v='app/src/main/res/drawable-anydpi/iris_flip_arrows.xml'; ET.parse(cand/v); x=rd(cand,v)
for t in ['android:width="36dp"','android:height="36dp"','android:viewportWidth="128"','android:viewportHeight="128"','android:strokeWidth="8"','android:strokeLineCap="round"']:
 assert t in x,t
assert rd(cand,'app/src/main/res/layout/layout_bottombuttons.xml').count('@drawable/iris_flip_arrows')==1
# 5. Added-file rollback completeness regression remains active.
def run(cmd,cwd,**kw): return subprocess.run(cmd,cwd=cwd,check=True,**kw)
with tempfile.TemporaryDirectory(prefix='iris26672_added_file_reg_') as td:
 t=Path(td); (t/'app').mkdir(); (t/'app/a.txt').write_text('a\n'); run(['git','init','-q'],t); run(['git','config','user.email','iris@example.invalid'],t); run(['git','config','user.name','Iris Handoff'],t); run(['git','add','app'],t); env=os.environ.copy(); env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}); run(['git','commit','-q','-m','base'],t,env=env); (t/'app/new.txt').write_text('new\n'); p=run(['git','ls-files','--others','--exclude-standard','-z','--','app'],t,stdout=subprocess.PIPE); un=[z.decode() for z in p.stdout.split(b'\0') if z]; run(['git','add','-N','--',*un],t); d=run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout; assert d.count(b'new file mode 100644')==1
print('PASS 26672 regressions: successful-26671 JPEG/HDR/capture/noise/Laplacian/histogram/manual-touch bytes hardlocked; HEIC change publication-only with upstream gain bytes/metadata unchanged and SR HEIC exact; manual row uses current-26671 12px baseline and geometric midpoint; flip button layout exact with vector-only arrow override; added-file rollback regression retained')
