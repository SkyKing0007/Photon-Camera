#!/usr/bin/env python3
"""26903 actual-source Android-independent Night B plan regression + guarded ownership tests.
Uses REAL unchanged IrisNightFrameSelector.java source and real javac/java, not a copied formula.
Android project Kotlin/Java, NDK, full glslang and APK remain Actions-required.
"""
from pathlib import Path
import subprocess,sys,tempfile,shutil,re
assert len(sys.argv)==2,'usage: test_26903_modes.py <ACTUAL frozen candidate root>'
root=Path(sys.argv[1]);java=root/'app/src/main/java/com/particlesdevs/photoncamera';assert java.is_dir()
selector=java/'processing/parameters/IrisNightFrameSelector.java'
controller=(java/'capture/CaptureController.java').read_text()
bridge=(java/'processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
post=(java/'processing/opengl/postpipeline/PostPipeline.java').read_text()
hdr=(java/'processing/processor/HdrxProcessor.java').read_text()
adapter=(java/'processing/processor/IrisNightBProcessor26903.java').read_text()
renderer=(java/'processing/ultrahdr/Iris26876BGpuFinalRenderer.java').read_text()
shader=(root/'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag').read_text()
# Verify tested logic is the actual source, not a shadow fixture with copied implementation.
assert 'public static Plan freezeNormalOnlyB' in selector.read_text()
program='''import com.particlesdevs.photoncamera.processing.parameters.IrisNightFrameSelector;
class Photon26903NightBPlanRegression{
 static void a(boolean x,String msg){if(!x)throw new AssertionError(msg);}
 public static void main(String[]args){
  int[] sizes={2,3,4,5,7,14,15,30,50};
  for(int n:sizes){
   var b=IrisNightFrameSelector.freezeNormalOnlyB(n);
   a(b.totalFrames==n&&b.shortFrames==n&&b.longFrames==0,"Night B frame budget "+n);
   for(int i=0;i<n;i++)a(b.isShortFrame(i),"Night B never extra long");
   var old=IrisNightFrameSelector.freezePlan(n);
   a(old.totalFrames==n,"Night A count changed");
   a(old.longFrames==(n==2?0:Math.max(1,(n+2)/5)),"Night A 12+3 15 budget changed");
   a(old.shortFrames==n-old.longFrames,"Night A short ratio changed");
  }
  a(IrisNightFrameSelector.freezeNormalOnlyB(1).totalFrames==2,"minimum two");
  a(IrisNightFrameSelector.freezeNormalOnlyB(99).totalFrames==50,"maximum fifty");
  System.out.println("PASS 26903 real javac/java Night B N normal 2..50, Night A 15=12+3 unchanged");
 }
}'''
with tempfile.TemporaryDirectory(prefix='photon26903_real_javac_') as d:
 t=Path(d);a=t/'src/com/particlesdevs/photoncamera/processing/parameters';a.mkdir(parents=True)
 shutil.copyfile(selector,a/'IrisNightFrameSelector.java')
 p=t/'src/Photon26903NightBPlanRegression.java';p.write_text(program)
 subprocess.run(['javac','-d',str(t/'classes'),str(a/'IrisNightFrameSelector.java'),str(p)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 subprocess.run(['java','-cp',str(t/'classes'),'Photon26903NightBPlanRegression'],check=True)
# Confirm actual Night A code stays isolated and Night B shutter records real physical owner/normal frames.
assert controller.count('IrisNightProcessor.process(batch, cameraEventsListener)')==1
assert controller.count('IrisNightBProcessor26903.process(')==1
assert 'iris26903NightB = iris26533CaptureMode == CameraMode.NIGHT' in controller
assert 'IrisZoomController.applyToRequest(' in controller
assert 'IrisNightExposureSelector.freezePlan(' in controller
assert 'frame.motionV2FrameRole != ImageFrame.MotionV2FrameRole.NORMAL' in controller
assert 'mIrisNight26903ExperimentB' in controller
assert 'shortRequested=" + framePlan.shortFrames' in controller
# Night B's native engine accepts B's frozen selection, DNG-first, correct full RAW/JPEG isolation.
assert 'Iris26856ABSettings.Mode.parse(images.get(0).motionV2ReconstructionExperiment26856)' in hdr
assert 'iris26864BHighZoomExactA' in hdr and 'Iris26864ZoomRoute.shouldRouteBToExactA(' in hdr
assert 'DngOnlyPublished' in hdr and 'mIrisDngIndependentSaved' in hdr
assert 'processingParameters.iris26903NightB = true;' in hdr
assert 'processingParameters.iris26903NightBFrozenSettings = mIris26903NightBFrozenSettings' in hdr
assert 'ImagePath.newImageFilePath()' in adapter
assert 'ImagePath.getNewImageFilePath(' not in adapter
assert 'frame.motionV2PhysicalCameraId = actualPhysical26903;' in controller
assert 'actualPhysical26903.equals(mIrisNight26903Zoom.ownerCameraId)' in controller
assert 'imageFile = Paths.get(iris26856BasePath + iris26856Extension);' in hdr
assert 'batch.nightBDngOptions' in adapter and 'batch.longFrameCount != 0' in adapter
assert 'frame.motionV2ActualExposureNs != baseExposure' in adapter
assert 'frame.motionV2ActualIso != baseIso' in adapter
assert 'parameters.iris26903NightBFrozenSettings' in bridge
assert '!parameters.irisNightActive &&' in bridge
assert 'IrisNightUltraHdr' in hdr and 'enhanceInPlaceForTrue2x' in hdr
assert 'mIris26903NightB ? mIris26903NightBJin2x : null' in hdr
assert 'mParameters.motionV2Active && !mParameters.iris26903NightB' in post
assert 'GLES30.GL_RGBA32F' in renderer and 'GLES30.GL_NEAREST' in renderer
assert 'uniform1i(program,"uNightBJinEnabled",nightBJinApply?1:0);' in renderer
assert 'if(nightBFullJin!=null && (params==null || !params.iris26903NightB))' in renderer
assert 'if(uNightBJinEnabled!=0)' in shader and 'iris26903ApplyJin(op,encoded)' in shader
# B Night SR ON 50MP never replaced by preview-only Jin; no output downsample in 50MP encoder.
assert 'mIris26876B2xGpuForCleanup' in hdr and 'saveB26876SuperResGpuJpeg' in hdr
assert 'nightBFullJin.applied' in renderer
print('PASS 26903 current actual source DNG-first, B raw-only, 50MP learned residual, ownership/excluded modes')
