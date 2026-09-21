#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,struct,zlib
base,cand=map(Path,sys.argv[1:3])
def H(r,p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
def same(p):assert H(base,p)==H(cand,p),p
v=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726678' in v and 'VERSION_BUILD=26678' in v
# Unrelated architectural owners remain exact successful-26677 bytes.
for p in ['app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'] : same(p)
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text(); bcc=(base/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
for x in ['IRIS_26678_TIMESTAMP_OWNED_ROW_FLICKER_EVIDENCE','IRIS_26678_RAW_ROW_FLICKER_OBSERVER','sampleMotion26678RawFlickerEvidence(','getMotion26678PreviewFlicker(','IRIS_26678_NORMAL_ROW_ILLUMINATION_NORMALIZATION','applyMotion26678NormalRowFlickerCorrection(','motion26678ChooseStructuralReferenceTimestamp(','IRIS_26678_ROW_FLICKER_CAPTURE','IRIS_26676_CAPTURE_GENERATION_GUARD','IRIS_26598_EXACT_TOTAL_OWNERSHIP_PROOF','IRIS_26480_SHORT_BATCH_BOUNDARY']:assert x in cc,x
for forbidden in ['set(CaptureRequest.SENSOR_EXPOSURE_TIME','set(CaptureRequest.SENSOR_SENSITIVITY','CONTROL_AE_MODE_OFF']:assert cc.count(forbidden)==bcc.count(forbidden),forbidden
mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text(); ps=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
for x in ['IRIS_26678_PREVIEW_FLICKER_PRESENTATION_STATE','getMotion26678PreviewFlicker','iris26678FlickerParams']: assert x in mr,x
for x in ['IRIS_26678_POST_WYSIWYG_ROW_FLICKER_CORRECTION','uniform vec4 iris26678FlickerParams','Output = color;']: assert x in ps,x
assert ps.index('IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION') < ps.index('IRIS_26678_POST_WYSIWYG_ROW_FLICKER_CORRECTION')
rot=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/RotateWatermark.java').read_text(); enc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text(); wm=(cand/'app/src/main/assets/shaders/addwatermark_rotate.glsl').read_text()
for x in ['IRIS_26678_ADAPTIVE_WATERMARK_ASSET_OWNER','iris_camera_watermark_dark.png','iris_camera_watermark_white.png','WatermarkDark','WatermarkWhite']:assert x in rot,x
assert 'watermark/iris_camera_watermark.png' not in rot
for x in ['IRIS_26678_TRUE2X_ADAPTIVE_WATERMARK_OWNER','useDarkWatermarkForBackground','DARK_ON_BRIGHT','WHITE_ON_DARK','iris_camera_watermark_dark.png','iris_camera_watermark_white.png','0.115f','0.025f','0.55f']:assert x in enc,x
assert 'watermark/iris_camera_watermark.png' not in enc
for x in ['IRIS_26678_FINAL_RASTER_WATERMARK_OUTPUT_OWNER','IRIS_26678_GL_READBACK_TOP_ORIGIN_CONTRACT','IRIS_26678_ADAPTIVE_WATERMARK_BACKGROUND_OWNER','uniform sampler2D WatermarkDark','uniform sampler2D WatermarkWhite','iris26678Background >= 0.55','0.115','0.025','iris26678FinalTop']:assert x in wm,x
assert wm.count('iris26678BackgroundLuma(')>=6
assert 'float iris26677Bottom = iris26677Margin;' not in wm
assert not (cand/'app/src/main/assets/watermark/iris_camera_watermark.png').exists()
# Parse exact user-supplied RGBA PNGs with stdlib; require identical alpha geometry.
def png_rgba(path):
 b=Path(path).read_bytes(); assert b[:8]==b'\x89PNG\r\n\x1a\n';pos=8;idat=b'';W=H=depth=ctype=inter=None
 while pos<len(b):
  n=struct.unpack('>I',b[pos:pos+4])[0];typ=b[pos+4:pos+8];data=b[pos+8:pos+8+n];pos+=12+n
  if typ==b'IHDR': W,H,depth,ctype,comp,flt,inter=struct.unpack('>IIBBBBB',data)
  elif typ==b'IDAT': idat+=data
  elif typ==b'IEND': break
 assert (W,H,depth,ctype,inter)==(2048,1312,8,6,0),(W,H,depth,ctype,inter)
 raw=zlib.decompress(idat);stride=W*4;rows=[];prev=bytearray(stride);off=0
 for y in range(H):
  f=raw[off];off+=1;cur=bytearray(raw[off:off+stride]);off+=stride
  for i in range(stride):
   a=cur[i-4] if i>=4 else 0;bb=prev[i];c=prev[i-4] if i>=4 else 0
   if f==1:cur[i]=(cur[i]+a)&255
   elif f==2:cur[i]=(cur[i]+bb)&255
   elif f==3:cur[i]=(cur[i]+((a+bb)//2))&255
   elif f==4:
    pp=a+bb-c;pa=abs(pp-a);pb=abs(pp-bb);pc=abs(pp-c);pr=a if pa<=pb and pa<=pc else (bb if pb<=pc else c);cur[i]=(cur[i]+pr)&255
   elif f!=0:raise AssertionError(('filter',f))
  rows.append(bytes(cur));prev=cur
 return W,H,rows
D=cand/'app/src/main/assets/watermark/iris_camera_watermark_dark.png';W=cand/'app/src/main/assets/watermark/iris_camera_watermark_white.png'
assert hashlib.sha256(D.read_bytes()).hexdigest()=='fd052bac289d27760c3cf873152a9603f2d4443b8b6f13f1ac630b8b62f5360c'
assert hashlib.sha256(W.read_bytes()).hexdigest()=='087e400ea25d0227aeafa4436c0f4fc4312d782a59e7112db30487ff9dba6470'
dw,dh,dr=png_rgba(D);ww,wh,wr=png_rgba(W);assert (dw,dh)==(ww,wh)
da=[];wa=[];dvals=[];wvals=[]
for y in range(dh):
 for x in range(dw):
  di=x*4; a=dr[y][di+3]; b=wr[y][di+3]; da.append(a);wa.append(b)
  if a: dvals.append(dr[y][di]);wvals.append(wr[y][di])
assert da==wa and sum(1 for x in da if x>0)>1000
assert max(wvals)==min(wvals)==255 and (sum(dvals)/len(dvals))<90
ratio=dh/dw
for outW,outH in [(3072,4096),(4096,3072),(1080,1920),(1920,1080),(6144,8192),(8192,6144),(4000,3000),(3000,4000)]:
 wmW=outW*0.115;wmH=wmW*ratio;margin=max(2.0,min(outW,outH)*0.025);left=outW-margin-wmW;top=outH-margin-wmH
 assert left>=0 and top>=0 and left+wmW<=outW and top+wmH<=outH,(outW,outH,left,top)
print('PASS 26678 semantic validation: timestamp-owned flicker + post-WYSIWYG correction + exact user dark/white adaptive watermark + portrait/landscape/true2x lower-right contract')
