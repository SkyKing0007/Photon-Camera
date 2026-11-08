import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.CaptureRequest;
import android.util.Range;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.processing.parameters.IrisNightExposureSelector;
public class Photon26909NightRegression {
 static void check(boolean v,String why){if(!v)throw new AssertionError(why);}
 static CameraCharacteristics cam(long cap,int isoMin,int isoMax){var c=new CameraCharacteristics();c.set(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE,new Range<>(100_000L,cap));c.set(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE,new Range<>(isoMin,isoMax));c.set(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY,isoMax);return c;}
 static CaptureController ctl(long shutter,int iso){var c=new CaptureController();c.mPreviewExposureTime=shutter;c.mPreviewIso=iso;return c;}
 public static void main(String[] args) {
  var c=cam(1_000_000_000L,100,12800);var p=ctl(8_333_000L,6413);
  var b=IrisNightExposureSelector.freezeNormalOnlyB(p,c,0.0f,false,900,null);
  check(b.shortExposureNs>=99_000_000L&&b.shortExposureNs<=100_000_000L,"B no gyro shake cap even shakiness=900");
  check(b.iso>=525&&b.iso<=550,"B ISO target ~534 not ~7000: "+b.iso);
  check(b.longExposureNs==b.shortExposureNs&&b.longIso==b.shortIso,"B all normal no LONG cohort");
  var bright=IrisNightExposureSelector.freezeNormalOnlyB(p,c,-0.67f,false,900,null);
  check(bright.shortExposureNs<=100_000_000L && bright.iso<b.iso,"existing exposure compensation protects highlights");
  var a=IrisNightExposureSelector.freezePlan(p,c,0.0f,false,900,null,true);
  check(a.shortExposureNs<100_000_000L && a.longExposureNs>a.shortExposureNs,"Night A two physical groups unchanged");
  var min50=IrisNightExposureSelector.freezeNormalOnlyB(ctl(1_000_000L,100),cam(100_000_000L,50,6400),0f,false,999,null);
  check(min50.iso<=100&&min50.shortExposureNs>=1_000_000L,"night lowest ISO need not be fixed 100");
  var smaller=IrisNightExposureSelector.freezeNormalOnlyB(p,cam(33_333_333L,100,12800),0f,false,999,null);
  check(smaller.shortExposureNs<=33_333_333L,"sensor lower shutter maximum guarded");
  var manual=ctl(8_333_000L,6413);manual.getParamController().shutter=250_000_000L;
  var manualB=IrisNightExposureSelector.freezeNormalOnlyB(manual,c,0f,false,900,null);
  check(manualB.shortExposureNs==250_000_000L,"explicit user manual shutter honored independently of automatic cap");
  var request=new CaptureRequest.Builder();IrisNightExposureSelector.applyShortPlan(request,b);
  check(request.get(CaptureRequest.CONTROL_AE_MODE)==0,"actual Night capture must request manual pair");
  check(request.get(CaptureRequest.SENSOR_EXPOSURE_TIME)==b.shortExposureNs,"Night request shutter exact");
  check(request.get(CaptureRequest.SENSOR_SENSITIVITY)==b.shortIso,"Night request ISO exact");
  System.out.println("PASS 26909 actual Night selector: B all-normal low ISO 1/10, arbitrary shake, compensated highlight, Night A 6+2 groups, manual preference, sensor caps");
 }
}
