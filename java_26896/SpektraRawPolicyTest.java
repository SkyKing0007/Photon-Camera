import java.util.*;
import com.unspektrawesome.camera.*;
public class SpektraRawPolicyTest {
  static void test(boolean b) {if(!b)throw new AssertionError("Wrong stream");}
  public static void main(String[] args){
    RawOutput small = new RawOutput(RawFormat.RAW10,new Size2d(4080,3072),33333333,0,false);
    RawOutput huge = new RawOutput(RawFormat.RAW10,new Size2d(8160,6144),99999999,0,true);
    RawOutput hugeSensor = new RawOutput(RawFormat.RAW_SENSOR,new Size2d(8192,6144),99999999,0,true);
    List<RawOutput> pixel=Arrays.asList(small,huge,hugeSensor);
    test(RawPreviewPolicy.selectCaptureOutput(pixel,EnumSet.allOf(RawFormat.class),false)==small);
    test(RawPreviewPolicy.selectCaptureOutput(pixel,EnumSet.allOf(RawFormat.class),true)==huge);
    boolean rejected=false;try{RawPreviewPolicy.selectCaptureOutput(Arrays.asList(small),EnumSet.allOf(RawFormat.class),true);}catch(IllegalArgumentException e){rejected=true;}
    test(rejected);
    test(RawPreviewPolicy.selectCaptureOutput(pixel,EnumSet.of(RawFormat.RAW_SENSOR),true)==hugeSensor);
    test(RawPreviewPolicy.selectCaptureOutput(pixel,EnumSet.of(RawFormat.RAW10),false)==small);
    System.out.println("PASS 26896 real JVM Pixel12.5/50 selection, unsupported and RAW-format fail-closed");
  }
}
