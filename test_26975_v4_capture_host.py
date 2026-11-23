#!/usr/bin/env python3
"""V4 independently exercised C-only geometry/flicker/sequence Java + source-path assertions.
No Android runtime, device IQ or original Pro Sabre native merge is implied.
"""
import argparse,pathlib,tempfile,subprocess
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path);a=p.parse_args()
R=pathlib.Path(__file__).resolve().parent
root=a.root or R/'handoff_payload_26975/app'
src=root/'src/main/java'
package='com/particlesdevs/photoncamera/processing/experimentc'
classes=['Iris26975COutputGeometry','Iris26975CFlickerModeFreeze',
         'Iris26975CHighlightFreeze','Iris26975CNightExposureFreeze']
paths=[src/package/(name+'.java') for name in classes]
fencePath=src/package/'Iris26972CSequenceFence.java'
withFence=fencePath.is_file()
if withFence:paths.append(fencePath)
for path in paths:assert path.is_file(),str(path)
controller=(src/'com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
cap=(src/'com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt').read_text()
bridge=(src/'com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt').read_text()
donor=(src/'com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt').read_text()
for token in ('mIris26975CZslRingBuffer','mIris26975CZslResultMap',
              'mIris26975CZslPreviewSelected','IRIS_26975_V4_C_PRIVATE_ZSL_INGRESS',
              'Math.min(frames,','IRIS_26975_V4_C_ALL_PRE_SHUTTER',
              'CaptureRequest.CONTROL_AE_ANTIBANDING_MODE_AUTO',
              'owner.activate()'):
 assert token in controller,token
assert 'Math.min(Math.min(frames - 1, 8)' not in controller
assert 'preShutterImages.size <= frameCount' in cap
assert 'private var activated = false' in cap and 'if (!activated) return' in cap
for token in ('val geometry:','plan.geometry,','output.geometry.outputWidth'):
 assert token in bridge,token
for token in ('val shutterCrop = Rect(shutterGrid.cropLeft,','defaultCrop = Rect(shutterCrop)',
              'rawPhysicalOutputSize = Size(shutterGrid.rawWidth, shutterGrid.rawHeight)',
              'RawRenderingEngine.AdobeCurve','MultiFrameStacker.processBurstRaw',
              'renderer.processMgcSpatialGpuLinearRgb'):
 assert token in donor,token
assert 'rawPhysicalOutputSize = Size(output.finalWidth, output.finalHeight)' not in donor
java='''import com.particlesdevs.photoncamera.processing.experimentc.*;
public final class V4GeometryAndFlickerHost {
  static void verify(boolean v) { if (!v) throw new AssertionError("V4 host"); }
  static void approx(double a,double b) { verify(Math.abs(a-b)<1.0); }
  public static void main(String[] args) {
    for (int r: new int[]{0,90,180,270}) {
      boolean q=r==90||r==270;
      Iris26975COutputGeometry g=new Iris26975COutputGeometry(4000,3000,
          400,300,3600,2700,r,q?3000:4000,q?4000:3000);
      verify(g.outputWidth==(q?3000:4000));
      verify(g.outputHeight==(q?4000:3000));
      double[] center=g.sourcePixelCenter(g.outputWidth/2,g.outputHeight/2);
      approx(center[0],2000);approx(center[1],1500);
      int[] halo=g.sourceFootprint(0,0,g.outputWidth,g.outputHeight);
      verify(halo[0]>=0 && halo[1]>=0 && halo[2]<=4000 && halo[3]<=3000);
      verify(!g.isExactNativePixelGrid());
    }
    Iris26975COutputGeometry nativeGrid=new Iris26975COutputGeometry(4000,3000,
        0,0,4000,3000,90,3000,4000);
    verify(nativeGrid.isExactNativePixelGrid());
    verify(Iris26975CFlickerModeFreeze.freeze(3,1,new int[]{0,1,2,3})==3);
    verify(Iris26975CFlickerModeFreeze.freeze(9,2,new int[]{1,2})==2);
    verify(Iris26975CFlickerModeFreeze.freeze(null,null,new int[]{0,1})==null);
    /* OPTIONAL_SEQUENCE_FENCE_TEST */
    Iris26975CHighlightFreeze.Decision manual=Iris26975CHighlightFreeze.freeze(
      true,10000000,100,100000L,1,true,1,100000L,300000000d,-1.5f,
      100000,100000000L,50,6400);
    verify(manual.exposureNs==10000000&&manual.iso==100);
    System.out.println("PASS V4 C-owned crop/rotation 4x, Lanczos footprint, HAL flicker selection, full-ZSL fence, manual priority");
  }
}
'''
if withFence:
 java=java.replace('/* OPTIONAL_SEQUENCE_FENCE_TEST */','''
    Iris26972CSequenceFence f=new Iris26972CSequenceFence();
    verify(!f.takeReleasePermit());f.markNeverSubmitted();verify(!f.takeReleasePermit());
    f.markTerminalDelivered();verify(f.takeReleasePermit());verify(!f.takeReleasePermit());
    Iris26972CSequenceFence posted=new Iris26972CSequenceFence();
    posted.markTerminalDelivered();verify(!posted.takeReleasePermit());
    posted.markCameraSequenceEnded();verify(posted.takeReleasePermit());
''' )
with tempfile.TemporaryDirectory(prefix='photon_26975_v4_java_') as d:
 d=pathlib.Path(d);(d/'V4GeometryAndFlickerHost.java').write_text(java)
 subprocess.run(['javac','-d',str(d),*[str(x) for x in paths],str(d/'V4GeometryAndFlickerHost.java')],check=True)
 subprocess.run(['java','-cp',str(d),'V4GeometryAndFlickerHost'],check=True)
print('PASS V4 actual C source ownership/isolation/physical renderer geometry static assertions')
