#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, re, xml.etree.ElementTree as ET

EXPECTED = [
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/model/CameraFragmentModel.java',
'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java',
'app/src/main/res/layout/camera_fragment.xml',
'app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/layout/layout_main_topbar.xml',
'app/version.properties',
]

def universe(root):
    root=Path(root)
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root/'app').rglob('*') if p.is_file()}

def body(text, signature):
    i=text.find(signature)
    if i<0: raise AssertionError('missing '+signature)
    j=text.find('{',i); depth=0
    for k in range(j,len(text)):
        if text[k]=='{': depth+=1
        elif text[k]=='}':
            depth-=1
            if depth==0: return text[j:k+1]
    raise AssertionError('unclosed '+signature)

if len(sys.argv)!=3: raise SystemExit('usage: validate_26773.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
a,b=universe(base),universe(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==EXPECTED,changed
assert all(k in a and k in b for k in EXPECTED)
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in b)

v=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726773' in v and 'VERSION_BUILD=26773' in v

cb=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java').read_text()
assert 'IRIS_26773_IMMUTABLE_HISTOGRAM_HINGE_OWNER' in cb
hb=body(cb,'public static void rotateHistogram(View view, int orientation)')
assert 'view.setPivotX(view.getWidth());' in hb and 'view.setPivotY(0f);' in hb
assert 'setTranslationX(0f)' in hb and 'setTranslationY(0f)' in hb
assert 'setPivotX(0f)' not in hb and 'width * 0.5f' not in hb
assert 'IRIS_ROTATION_DURATION_MS = 350L' in cb
arb=body(cb,'public static void setAspectRatio(View view, String ratio)')
assert 'if (!ratio.equals(params.dimensionRatio))' in arb

model=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/model/CameraFragmentModel.java').read_text()
ob=body(model,'public void setOrientation(int orientation)')
assert 'notifyPropertyChanged(BR.orientation);' in ob and 'notifyChange()' not in ob
assert 'IRIS_26773_ORIENTATION_ONLY_BINDING_INVALIDATION' in ob
assert 'notifyPropertyChanged(BR.bitmap);' in model
assert 'notifyPropertyChanged(BR.settingsBarVisibility);' in model

orientation_bindings=0
for rel in ['app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/layout_bottombuttons.xml','app/src/main/res/layout/layout_main_topbar.xml']:
    text=(cand/rel).read_text()
    ET.fromstring(text)
    assert '@{uimodel}' not in text, rel
    orientation_bindings += text.count('@{uimodel.orientation}')
assert orientation_bindings==7,orientation_bindings

storage=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java').read_text()
sb=body(storage,'private static boolean ensureDownloadsDirectory(Context context, String child)')
for token in ['IRIS_26773_DOWNLOADS_DIRECTORY_MATERIALIZATION_OWNER','openOutputStream(marker, "w")','os.write(new byte[]','findDownloadsUri(context, markerPath)','openInputStream(verified)','is.read() >= 0']:
    assert token in sb,token
assert 'return getOrCreateDownloadsUri(context, child + "/.iris"' not in sb

# Domain protection: no GLSL/native/DNG runtime path is changed.
assert not any(k.endswith(('.glsl','.comp','.vert','.frag')) or '/shaders/' in k for k in changed)
assert not any(k.startswith('app/src/main/cpp/') for k in changed)
assert not any('dng' in k.lower() for k in changed)
print('PASS 26773 semantic/ownership/domain validation: all-mode fixed-hinge UI + orientation-isolated shell + verified Downloads materialization')
print('PASS 26773 exact runtime allowlist: 7 modified + 0 added + 0 deleted; 1772 protected files unchanged')
