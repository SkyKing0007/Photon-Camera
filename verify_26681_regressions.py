#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
base,cand=map(Path,sys.argv[1:3])

def H(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
def same(p): assert H(base,p)==H(cand,p),p
def text(r,p): return (r/p).read_text()
def method(t,sig):
    i=t.index(sig); b=t.index('{',i); d=0
    for j in range(b,len(t)):
        if t[j]=='{': d+=1
        elif t[j]=='}':
            d-=1
            if d==0:return t[i:j+1]
    raise AssertionError(sig)

def tail_after_guard(block, marker):
    i=block.index(marker); r=block.index('return;',i); return block[r+len('return;'):]

bcc=text(base,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
cc=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')

# 26680 stable-preview/flicker ownership remains byte-identical.
for sig in [
'    private void updateMotion26680StablePreviewAuthority(',
'    private void updateMotion26662GoogleReferenceExposureAuthority(',
'    private void sampleMotion26678RawFlickerEvidence(',
'    private boolean motion26678FindEvidenceLocked(',
'    private long motion26678ChooseStructuralReferenceTimestamp(',
'    private boolean applyMotion26678NormalRowFlickerCorrection(']:
    assert method(bcc,sig)==method(cc,sig),sig
# 26679/26680 HDR transaction mechanics remain exact.
for sig in [
'    private boolean applyMotion26486ExplicitShortCaptureIfNeeded(',
'    private boolean applyMotion26505ExplicitLongCaptureIfUseful(',
'    private Motion26598PreShutterNormals freezeMotion26598PreShutterNormals(',
'    private boolean motion26676ProtectionIncreasePendingForShutter(',
'    private boolean motion26676DeferShutterUntilProtectedGeneration(',
'    private void triggerZslCapture(']:
    assert method(bcc,sig)==method(cc,sig),sig
# The stable-preview update call remains single production owner; legacy 26662 writer remains dormant.
assert cc.count('                updateMotion26680StablePreviewAuthority(result);')==1
assert cc.count('                updateMotion26662GoogleReferenceExposureAuthority(result);')==0
# Shutter enters Spektra before any Motion admission logic.
take=method(cc,'    public void takePicture(')
assert take.index('CameraMode.SPEKTRA') < take.index('IRIS_26679_SCENE_INDEPENDENT_SHUTTER_ADMISSION')
assert take.index('spektraCameraOwner.takePicture();') < take.index('IRIS_26679_SCENE_INDEPENDENT_SHUTTER_ADMISSION')
# Spektra lifecycle delegates return before legacy reopen/resume paths.
restart=method(cc,'    public void restartCamera()')
assert 'spektraCameraOwner.restartCamera();' in restart and restart.index('spektraCameraOwner.restartCamera();') < restart.index('mCameraOpenCloseLock.acquire();', restart.index('spektraCameraOwner.restartCamera();'))
resume=method(cc,'    public void resumeCamera()')
assert resume.index('spektraCameraOwner.resumeCamera();') < resume.index('processExecutor.execute')
close=method(cc,'    public void closeCamera()')
assert 'spektraCameraOwner.retireForHandoff();' in close
# Generic legacy request writers must early-return under Spektra.
for sig,anchor in [
('    public void reset3Aparams()','setAEMode(mPreviewRequestBuilder'),
('    public void setPreviewAEModeRebuild(','setAEMode(mPreviewRequestBuilder'),
('    public void applyFpsRange()','mPreviewRequestBuilder.set('),
('    public void resetPreviewAEMode()','setAEMode(mPreviewRequestBuilder')]:
    m=method(cc,sig); assert 'isSpektraModeActive()' in m and 'return;' in m and m.index('return;') < m.index(anchor),(sig,anchor)
# No Spektra dependency may enter 26680 Motion stable-preview authority.
stable=method(cc,'    private void updateMotion26680StablePreviewAuthority(')
assert 'Spektra' not in stable

# Modified control files preserve legacy behavior after a Spektra-only early return.
pcb=text(base,'app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
pcc=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
for sig in ['    public void setShutter(','    public void setISO(','    public void setFocus(','    public void setEV(']:
    cm=method(pcc,sig); bm=method(pcb,sig)
    assert 'isSpektraModeActive()' in cm and 'return;' in cm
    # Every legacy Camera2 mutation anchor from the old method still survives after Spektra guard.
    for anchor in ['mPreviewRequestBuilder','rebuildPreviewBuilder']:
        if anchor in bm: assert anchor in cm,(sig,anchor)

tfb=text(base,'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java')
tfc=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java')
for sig in ['    private void applyFocus(','    private void resetAutoFocus(']:
    cm=method(tfc,sig); bm=method(tfb,sig); assert 'isSpektraModeActive()' in cm and 'return;' in cm
    for anchor in ['mPreviewRequestBuilder','buildMeteringRegion','focusLocked']:
        if anchor in bm: assert anchor in cm,(sig,anchor)

# Critical unrelated 26680 owners remain byte-identical.
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/preview/MainRenderer.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/modeswitcher/LiquidModePicker.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    same(p)
# Existing 257-shader universe is unchanged; only 14 Spektra assets are additions.
bsh={str(p.relative_to(base)) for p in (base/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
csh={str(p.relative_to(cand)) for p in (cand/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(bsh)==257 and len(csh)==271 and bsh <= csh and len(csh-bsh)==14
print('PASS 26681 regressions: 26680 stable-preview/shutter/HDR owners hardlocked; Spektra delegates before legacy mutation; only 14 shader additions')
