import com.particlesdevs.photoncamera.capture.Iris26911Continuity;
import java.nio.ByteBuffer;
import java.util.HashMap;
public final class Photon26911ContinuityRegression {
 private static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 private static ByteBuffer grid(int v){
  ByteBuffer b=ByteBuffer.allocate(12*96*4);
  for(int i=0;i<12*96;i++){b.put((byte)v).put((byte)v).put((byte)v).put((byte)255);}
  return b;
 }
 public static void main(String[] args){
  final int off=0;
  check(Iris26911Continuity.exactManualFrame(off,100000000L,2244,off,100000000L,2244,100000000L,2244,off),"exact manual");
  check(!Iris26911Continuity.exactManualFrame(1,70000000L,3205,1,70000000L,3205,100000000L,2244,off),"old HAL prohibited");
  check(!Iris26911Continuity.exactManualFrame(off,70000000L,3205,off,70000000L,3205,100000000L,2244,off),"equal energy is not equal shutter");
  check(!Iris26911Continuity.exactManualFrame(off,100000000L,2244,off,90000000L,2244,100000000L,2244,off),"unhonored shutter");
  check(!Iris26911Continuity.exactManualFrame(off,100000000L,2244,off,100000000L,3205,100000000L,2244,off),"unhonored ISO");
  check(Iris26911Continuity.significantSceneChange(0.025f,0.12f,0f),"real scene brighter");
  check(Iris26911Continuity.significantSceneChange(0.14f,0.025f,0f),"real scene darker");
  check(!Iris26911Continuity.significantSceneChange(0.05f,0.06f,0f),"same night scene");
  check(Iris26911Continuity.significantSceneChange(0.05f,0.055f,0.015f),"full-well guard");
  check(!Iris26911Continuity.navigationRequiresRemeter(true,2),"one pan must not reset AE");
  check(Iris26911Continuity.navigationRequiresRemeter(true,3),"confirmed reframe can meter");
  check(!Iris26911Continuity.navigationRequiresRemeter(false,9),"motion evidence required");
  Iris26911Continuity.Preview preview=new Iris26911Continuity.Preview();
  HashMap<Long,Integer> phases=new HashMap<>();
  preview.sample(grid(110),1000000000L);
  preview.resolve(1000000000L,x->phases.getOrDefault(x,0),true,0.025f);
  check(preview.liftEv()==0f,"unknown timestamp not trusted");
  phases.put(1000000000L,1);preview.resolve(1050000000L,x->phases.getOrDefault(x,0),true,0.025f);
  preview.sample(grid(110),1100000000L);phases.put(1100000000L,1);
  preview.resolve(1100000000L,x->phases.getOrDefault(x,0),true,0.025f);
  preview.sample(grid(38),1200000000L);phases.put(1200000000L,2);
  preview.resolve(1200000000L,x->phases.getOrDefault(x,0),true,0.025f);
  check(preview.liftEv()>1f && preview.liftEv()<=3f,"measured ISP brightness transition compensated");
  preview.sample(grid(38),1300000000L);phases.put(1300000000L,2);
  preview.resolve(1300000000L,x->phases.getOrDefault(x,0),true,0.025f);
  check(preview.liftEv()>1f,"continuity stays after handoff");
  preview.resolve(1400000000L,x->phases.getOrDefault(x,0),false,0.025f);
  check(preview.liftEv()==0f,"bright scene resets to unity");
  preview.sample(grid(150),2000000000L);phases.put(2000000000L,1);
  preview.resolve(2000000000L,x->phases.getOrDefault(x,0),true,0.025f);
  preview.sample(grid(150),2100000000L);phases.put(2100000000L,1);
  preview.resolve(2100000000L,x->phases.getOrDefault(x,0),true,0.025f);
  preview.sample(grid(150),2200000000L);phases.put(2200000000L,2);
  preview.resolve(2200000000L,x->phases.getOrDefault(x,0),true,0.025f);
  check(preview.liftEv()==0f,"no visible luminance shift means no lift");
  preview.reset();check(preview.liftEv()==0f,"camera generation reset");
  System.out.println("PASS 26911 actual production Java shutter/ISO, deferred timestamp GL sampler, low-light scene and bright reset");
 }
}
