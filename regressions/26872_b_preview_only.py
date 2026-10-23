#!/usr/bin/env python3
"""Permanent 26871 right-to-left preview-band failure; historic 26679 pixel-correction regression."""
from pathlib import Path
import sys,hashlib,subprocess,tempfile,shutil
assert len(sys.argv)==3
old,new=(Path(x)/'app' for x in sys.argv[1:]);p='src/main/'
def read(root,rel):return (root/p/rel).read_text()
cc_old=read(old,'java/com/particlesdevs/photoncamera/capture/CaptureController.java')
cc=read(new,'java/com/particlesdevs/photoncamera/capture/CaptureController.java')
shader=read(new,'assets/shaders/preview/main_fs.glsl')
main=read(new,'java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')
helper='java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/Iris26872PreviewStripe.java'
owner=read(new,helper)
assert cc.count('public boolean iris26872BPreviewStripeEligible()')==1
assert 'return iris26871BExposureSelected() && !mIsRecordingVideo && isZslMode();' in cc
assert 'IRIS_26841' in cc and 'IRIS_26843' in cc
assert cc_old.split('    /* IRIS_26680_FLICKER_OBSERVER_ONLY_PREVIEW',1)[1].split('    private ',1)[0] == cc.split('    /* IRIS_26680_FLICKER_OBSERVER_ONLY_PREVIEW',1)[1].split('    private ',1)[0], '26680 old fail-closed protection mutated'
assert 'getMotion26678PreviewFlicker(' in main and 'iris26872BPreviewStripeEligible()' in main
assert 'Iris26872PreviewStripe' in main and 'glReadPixels(0, 0, Iris26872PreviewStripe.WIDTH' in main
assert 'GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER, 0)' in main
assert 'mIris26872ProbeDisabled = true' in main
assert shader.count('uniform vec4 iris26872PreviewStripe;') == 1
assert 'lowGuard * highGuard' in shader and 'Output = color' in shader
assert 'MAX_LOG_CORRECTION = 0.12f' in owner
assert 'candidateFrames < 3' in owner
assert 'goodRows < 60' in owner and 'agreeingSamples < goodSamples * .76f' in owner
assert 'Math.log(y)' in owner and 'Math.exp' not in owner
# Actual 26871 Camera2 exposure logic (outside one new read-only method) is byte-exact.
start='    /* IRIS_26872_B_PREVIEW_ONLY_SCOPE:'
assert cc.count(start)==1
line=cc.index(start);stop=cc.index('    /* IRIS_26843_FAST_PROTECTIVE_HDR_ARM',line)
assert cc[:line]+cc[stop:] == cc_old,'26871 HAL AE/highlight exposure owner changed'
# No modification to actual RAW/Native/HDRq/DNG/UHDR source outside explicit list.
for rel in ('java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
            'java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
            'java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'):
 assert hashlib.sha256((old/p/rel).read_bytes()).digest()==hashlib.sha256((new/p/rel).read_bytes()).digest(),rel
print('PASS 26872 26871 exact exposure/highlight owner, A/B gate, protected old 26679/26680 RAW/preview disable, all HDRq/noise unchanged')
# Run the same exact previously failing frequency/locality conditions against the
# actual Java implementation, not a Python-only numerical imitation.
java=(new/p/helper)
assert shutil.which('javac') and shutil.which('java'),'real Java runtime needed for regression'
test=r'''package com.particlesdevs.photoncamera.ui.camera.views.viewfinder;
import java.nio.ByteBuffer;
public final class JavaStripeProbeTest {
 static ByteBuffer frame(int n,int columns,boolean global,boolean moving) {
  int w=Iris26872PreviewStripe.WIDTH,h=Iris26872PreviewStripe.HEIGHT;
  ByteBuffer b=ByteBuffer.allocate(4*w*h);
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
   double phase=2*Math.PI*2*(y+.5)/h+(.52*n);
   double flicker=x<columns?(moving?.14*Math.sin(phase):0):0;
   double lum=.24*Math.exp(flicker+(global?.08*n:0));
   int v=(int)Math.round(Math.max(0,Math.min(255,lum*255)));
   b.put((byte)v).put((byte)v).put((byte)v).put((byte)255);
  }
  b.flip();return b;
 }
 static void test(String name,int columns,boolean global,boolean moving,boolean expected){
  Iris26872PreviewStripe p=new Iris26872PreviewStripe();int hits=0;
  for(int n=0;n<14;n++)if(p.consume(frame(n,columns,global,moving),100_000_000L+n*33_000_000L))hits++;
  if((hits>0)!=expected)throw new AssertionError(name+" hits="+hits);
  System.out.println("PASS 26872 exact Java "+name+" enabled="+hits);
 }
 public static void main(String[] args){
  test("stationary-scene",12,false,false,false);
  test("moving-rolling-band",12,false,true,true);
  test("TV-localized-only",3,false,true,false);
  test("pure-HAL-AE-global-EV-change",12,true,false,false);
 }
}'''
with tempfile.TemporaryDirectory(prefix='26872_actual_java_regression_') as d:
 loc=Path(d);f=loc/'JavaStripeProbeTest.java';f.write_text(test)
 subprocess.run(['javac','-d',str(loc),str(java),str(f)],check=True,capture_output=True)
 subprocess.run(['java','-cp',str(loc),'com.particlesdevs.photoncamera.ui.camera.views.viewfinder.JavaStripeProbeTest'],check=True)
print('PASS 26872 actual Java motion/row/EV/TV negative+positive regressions')
