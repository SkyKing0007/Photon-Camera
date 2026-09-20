#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,struct
base,cand=map(Path,sys.argv[1:3])
def H(r,p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
def same(p):assert H(base,p)==H(cand,p),p
v=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726677' in v and 'VERSION_BUILD=26677' in v
for p in ['app/src/main/assets/shaders/preview/main_fs.glsl','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/RotateWatermark.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java']:same(p)
wm=(cand/'app/src/main/assets/shaders/addwatermark_rotate.glsl').read_text();native=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for x in ['IRIS_26677_IRIS_WATERMARK_OUTPUT_OWNER','0.115','0.025','gl_FragCoord.y + float(yOffset)','(iris26677Frag.y - iris26677Bottom) / iris26677WmHeight']:assert x in wm,x
assert '1.0 - (iris26677Frag.y - iris26677Bottom) / iris26677WmHeight' not in wm
for x in ['IRIS_26677_IRIS_WATERMARK_OUTPUT_OWNER','0.115f','0.025f']:assert x in native,x
b=(cand/'app/src/main/assets/watermark/iris_camera_watermark.png').read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';W,H,D,C=struct.unpack('>IIBB',b[16:26]);assert (W,H,D,C)==(672,554,8,6)
print('PASS 26677 semantic validation: successful-26676 behavior hardlocked; watermark corrected only')
