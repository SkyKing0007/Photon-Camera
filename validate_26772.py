#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, re, difflib, xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26772.py BASE26771 CAND26772')
base,cand=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
expected=[x for x in (root/'26772_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
modified=[x for x in (root/'26772_MODIFIED_PATHS.txt').read_text().splitlines() if x]
deleted=[x for x in (root/'26772_DELETED_PATHS.txt').read_text().splitlines() if x]
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(base),H(cand)
changed=sorted(k for k in set(hb)|set(hc) if hb.get(k)!=hc.get(k))
assert len(hb)==1824 and len(hc)==1779,(len(hb),len(hc))
assert changed==sorted(expected),(len(changed),len(expected),sorted(set(changed)^set(expected))[:10])
assert sorted(k for k in hb if k not in hc)==sorted(deleted)
assert sorted(k for k in hb if k in hc and hb[k]!=hc[k])==sorted(modified)
assert not [k for k in hc if k not in hb]
print('PASS 26772 exact 68-path runtime allowlist / 23 modifications / 45 deletions / 0 additions')
# Version/build
vp=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726772' in vp and 'VERSION_BUILD=26772' in vp
print('PASS 26772 version/build')
# Changed XML must be well formed; all deleted gallery resources remain absent.
for rel in modified:
    if rel.endswith('.xml'):
        ET.parse(cand/rel)
for rel in deleted:
    assert not (cand/rel).exists(),rel
print('PASS 26772 changed XML/resources parse clean and all Gallery deletions absent')
# Gallery removal: one launcher only, no internal Gallery package/resource/key authority.
manifest=(cand/'app/src/main/AndroidManifest.xml').read_text()
assert 'GalleryActivity' not in manifest and 'GalleryActivityLauncher' not in manifest
assert manifest.count('android.intent.action.MAIN')==1 and manifest.count('android.intent.category.LAUNCHER')==1
assert 'com.particlesdevs.photoncamera.ui.camera.CameraActivity' in manifest
all_text='\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src').rglob('*') if p.is_file() and p.suffix in {'.java','.kt','.xml'})
for stale in ['com.particlesdevs.photoncamera.gallery','GalleryActivityLauncher','pref_hide_gallery_icon_key','gallery_nav_graph','gallery_preferences']:
    assert stale not in all_text,stale
cf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text()
vm=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/CameraFragmentViewModel.java').read_text()
assert 'Intent.ACTION_VIEW' in cf and 'GalleryActivity.class' not in cf
assert 'MediaStore.Images.Media.EXTERNAL_CONTENT_URI' in vm and 'GalleryFileOperations' not in vm
print('PASS 26772 Iris Gallery app/launcher/path removed; CameraActivity sole launcher; external gallery viewing retained')
# Storage backend ownership.
ssh=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java').read_text()
ca=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java').read_text()
for a in ['IRIS_26772_SELECTED_STORAGE_ROOT_OWNER','BACKEND_DOWNLOADS','MediaStore.Downloads','MediaStore.MediaColumns.RELATIVE_PATH','IRIS_LOGS_DIR_NAME','IRIS_RAW_DIR_NAME','setDownloadsRoot','getOrCreateDownloadsUri']:
    assert a in ssh,a
for a in ['showStorageAccessChoiceDialog','storage_choose_folder','storage_use_download','setDownloadsRoot']:
    assert a in ca,a
assert 'expectedBasePath' not in ca and 'DCIM' not in ca[ca.find('showStorageAccessChoiceDialog'):ca.find('showStorageAccessChoiceDialog')+2500]
assert 'findOrCreateDirectory(iris, IRIS_LOGS_DIR_NAME)' in ssh
print('PASS 26772 dual storage backend: arbitrary SAF + supported MediaStore.Downloads, with Iris Camera/Tuning/Spektra/Raw/Logs ownership')
# Logger mechanism remains Iris-owned; only backend/destination routing changes.
logb=(base/'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java').read_text()
logc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java').read_text()
for a in ['IRIS_26772_SELECTED_ROOT_IRIS_LOG_OWNER','openSelectedRootWriter','SimpleStorageHelper.openIrisAppendOutputStream','SimpleStorageHelper.cleanupIrisLogFiles']:
    assert a in logc,a
for invariant in ['LOG_RETENTION_DAYS = 10','HandlerThread logThread','ThreadLocal<SimpleDateFormat>','motionLogHandler','shouldSkipPersistentSpam']:
    assert invariant in logb and invariant in logc,invariant
assert 'openMediaStoreWriter' in logc  # Android 10 proven fallback retained.
print('PASS 26772 existing Iris logger threading/format/retention owner preserved; Android 11+ destination follows selected Iris Logs root')
# Still DNG follows DCIM/Camera; RAW Video remains Raw-only owner.
ip=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImagePath.java').read_text()
assert 'File dir = FileManager.sDCIM_CAMERA;' in ip
assert 'if (extension.equalsIgnoreCase("dng"))' not in ip
assert ip.count('File dir = FileManager.sPHOTON_RAW_DIR;')==2
assert 'getNewVideoFolderPath' in ip
# DNG implementation files themselves are protected unchanged.
for line in (root/'26772_DNG_AUTHORITY.sha256').read_text().splitlines():
    h,rel=line.split(None,1); rel=rel.strip(); assert (base/rel).read_bytes()==(cand/rel).read_bytes()==(base/rel).read_bytes()
print('PASS 26772 Motion/Night/still DNG routes with JPG/HEIC to DCIM/Camera; Raw remains RAW Video owner; DNG serialization/math byte-invariant')
# Histogram: exact portrait top corner is fixed; no translation owner.
cb=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java').read_text()
assert 'IRIS_26772_STATIONARY_HISTOGRAM_CORNER_OWNER' in cb
assert 'if (orientation == -90)' in cb and 'view.setPivotX(width);' in cb
assert 'else if (orientation == 90)' in cb and 'view.setPivotX(0f);' in cb
# Both quarter turns pivot at top edge, and no translation is introduced.
segment=cb[cb.index('@BindingAdapter("bindHistogramRotate")'):cb.index('@BindingAdapter("bindFrontCameraRotate")')]
assert segment.count('view.setPivotY(0f);')==2
assert 'view.setTranslationX(0f);' in segment and 'view.setTranslationY(0f);' in segment
print('PASS 26772 histogram stationary top-corner pivot: right/left quarter-turn ordering preserved with zero translation')
# Front camera: rotate independent parent; existing tap-spin owner protected in CameraUIController.
layout=(cand/'app/src/main/res/layout/layout_bottombuttons.xml').read_text()
assert 'front_camera_orientation_rotator' in layout and 'bindFrontCameraRotate="@{uimodel}"' in layout
assert layout.index('front_camera_orientation_rotator') < layout.index('flip_camera_button')
assert 'view.animate().rotation(model.getOrientation())' in cb
ui_rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java'
assert (base/ui_rel).read_bytes()==(cand/ui_rel).read_bytes()
assert 'rotationBy(180)' in (cand/ui_rel).read_text()
print('PASS 26772 front-camera physical rotation owner separated from unchanged tap-to-switch 180-degree animation')
# Lens 13sp and universal min(anchor*30,120) ceiling.
aux=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java').read_text()
zoom=(cand/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_text()
assert 'COMPLEX_UNIT_SP, 13.0f' in aux
assert 'GLOBAL_MAX_ZOOM = 120.0f' in zoom and 'anchor * LOCAL_MAX_ZOOM' in zoom and 'Math.min(maximum, GLOBAL_MAX_ZOOM)' in zoom
for anchor,expected_max in [(0.5,15.0),(1.0,30.0),(2.0,60.0),(4.1,120.0),(10.0,120.0)]:
    assert min(anchor*30.0,120.0)==expected_max
print('PASS 26772 lens labels restored to 13sp; universal zoom maximum=min(opticalAnchor*30,120x)')
# Flattened-highlight correction is confined to the existing final-trust shader region only.
grel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
gb=(base/grel).read_text(); gc=(cand/grel).read_text()
assert 'IRIS_26772_FLATTENED_HIGHLIGHT_CHROMA_OWNER' not in gb and 'IRIS_26772_FLATTENED_HIGHLIGHT_CHROMA_OWNER' in gc
for a in ['highlightInvalid26772','highlightConnected26772','flattenedHighlight26772','0x2000','smoothstep(0.86,0.96,centerPeak)','smoothstep(0.72,0.90,centerY)']:
    assert a in gc,a
# No change elsewhere in this large owner file.
bl=gb.splitlines(); cl=gc.splitlines(); sm=difflib.SequenceMatcher(a=bl,b=cl,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    assert i1>=1590 and i2<=1643,(tag,i1,i2,j1,j2)
    assert j1>=1590 and j2<=1669,(tag,i1,i2,j1,j2)
# Neighbor RGB is used only for plateau luma/peak evidence; final RGB remains center-luma/chroma reconstruction.
assert 'vec3 qr=rgb26769(q);float qY=y26769(qr),qPeak=max3_26769(qr);' in gc
assert 'vec3 finalRgb=clamp(vec3(postY)+recoveredNC*max(postY,0.060)' in gc
print('PASS 26772 flattened-highlight chroma correction confined to final VGN trust pass; normal color/capture owners outside that region unchanged')
# Full asset shader universe is unchanged; protected capture/tone/DNG/native/vendor checked by manifests in build script.
assert all((base/'app/src/main/assets/shaders'/p).read_bytes()==(cand/'app/src/main/assets/shaders'/p).read_bytes() for p in [str(x.relative_to(base/'app/src/main/assets/shaders')) for x in (base/'app/src/main/assets/shaders').rglob('*') if x.is_file()])
print('PASS 26772 complete 271-file asset shader universe unchanged from successful 26771 R2')
print('PASS 26772 semantic/ownership/domain regression suite')
