#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv) != 4:
    raise SystemExit('usage: r3_26772_validate.py BASE FAILED26772 R3CANDIDATE')
base, failed, cand = map(Path, sys.argv[1:])
rel = Path('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java')
layout = Path('app/src/main/res/layout/layout_bottombuttons.xml')
old_gallery = Path('app/src/main/java/com/particlesdevs/photoncamera/gallery/binding/CustomBinding.java')

def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def universe(root):
    return {str(p.relative_to(root)):h(p) for p in (root/'app').rglob('*') if p.is_file()}
F, C = universe(failed), universe(cand)
assert len(F) == len(C) == 1779, (len(F), len(C))
diff = sorted(k for k in set(F)|set(C) if F.get(k) != C.get(k))
assert diff == [str(rel)], diff
src = (cand/rel).read_text()
assert src.count('@BindingAdapter("imageFromBitmap")') == 1
assert src.count('IRIS_26772_R3_GALLERY_THUMBNAIL_BITMAP_BINDING_OWNER') == 1
assert 'import android.graphics.Bitmap;' in src
assert 'import android.widget.ImageView;' in src
assert 'public static void setImageBitmap(ImageView view, Bitmap bitmap)' in src
assert 'view.setImageBitmap(bitmap);' in src
assert not (cand/old_gallery).exists(), 'legacy Gallery binding owner restored'
xml = (cand/layout).read_text()
assert xml.count('imageFromBitmap="@{uimodel.bitmap}"') == 1
owners=[]
for p in (cand/'app/src/main').rglob('*'):
    if p.is_file() and p.suffix in ('.java','.kt','.xml'):
        try: t=p.read_text()
        except UnicodeDecodeError: continue
        if '@BindingAdapter("imageFromBitmap")' in t:
            owners.append(str(p.relative_to(cand)))
assert owners == [str(rel)], owners
# Preserve intended 26772 version/build exactly; R3 is a repair revision, not a new behavioral build.
vp=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726772' in vp and 'VERSION_BUILD=26772' in vp
print('PASS R3: exact one-file repair over intended 26772 candidate; imageFromBitmap ownership migrated to surviving camera binding; Gallery remains deleted')
