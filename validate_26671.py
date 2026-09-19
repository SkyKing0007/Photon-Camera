#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26671.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
# Exact authority-seeded scope.
bm={str(p.relative_to(base)):sh(base,str(p.relative_to(base))) for p in sorted((base/'app').rglob('*')) if p.is_file()}
cm={str(p.relative_to(cand)):sh(cand,str(p.relative_to(cand))) for p in sorted((cand/'app').rglob('*')) if p.is_file()}
assert len(bm)==len(cm)==1725 and set(bm)==set(cm)
changed=[x for x in (root/'R1_26671_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert len(changed)==5 and sorted(p for p in bm if bm[p]!=cm[p])==sorted(changed)
# Successful 26670 is hard behavioral golden outside five paths.
for p in bm:
 if p not in changed: assert bm[p]==cm[p],p
for p in [
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
 'app/src/main/res/layout/manual_palette.xml',
 'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
 'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
 'app/src/main/assets/shaders/preview/main_fs.glsl']:
 assert sh(base,p)==sh(cand,p),('26670 hardlock drift',p)
# 26653 highlight owner itself is untouched inside both changed shaders; only post-map gamma release changes.
def func(text,name):
 st=text.index('float '+name+'('); i=text.index('{',st); d=0
 for j in range(i,len(text)):
  if text[j]=='{': d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[st:j+1]
 raise AssertionError(name)
for p,name in [('app/src/main/assets/shaders/motionv2/render.glsl','iris26653MapMotionSdrFinalGuide'),('app/src/main/assets/shaders/motionv2/gainmap.glsl','iris26653MapMotionSdrGuide')]:
 b=rd(base,p); c=rd(cand,p)
 assert func(b,name)==func(c,name),p
 assert 'IRIS_26671_SINGLE_HIGHLIGHT_LUMINANCE_OWNER' in c
 assert 'const float releaseStart=0.78;' in c
 assert 'float release=t*t*(3.0-2.0*t);' in c
 assert 'return mix(gammaOwned,y,release);' in c
# Curve proof: exact 26670 through 0.78, C1 smooth release, monotone/no plateau, white identity.
def old(y):
 y=max(y,0.0)
 if y<=1.0:
  w=min(max(y,0.0),1.0)**6; g=.90*max(y,1e-8)**2.5; return y+(g-y)*w
 return .90+(y-1.0)*(6.0*(.90-1.0)+.90*2.5)
def new(y):
 y=max(y,0.0); g=old(y)
 if y<=.78:return g
 if y>=1.0:return y
 t=(y-.78)/.22; rel=t*t*(3.0-2.0*t); return g+(y-g)*rel
for i in range(7801):
 y=i/10000.0; assert new(y)==old(y),(y,new(y),old(y))
prev=new(0.0); mind=1e9
for i in range(1,20001):
 y=i/10000.0; cur=new(y); slope=(cur-prev)*10000.0; assert cur+1e-12>=prev,(y,prev,cur); mind=min(mind,slope); prev=cur
assert mind>0.55,mind
assert abs(new(1.0)-1.0)<1e-12 and new(.90)>old(.90) and new(.95)>old(.95)
# Histogram: same settings-dropdown surface + rounded inner clip + read-only behavior.
h=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java')
for t in ['IRIS_26671_HISTOGRAM_INNER_PILL_CLIP','canvas.clipPath(innerClipPath)','canvas.restoreToCount(save)','canvas.drawRoundRect(borderRect','dp(2.2f)','dp(1.4f)','Color.argb(0xCC, 255, 255, 255)']:
 assert t in h,t
for bad in ['CaptureRequest','CONTROL_AE','CONTROL_AF','CONTROL_AWB']: assert bad not in h,bad
ET.parse(cand/'app/src/main/res/layout/camera_fragment.xml')
x=rd(cand,'app/src/main/res/layout/camera_fragment.xml'); st=x.index('<com.particlesdevs.photoncamera.ui.camera.views.IrisLiveHistogramView'); block=x[st:x.index('/>',st)+2]
assert 'android:background="@drawable/exif_background"' in block and 'iris_outline_pill' not in block
assert '#99000000' in rd(cand,'app/src/main/res/drawable/exif_background.xml')
assert sh(base,'app/src/main/res/drawable/exif_background.xml')==sh(cand,'app/src/main/res/drawable/exif_background.xml')
# Version exact.
v=rd(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726671' in v and 'VERSION_BUILD=26671' in v
print('VALIDATE_26671_OK exact successful-26670 hardlock outside 5 paths; exact 26670 <=0.78 highlight mapping; monotone upper gamma release; settings-dropdown histogram surface + inner pill clip; version 0.9726671/26671')
