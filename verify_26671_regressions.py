#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,os
if len(sys.argv)!=3: raise SystemExit('usage: verify_26671_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
# 1. Successful 26670 is hard behavioral authority outside the five-file scope.
changed=set(x for x in (root/'R1_26671_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
for p in sorted((base/'app').rglob('*')):
 if not p.is_file(): continue
 rel=str(p.relative_to(base))
 if rel not in changed: assert sh(base,rel)==sh(cand,rel),rel
# Critical camera/motion/denoise/Laplacian/viewfinder/manual owners are exact 26670 bytes.
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java',
'app/src/main/res/layout/manual_palette.xml']:
 assert sh(base,p)==sh(cand,p),p
# 2. Existing 26670 capture and NORMAL-master bracket ownership must still be present.
cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26670_CAPTURE_TRANSACTION_PREVIEW_RESTORE','IRIS_26670_ISOLATED_POST_SHUTTER_HDR_TRANSACTION','livePreviewOwner=SUCCESSFUL_26660_HAL_USER_AE','adaptiveLong=false','shortTemporalAccumulator=false']:
 assert t in cap,t
bridge=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['shortTemporalOwner=false','longFrame?.let { orderedPhysical += it to RawBurstFrameRole.SHADOW_LONG }','shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }']:
 assert t in bridge,t
stack=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue','val mergedFrameCount = normalFrameCount + shadowLongFrameCount','IRIS_26651_NORMAL_MASTER_SHORT_FUSION']:
 assert t in stack,t
# 3. Highlight fix is global/pointwise and cannot revive local/spatial artifacts.
def func(text,name):
 st=text.index('float '+name+'('); i=text.index('{',st); d=0
 for j in range(i,len(text)):
  if text[j]=='{': d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[st:j+1]
 raise AssertionError(name)
for p,name in [('app/src/main/assets/shaders/motionv2/render.glsl','iris26653MapMotionSdrFinalGuide'),('app/src/main/assets/shaders/motionv2/gainmap.glsl','iris26653MapMotionSdrGuide')]:
 s=rd(cand,p); f=func(s,'iris26660ObjectColorGamma')
 for bad in ['texture(','texelFetch(','imageLoad(','imageStore(','dFdx(','dFdy(','fwidth(']: assert bad not in f,(p,bad)
 for t in ['IRIS_26671_SINGLE_HIGHLIGHT_LUMINANCE_OWNER','releaseStart=0.78','return mix(gammaOwned,y,release);']: assert t in f,(p,t)
 # Existing final highlight curve itself is byte/text exact.
 assert func(rd(base,p),name)==func(s,name),p
# Numerical regression: exact 26670 through .78 and monotone release to mapped white.
def old(y):
 y=max(y,0.0)
 if y<=1.0:
  w=min(max(y,0.0),1.0)**6; g=.90*max(y,1e-8)**2.5; return y+(g-y)*w
 return .90+(y-1.0)*(6.0*(.90-1.0)+.90*2.5)
def new(y):
 y=max(y,0.0); g=old(y)
 if y<=.78:return g
 if y>=1:return y
 t=(y-.78)/.22; q=t*t*(3-2*t); return g+(y-g)*q
for i in range(7801):
 y=i/10000.0; assert new(y)==old(y),y
prev=new(0.0); mind=999
for i in range(1,20001):
 y=i/10000.0; cur=new(y); d=(cur-prev)*10000; assert cur>=prev-1e-12,(y,prev,cur); mind=min(mind,d); prev=cur
assert mind>0.55 and new(.90)>old(.90) and new(.95)>old(.95) and abs(new(1)-1)<1e-12
# 4. Histogram UI remains read-only, now hard-clipped inside pill and uses exact existing dropdown surface.
h=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java')
for t in ['if (inFlight) return','PixelCopy.request(preview, copyBitmap','pixelScratch','IRIS_26671_HISTOGRAM_INNER_PILL_CLIP','canvas.clipPath(innerClipPath)','canvas.restoreToCount(save)','canvas.drawRoundRect(borderRect']:
 assert t in h,t
for bad in ['CaptureRequest','CONTROL_AE','CONTROL_AF','CONTROL_AWB']: assert bad not in h,bad
layout=rd(cand,'app/src/main/res/layout/camera_fragment.xml'); st=layout.index('<com.particlesdevs.photoncamera.ui.camera.views.IrisLiveHistogramView'); block=layout[st:layout.index('/>',st)+2]
assert 'android:background="@drawable/exif_background"' in block and 'iris_outline_pill' not in block
assert sh(base,'app/src/main/res/drawable/exif_background.xml')==sh(cand,'app/src/main/res/drawable/exif_background.xml')
# 5. Permanent added-file rollback completeness regression.
def run(cmd,cwd,**kw): return subprocess.run(cmd,cwd=cwd,check=True,**kw)
with tempfile.TemporaryDirectory(prefix='iris26671_added_file_reg_') as td:
 t=Path(td); (t/'app').mkdir(); (t/'app/a.txt').write_text('a\n'); run(['git','init','-q'],t); run(['git','config','user.email','iris@example.invalid'],t); run(['git','config','user.name','Iris Handoff'],t); run(['git','add','app'],t); env=os.environ.copy(); env.update({'GIT_AUTHOR_DATE':'2000-01-01T00:00:00Z','GIT_COMMITTER_DATE':'2000-01-01T00:00:00Z'}); run(['git','commit','-q','-m','base'],t,env=env); (t/'app/new.txt').write_text('new\n'); p=run(['git','ls-files','--others','--exclude-standard','-z','--','app'],t,stdout=subprocess.PIPE); un=[x.decode() for x in p.stdout.split(b'\0') if x]; assert un==['app/new.txt']; run(['git','add','-N','--',*un],t); d=run(['git','diff','--binary','--full-index','--no-ext-diff','--','app'],t,stdout=subprocess.PIPE).stdout; assert d.count(b'new file mode 100644')==1
print('PASS 26671 regressions: successful-26670 camera/motion/noise/Laplacian/viewfinder/manual bytes hardlocked; NORMAL-master HDR ownership retained; pointwise upper gamma release exact<=0.78 monotone/no plateau; histogram read-only inner-pill clip + exact settings-dropdown surface; added-file patch regression retained')
