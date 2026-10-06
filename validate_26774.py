#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

EXPECTED = [
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java',
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

if len(sys.argv)!=3: raise SystemExit('usage: validate_26774.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
a,b=universe(base),universe(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==EXPECTED,changed
assert all(k in a and k in b for k in EXPECTED)
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in b)

v=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726774' in v and 'VERSION_BUILD=26774' in v

cb=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java').read_text()
assert 'IRIS_26774_DOWNWARD_RIGHT_BOUND_HISTOGRAM_HINGE_OWNER' in cb
hb=body(cb,'public static void rotateHistogram(View view, int orientation)')
for token in [
    'if (orientation == -90)', 'view.setPivotX(width);', 'view.setPivotY(0f);',
    '.translationX(-height)', '.rotation(-90f)',
    'else if (orientation == 90)', 'view.setPivotX(0f);', 'view.setPivotY(height);',
    '.translationX(width - height)', '.translationY(-height)', '.rotation(90f)',
    'else if (orientation == 0)', '.translationX(0f)', '.translationY(0f)',
    '.withEndAction(() ->'
]: assert token in hb, token
# R6/26773 fix must remain: quarter-turns are property-bound, not full-model invalidation.
model=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/model/CameraFragmentModel.java').read_text()
assert 'IRIS_26773_ORIENTATION_ONLY_BINDING_INVALIDATION' in model
assert 'notifyPropertyChanged(BR.orientation);' in body(model,'public void setOrientation(int orientation)')
# 26773 Downloads materialization remains byte-identical and active.
storage=(cand/'app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java').read_text()
assert 'IRIS_26773_DOWNLOADS_DIRECTORY_MATERIALIZATION_OWNER' in storage

# Symbolic geometry regression using Android's positive-clockwise screen-coordinate transform.
# Both +/-90 targets must occupy the same right-most strip of the portrait rectangle and fall down.
def bbox(w,h,px,py,deg,tx,ty):
    import math
    a=math.radians(deg); c=math.cos(a); s=math.sin(a)
    pts=[]
    for x,y in ((0,0),(w,0),(0,h),(w,h)):
        xr=x-px; yr=y-py
        pts.append((px+c*xr-s*yr+tx, py+s*xr+c*yr+ty))
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return tuple(round(v,6) for v in (min(xs),min(ys),max(xs),max(ys)))
w,h=320.0,84.0
minus=bbox(w,h,w,0,-90,-h,0)
plus=bbox(w,h,0,h,90,w-h,-h)
expected=(w-h,0.0,w,w)
assert minus==expected,(minus,expected)
assert plus==expected,(plus,expected)

# Domain protection: no GLSL/native/storage/layout/model/Spektra/image pipeline path changed.
assert not any(k.endswith(('.glsl','.comp','.vert','.frag')) or '/shaders/' in k for k in changed)
assert not any(k.startswith('app/src/main/cpp/') for k in changed)
assert not any('dng' in k.lower() for k in changed)
assert not any('SimpleStorageHelper' in k or 'Spektra' in k or '/processing/' in k for k in changed)
print('PASS 26774 semantic/ownership regression: both quarter turns fall downward into identical right-bound strip; portrait returns to zero translation')
print('PASS 26774 exact runtime allowlist: 2 modified + 0 added + 0 deleted; 1777 protected files unchanged')
