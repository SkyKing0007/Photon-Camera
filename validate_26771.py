#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26771.py BASE26770 CAND26771')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
expected=[x for x in (root/'26771_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=[x for x in (root/'26771_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x]
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
a,b=H(base),H(cand)
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert len(a)==1823 and len(b)==1824,(len(a),len(b))
assert changed==sorted(expected),(changed,expected)
assert sorted(k for k in b if k not in a)==sorted(added)
assert not [k for k in a if k not in b]
print('PASS 26771 exact 30-path runtime allowlist / 1 addition / 0 deletions')
# version
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726771' in v and 'VERSION_BUILD=26771' in v
print('PASS 26771 version/build')
# XML/resources parse all changed XML
for rel in expected:
    if rel.endswith('.xml'): ET.parse(cand/rel)
print('PASS 26771 changed XML/resources parse clean')
# Splash direct launch
manifest=(cand/'app/src/main/AndroidManifest.xml').read_text()
assert 'com.particlesdevs.photoncamera.ui.SplashActivity' not in manifest
assert 'android:name="com.particlesdevs.photoncamera.ui.camera.CameraActivity"' in manifest
assert 'android:screenOrientation="portrait"' in manifest
assert 'android:theme="@style/Theme.Photon.CameraLaunch"' in manifest
assert manifest.count('<action android:name="android.intent.action.MAIN" />')>=2  # camera + gallery launcher alias
assert '<category android:name="android.intent.category.LAUNCHER" />' in manifest
photon=(cand/'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java').read_text()
assert 'new Intent(context, CameraActivity.class)' in photon and 'SplashActivity.class' not in photon
styles=(cand/'app/src/main/res/values/styles.xml').read_text(); v31=(cand/'app/src/main/res/values-v31/styles.xml').read_text()
assert 'Theme.Photon.CameraLaunch' in styles and '@android:color/black' in styles
assert 'windowSplashScreenAnimatedIcon' in v31 and '@android:color/transparent' in v31 and 'windowSplashScreenAnimationDuration">0<' in v31
print('PASS 26771 custom branded splash removed; CameraActivity direct portrait launcher; API31 launch surface minimal')
# Orientation ownership
ori=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CustomOrientationEventListener.java').read_text()
assert 'IRIS_26771_PHYSICAL_ORIENTATION_OWNER' in ori
assert 'ACCELEROMETER_ROTATION' not in ori and 'Settings.System.getInt' not in ori
bind=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java').read_text()
for s in ['IRIS_26771_HISTOGRAM_SAFE_PIVOT_OWNER','orientation == -90','view.setPivotX(width)','orientation == 90','view.setPivotX(0f)','view.setPivotY(height)']: assert s in bind,s
camxml=(cand/'app/src/main/res/layout/camera_fragment.xml').read_text(); bottom=(cand/'app/src/main/res/layout/layout_bottombuttons.xml').read_text()
assert camxml.count('bindHistogramRotate="@{uimodel}"')==2
# front camera parent owns physical rotation; child tap spin remains protected separately
switch_block=re.search(r'<FrameLayout\s+android:id="@\+id/camera_switch_container".*?</FrameLayout>',bottom,re.S); assert switch_block and 'bindRotate="@{uimodel}"' in switch_block.group(0)
assert 'android:id="@+id/flip_camera_button"' in switch_block.group(0)
ui_ctl_rel=Path('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
assert (base/ui_ctl_rel).read_bytes()==(cand/ui_ctl_rel).read_bytes(); assert 'rotationBy(180)' in (cand/ui_ctl_rel).read_text()
# fixed format pill and modes remain without rotation binding
fmt=re.search(r'<LinearLayout\s+android:id="@\+id/format_selector_pill".*?</LinearLayout>',camxml,re.S); assert fmt and 'bindRotate' not in fmt.group(0)
mode_rel=Path('app/src/main/res/layout/layout_modeswitcher.xml'); assert (base/mode_rel).read_bytes()==(cand/mode_rel).read_bytes(); assert 'bindRotate' not in (cand/mode_rel).read_text()
aux=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java').read_text(); assert 'setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 9.0f)' in aux
print('PASS 26771 orientation: portrait-lock-independent physical rotation + front-camera parent + safe histogram pivot + fixed mode/format pills + uniform 9sp lens labels')
# Storage prompt and unrestricted folder picker
strings=(cand/'app/src/main/res/values/strings.xml').read_text()
assert '<string name="perm_rationale_dcim_title">Storage Access</string>' in strings
assert 'Access to the storage folder is required for saving RAW video files and reading device custom configs.' in strings
assert 'Select a storage folder' in strings and 'Select the DCIM folder' not in strings
camera=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java').read_text()
assert 'new OpenFolderPickerContract(this)' in camera
assert 'new OpenFolderPickerContract.Options()' in camera
assert 'createDcimInitialPath' not in camera and 'RequestStorageAccessContract' not in camera
assert 'SimpleStorageHelper.setStorageRoot' in camera and 'SimpleStorageHelper.ensureIrisStorageHierarchy' in camera
assert 'FileManager.CreateFolders()' not in camera
print('PASS 26771 unrestricted user-selected Storage Access picker; no DCIM path gate')
# Storage authority helper
helper=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java').read_text()
for token in ['IRIS_26771_SELECTED_STORAGE_ROOT_OWNER','selected_tree_uri','IRIS_CAMERA_DIR_NAME = "Iris Camera"','IRIS_TUNING_DIR_NAME = "Tuning"','IRIS_SPEKTRA_DIR_NAME = "Spektra"','IRIS_RAW_DIR_NAME = "Raw"','findOrCreateDirectory(selected, IRIS_CAMERA_DIR_NAME)','findOrCreateDirectory(iris, IRIS_TUNING_DIR_NAME)','findOrCreateDirectory(iris, IRIS_SPEKTRA_DIR_NAME)','findOrCreateDirectory(iris, IRIS_RAW_DIR_NAME)','openFdForWrite','openOutputStreamByAbsPath','createOrReplaceIrisFile']: assert token in helper,token
assert 'DCIM_BASE_PATH' not in helper and 'PhotonCamera' not in helper
assert 'Logs' in helper and 'intentionally remain owned' in helper
fm=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/FileManager.java').read_text()
assert 'IRIS_26771_STORAGE_COMPATIBILITY_ALIASES' in fm and 'sIRIS_SPEKTRA_DIR' in fm
assert 'public static void CreateFolders()' not in fm
# no stale old root literal anywhere under active app/src
for p in (cand/'app/src').rglob('*'):
    if p.is_file():
        try: t=p.read_text()
        except Exception: continue
        assert 'DCIM/PhotonCamera' not in t and 'DCIM\\PhotonCamera' not in t,(str(p),'stale DCIM/PhotonCamera')
print('PASS 26771 selected-root Iris Camera/Tuning/Spektra/Raw authority; Photon folder creator removed; no stale DCIM/PhotonCamera literal')
# Current Iris logger remains exact, including current MediaStore/Downloads ownership/location behavior.
for rel in [Path('app/src/main/java/com/particlesdevs/photoncamera/util/Log.java'),Path('app/src/main/java/com/particlesdevs/photoncamera/util/MotionTrace.java')]:
    assert (base/rel).read_bytes()==(cand/rel).read_bytes(),rel
log=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java').read_text(); assert 'Iris Camera/Logs' in log or 'Logs' in log
print('PASS 26771 existing Iris Log.java/MotionTrace writer bytes protected unchanged')
# Major selected-root consumers now use SAF helper.
checks={
'app/src/main/java/com/particlesdevs/photoncamera/pro/Specific.java':['Tuning/DeviceSpecific.txt','openIrisInputStream','irisFileExists'],
'app/src/main/java/com/particlesdevs/photoncamera/pro/SensorSpecifics.java':['Tuning/SensorSpecifics.txt','openIrisInputStream','irisFileExists'],
'app/src/main/java/com/particlesdevs/photoncamera/debugclient/Debugger.java':['Tuning/DebugClient.txt','openIrisInputStream'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLBasePipeline.java':['Tuning/PhotonCameraTuning.ini','openIrisInputStream'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLOneScript.java':['Tuning/PhotonCameraTuning.ini','openIrisInputStream'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AWB.java':['Tuning/awb_lut.png','openIrisInputStream'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Equalization.java':['Tuning/analyze_lut.png','openIrisInputStream'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java':['Tuning/initial_lut.png','openIrisInputStream'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':['customCCT.txt','openIrisInputStream','irisFileExists'],
'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java':['createOrReplaceIrisFile','Spektra/'],
}
for rel,toks in checks.items():
    t=(cand/rel).read_text()
    for tok in toks: assert tok in t,(rel,tok)
print('PASS 26771 tuning/config/customCCT/Spektra consumers follow selected Iris root')
# DNG algorithm invariants: five of six DNG authority files exact; changed writer transport-only.
dng_exact=[
'app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp','app/src/main/cpp/dngCreator.h',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']
for rel in map(Path,dng_exact): assert (base/rel).read_bytes()==(cand/rel).read_bytes(),rel
bw=(base/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java').read_text(); cw=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java').read_text()
# normalize the transport edits back to authority and require total equality
nw=cw.replace('import com.particlesdevs.photoncamera.util.SimpleStorageHelper;\n','')
nw=nw.replace('''            SimpleStorageHelper.deleteByAbsPath(output.toString());\n            OutputStream safOutput = SimpleStorageHelper.openOutputStreamByAbsPath(output.toString());\n            if (safOutput == null) throw new IOException("True2x DNG SAF output unavailable: " + output);\n            try (OutputStream out = new BufferedOutputStream(safOutput, 1024 * 1024)) {''','''            Files.deleteIfExists(output);\n            try (OutputStream out = new BufferedOutputStream(\n                    Files.newOutputStream(output, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE),\n                    1024 * 1024)) {''')
nw=nw.replace('''            long actualOutputBytes = SimpleStorageHelper.lengthByAbsPath(output.toString());\n            if (actualOutputBytes != expected) {\n                throw new IOException("DNG final size mismatch expected=" + expected\n                        + " actual=" + actualOutputBytes);\n            }''','''            if (Files.size(output) != expected) {\n                throw new IOException("DNG final size mismatch expected=" + expected\n                        + " actual=" + Files.size(output));\n            }''')
nw=nw.replace('try { SimpleStorageHelper.deleteByAbsPath(output.toString()); } catch (Throwable ignored) {}','try { Files.deleteIfExists(output); } catch (Throwable ignored) {}')
assert nw==bw
# ImageSaver DNG writer change is stream transport only.
bi=(base/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text(); ci=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
ni=ci.replace('import com.particlesdevs.photoncamera.util.SimpleStorageHelper;\n','')
ni=ni.replace('''                try (OutputStream outputStream = SimpleStorageHelper.openOutputStreamByAbsPath(dngFilePath.toString())) {\n                    if (outputStream == null) throw new IOException("DNG SAF output unavailable: " + dngFilePath);''','''                try (OutputStream outputStream = Files.newOutputStream(dngFilePath)) {''')
ni=ni.replace('''            try (OutputStream outputStream = SimpleStorageHelper.openOutputStreamByAbsPath(dngFilePath.toString())) {\n                if (outputStream == null) throw new IOException("DNG SAF output unavailable: " + dngFilePath);\n                dngCreator.writeBuffer(outputStream, buffer, parameters.rawSize.x, parameters.rawSize.y);\n            }''','''            try {\n                OutputStream outputStream = Files.newOutputStream(dngFilePath);\n                dngCreator.writeBuffer(outputStream, buffer, parameters.rawSize.x, parameters.rawSize.y);\n                outputStream.close();\n            }''')
assert ni==bi
print('PASS 26771 DNG serialization/math byte-protected; only output transport follows selected SAF root')
# Protect successful 26770 IQ/capture architecture and every runtime shader.
protected_key=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']
for rel in map(Path,protected_key): assert (base/rel).read_bytes()==(cand/rel).read_bytes(),rel
base_sh={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
cand_sh={str(p.relative_to(cand)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (cand/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(base_sh)==len(cand_sh)==271 and base_sh==cand_sh
print('PASS 26771 successful-26770 capture/VGN/tone/shader owners byte-protected; 271 asset shaders unchanged')
print('PASS 26771 semantic/ownership/domain regression suite')
