#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26681.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent

def t(rel): return (C/rel).read_text(errors='strict')
def b(rel): return (C/rel).read_bytes()
def same(rel): return (B/rel).read_bytes()==(C/rel).read_bytes()
def need(s,*parts):
 for p in parts:
  assert p in s, f'missing semantic anchor: {p}'

def filemap(root):
 import hashlib
 out={}
 for p in sorted((root/'app').rglob('*')):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 return out

bm=filemap(B); cm=filemap(C)
changed=sorted(k for k in set(bm)|set(cm) if bm.get(k)!=cm.get(k))
expected=sorted(x for x in (ROOT/'R1_26681_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
assert changed==expected, f'exact changed scope mismatch {len(changed)} != {len(expected)}'
assert len(bm)==1727 and len(cm)==1764 and len(changed)==49

# Version and enum ordinal persistence.
vp=t('app/version.properties'); need(vp,'VERSION_NAME=0.9726681','VERSION_BUILD=26681')
mode=t('app/src/main/java/com/particlesdevs/photoncamera/api/CameraMode.java')
m=re.search(r'public enum CameraMode\s*\{(.*?)\;',mode,re.S); assert m
names=re.findall(r'\b(UNLIMITED|RAWVIDEO|MOTION|PHOTO|NIGHT|VIDEO|SPEKTRA)\s*\(',m.group(1))
assert names==['UNLIMITED','RAWVIDEO','MOTION','PHOTO','NIGHT','VIDEO','SPEKTRA'],names

# Exact existing picker implementation protected; UI only adds one value/state.
assert same('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java')
ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
need(ui,'"Spektra"','CameraMode.SPEKTRA','IRIS_26681_SPEKTRA_MODE_UI_OWNER','class SpektraModeState','displayedMode == CameraMode.SPEKTRA')
need(ui,'formatRawButton.setVisibility(spektra ? View.GONE : View.VISIBLE)','formatRawJpgButton.setVisibility(spektra ? View.GONE : View.VISIBLE)','formatActiveLabel.setText("JPG")')
# Spektra branch must return before pref writes.
sel=re.search(r'private void selectFormat\(int value\) \{(.*?)\n    \}',ui,re.S); assert sel
assert sel.group(1).find('displayedMode == CameraMode.SPEKTRA') < sel.group(1).find('PreferenceKeys.setSaveRaw')

layout=t('app/src/main/res/layout/layout_main_viewfinder.xml'); need(layout,'@+id/spektra_surface','<SurfaceView')
frag=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'); need(frag,'bindSpektraPreviewSurface','setSpektraPreviewVisible')
settings=t('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
need(settings,'IRIS_26681_SPEKTRA_SETTINGS_FIREWALL','cameraMode == CameraMode.SPEKTRA','pref_category_photo_key','pref_category_jpg_key','pref_category_hdrx_key','pref_category_video_key','pref_category_rawvideo_key')

# Camera facade must early-delegate core lifecycle/shutter and generic control writers.
cc=t('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for a in ['SpektraCameraOwner','bindSpektraPreviewSurface','IRIS_26681_SPEKTRA_CLOSE_DELEGATE','spektraCameraOwner.takePicture()','spektraCameraOwner.resumeCamera()','spektraCameraOwner.retireForHandoff()']:
 assert a in cc,a
for meth in ['setPreviewAEModeRebuild','applyFpsRange','resetPreviewAEMode']:
 block=re.search(r'(?:public|private|protected)[^{]*\b'+meth+r'\s*\([^)]*\)\s*\{(.{0,1800})',cc,re.S)
 assert block and ('SPEKTRA' in block.group(1) or 'isSpektraModeActive' in block.group(1)),f'{meth} lacks Spektra guard'

owner=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
need(owner,'enum State','STILL_CONFIGURING','STILL_CAPTURING','PROCESSING','PREVIEW_RECONFIGURING','retireForHandoff')
# RAW route preference order is literal and stable.
need(owner,'new int[] {ImageFormat.RAW10, ImageFormat.RAW_SENSOR, ImageFormat.RAW12}')
need(owner,'CaptureRequest.CONTROL_AE_MODE_OFF','CaptureRequest.SENSOR_SENSITIVITY','CaptureRequest.SENSOR_EXPOSURE_TIME')
need(owner,'setRepeatingRequest','session.capture','SpektraShotStore.writeAtomic','SpektraShotStore.read')
assert owner.find('SpektraShotStore.writeAtomic') < owner.find('SpektraShotStore.read')
need(owner,'TotalCaptureResult.SENSOR_TIMESTAMP','setPhysicalCameraId','ImageReader.newInstance')
# No temporal/Motion capture primitives in the Spektra owner.
imports='\n'.join(x for x in owner.splitlines() if x.startswith('import '))
for bad in ['IsoExpoSelector','HdrxProcessor','FrameNumberSelector','motionv2','Wronski','Sabre','Parameters','SpecificSensor']:
 assert bad not in imports,f'forbidden Spektra dependency import: {bad}'

exp=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java')
for a in ['AUTO, ISO_PRIORITY, SHUTTER_PRIORITY, MANUAL','STARTUP_NS = 1_500_000_000L','HISTORY_NS = 300_000_000L','MIN_UPDATE_NS = 16_000_000L','MAX_STEP_EV = 0.20','0.025','0.040','0.08','pivotNs']:
 assert a in exp,a

meta=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
need(meta,'Integer dynamicWhite = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL)','float[] dynamic = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL)','android.util.Pair<Double, Double>[] noisePairs = result.get(CaptureResult.SENSOR_NOISE_PROFILE)','double[] noiseProfile')
# Exact compile regression: Camera2 dynamic white is Integer, never Float.
assert 'Float dynamicWhite = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL)' not in meta

raw=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
need(raw,'BAND_CORE_ROWS = 256','RCD_HALO = 12','SAVED_CHROMA_DENOISE_STRENGTH = 0.75f','spektra/raw_clip_mask','spektra/highlight_recover','spektra/sensor_to_linear_srgb','spektra/chroma_denoise')
assert 'if (savedPhoto)' in raw

store=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShotStore.java')
need(store,'.tmp','.shot','getFD().sync()','Os.rename','Truncated Spektra recovery file','unexpected trailing data')
pub=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java')
need(pub,'Bitmap.CompressFormat.JPEG, 100','MediaStore.Images.Media.IS_PENDING','fd.sync()','TAG_ORIENTATION','ORIENTATION_NORMAL','TAG_DATETIME_ORIGINAL')

native=t('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
for a in ['RgbToRawMethod::Hanatos2026','ColorSpace::LinearRec709','ColorSpace::Srgb','p.film = 2','p.paper = 3','PrintTimingMode::FilteredEnlarger','p.autoExposure = false','p.printerLightCalibration = true','p.grainEnabled = false','p.halationEnabled = false','p.cameraDiffusionEnabled = false','p.printDiffusionEnabled = false','p.scannerEnabled = false']:
 assert a in native,a

# Frozen resource hashes.
resource_hashes={
'app/src/main/assets/spektra/data/SpektraProfileData.bin':'6154cae1aa106d2f74bd18eaf907401bc91a0c6c44025aff1d9ea3934f633f20',
'app/src/main/assets/spektra/data/SpektraHanatos2025Spectra.f32':'d615aaedaf269d07b14a351c0c9d54dc7c1df55e9da5f96246e4a737e0fe320f',
'app/src/main/assets/spektra/data/SpektraOutputGamutCompression.f32':'d633700344a0e47f6729e14d20418b7048695ea22fecc59dc30f23f66f3956f6'}
for rel,h in resource_hashes.items(): assert hashlib.sha256(b(rel)).hexdigest()==h,rel

# Hard-lock known shared owners that Spektra must not alter.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/preview/MainRenderer.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']:
 assert same(rel),f'protected shared owner changed: {rel}'

# CMake isolated native owner and exact upstream pin.
cm=t('app/src/main/cpp/CMakeLists.txt')
need(cm,'IRIS_26681_SPEKTRA_ISOLATED_VULKAN_OWNER','86476afc5b077de77e2278e3658d1ba9309892a1','IRIS26681_SPEKTRA_GLSLANG','add_library(iris26681-spektrafilm STATIC','add_library(spektra_iris SHARED')
print('PASS 26681 semantic/ownership validation: sealed Spektra mode, exact 49-path scope, 26680 shared owners protected')
