#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,xml.etree.ElementTree as ET
if len(sys.argv)!=3:raise SystemExit('usage: validate_26702.py BASE26701 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root):return {'app/'+str(p.relative_to(root/'app')):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def t(rel):return (c/rel).read_text()
def method(text,sig):
 i=text.index(sig);brace=text.index('{',i);d=0
 for j in range(brace,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(sig)
def segment(text,start,end):return text[text.index(start):text.index(end,text.index(start)+len(start))]
B=H(b);C=H(c);exp=[x.strip() for x in (pkg/'26702_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k));assert len(B)==len(C)==1823;assert changed==sorted(exp) and len(changed)==15,(changed,exp)
for rel in B:
 if rel not in exp:assert B[rel]==C[rel],rel
assert not [x for x in (pkg/'26702_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
# UI/settings: Motion-only switch, default ON.
settings=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java')
assert 'KEY_LOCAL_LAPLACIAN_TONE = "pref_iris_local_laplacian_tone"' in settings
assert 'getBoolean(sm, KEY_LOCAL_LAPLACIAN_TONE, true)' in settings
prefs=t('app/src/main/res/xml/preferences.xml');strings=t('app/src/main/res/values/strings.xml')
ET.parse(c/'app/src/main/res/xml/preferences.xml');ET.parse(c/'app/src/main/res/values/strings.xml')
assert prefs.count('ns0:key="pref_iris_local_laplacian_tone"')==1 and 'ns0:defaultValue="true"' in prefs
assert '<string name="iris_local_laplacian_tone">Local Laplacian Tone</string>' in strings
sa=t('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java');assert 'removePreferenceAnywhere(IrisMotionSettings.KEY_LOCAL_LAPLACIAN_TONE);' in sa
# Shutter freeze -> immutable MotionBatch -> Hdrx Parameters handoff.
cc=t('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for token in ['mMotion26702LocalLaplacianAtShutter = IrisMotionSettings.isLocalLaplacianToneEnabled();','IRIS_26702_LOCAL_LAPLACIAN_SHUTTER_SNAPSHOT','mMotion26702LocalLaplacianAtShutter);','localLaplacianFrozen=']:
 assert token in cc,token
mb=t('app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java');assert 'public final boolean localLaplacianToneEnabled;' in mb and 'this.localLaplacianToneEnabled = localLaplacianToneEnabled;' in mb
ds=t('app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java');assert 'batch.localLaplacianToneEnabled,' in ds
hdr=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java');assert 'mMotion26702LocalLaplacianEnabled = localLaplacianToneEnabled;' in hdr and 'processingParameters.motionV2LocalLaplacianToneEnabled' in hdr
params=t('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java');assert 'public boolean motionV2LocalLaplacianToneEnabled = true;' in params
# ON path retains exact 26701 Local-Laplacian implementation methods.
br=(b/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();cr=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for sig in ['    private GLTexture iris26621BuildLocalLaplacianTone(','    private GLTexture iris26626ApplyBoundedSourceDomainPreservation(']:
 assert method(br,sig)==method(cr,sig),sig
for token in ['if (iris26702LocalLaplacianEnabled) {','iris26621LocalTone = iris26621BuildLocalLaplacianTone(extendedLinearHdr);','iris26621ClearLocalToneState();','iris26621LocalTone = null;','IRIS_26702_LOCAL_LAPLACIAN_AB','trueBypass=','globalToneFallback=']:
 assert token in cr,token
# Existing shaders own global fallback and remain byte-identical.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
render=t('app/src/main/assets/shaders/motionv2/render.glsl');gain=t('app/src/main/assets/shaders/motionv2/gainmap.glsl')
assert 'if(iris26592MotionHdrHandoff!=0 && iris26621LocalToneEnabled!=0)' in render and 'linearSrgb=mapExtendedLinearHeadroom(linearSrgb);' in render
assert 'if(iris26621LocalToneEnabled==0)return globalMapped;' in gain
# 26701 gain-map byte-array optimization is preserved exactly.
marker='/* IRIS_26701_GAINMAP_BYTE_ARRAY_EXACT_REMAP';end='                /*\n                 * Per-pixel gain-map provenance'
bs=br[br.index(marker):br.index(end,br.index(marker))];cs=cr[cr.index(marker):cr.index(end,cr.index(marker))];assert bs==cs
# true2x: ON remains fail-closed on map, OFF is explicit global-only and rejects stale map.
enc=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
for token in ['final boolean localToneRequired = parameters.motionV2Active','&& parameters.motionV2LocalLaplacianToneEnabled','IRIS_26702_TRUE2X_LOCAL_TONE_BYPASS_STALE_MAP','parameters.motionV2Active, localToneRequired','boolean motionHdrHandoff, boolean localToneEnabled']:
 assert token in enc,token
cpp=t('app/src/main/cpp/motionv2_jpeg444_jni.cpp');bpp=(b/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for token in ['jboolean motionHdrHandoff,jboolean localToneEnabled','const bool iris26702LocalToneEnabled=localToneEnabled==JNI_TRUE;','if(p.motionHdrHandoff&&iris26702LocalToneEnabled)','else if(!iris26702LocalToneEnabled&&']:
 assert token in cpp,token
for sig in ['inline float localToneMappedGuide(','inline Vec3 renderHeadroom(']:assert method(bpp,sig)==method(cpp,sig),sig
# Active Spektra saved owner corrected; preview geometry remains exact 26701 behavior; dormant wrong owner neutralized.
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt');braw=(b/'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt').read_text()
cap=segment(raw,'    fun captureStill(): Boolean','    fun configure(')
for token in ['IRIS_26702_SPEKTRA_ACTIVE_MOTION_ORIENTATION_PARITY','PhotonCamera.getGravity().getCameraRotation(sensorOrientation)','CaptureTransform(','activeOwner=RawVulkanPreviewController']:
 assert token in cap,token
assert 'displayRotationDegrees()' not in cap
assert segment(raw,'    private fun renderFrame(','    private fun') == segment(braw,'    private fun renderFrame(','    private fun')
spek=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
assert 'IRIS_26701_SPEKTRA_MOTION_ORIENTATION_PARITY' not in spek and 'final int outputRotation = outputRotationDegrees();' in spek
# Lightweight thermal evidence cannot add GPU synchronization/readback.
thermal=method(cr,'    private void iris26702LogThermal(')
assert 'getCurrentThermalStatus()' in thermal and 'BatteryManager.EXTRA_TEMPERATURE' in thermal
for forbidden in ['glFinish','BufferLoad','textureBuffer','glReadPixels']:assert forbidden not in thermal
ver=t('app/version.properties');assert 'VERSION_NAME=0.9726702' in ver and 'VERSION_BUILD=26702' in ver
print('PASS validate 26702: exact 15-file scope; active Spektra Motion-parity orientation; shutter-frozen default-ON Local-Laplacian A/B; true OFF bypass with SDR/UHDR/true2x global-tone parity; exact 26701 ON methods and gain-map optimization preserved')
