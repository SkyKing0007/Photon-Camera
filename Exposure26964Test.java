import com.particlesdevs.photoncamera.capture.Iris26909ShutterIsoMath;
import java.util.Random;
public final class Exposure26964Test {
  static int tests=0;
  static void check(boolean b, String why) { tests++; if (!b) throw new AssertionError(why); }
  static Iris26909ShutterIsoMath.Plan solve(long shutter, int iso, int min, int max, double focal, int analog, boolean ois, boolean moving) {
    return Iris26909ShutterIsoMath.solveSceneLensAware(shutter,iso,min,max,100000L,1000000000L,1000000000L,focal,analog,ois,moving);
  }
  static void energy(Iris26909ShutterIsoMath.Plan p, long sourceShutter, int sourceIso) {
    check(p!=null,"valid physical plan");
    check(p.shutterNs>=100000 && p.shutterNs<=100000000,"cap");
    check(p.iso>=50 && p.iso<=12800,"iso");
    double v=(double)p.shutterNs*p.iso/((double)sourceShutter*sourceIso);
    check(Math.abs(Math.log(v))<.045,"physical brightness match "+v);
    check(p.frameDurationNs>=p.shutterNs,"physical fps");
  }
  public static void main(String[] args) {
    final long ss=8333333L;
    Iris26909ShutterIsoMath.Plan tele=solve(ss,4331,50,12800,100,3200,true,false);
    energy(tele,ss,4331);
    check(tele.shutterNs<65000000L,"tele quicker than 1/15: "+tele.shutterNs);
    check(tele.shutterNs>=16000000L,"tele respects noise");
    Iris26909ShutterIsoMath.Plan main=solve(ss,4331,50,12800,24,3200,true,false);
    energy(main,ss,4331);
    check(main.shutterNs>tele.shutterNs,"tele prefers shorter shutter at same light");
    Iris26909ShutterIsoMath.Plan ultra=solve(ss,4331,50,12800,14,3200,true,false);
    energy(ultra,ss,4331);
    check(ultra.shutterNs>=main.shutterNs,"ultrawide can trade shutter for ISO");
    Iris26909ShutterIsoMath.Plan daylight=solve(1000000,100,100,12800,24,3200,false,false);
    check(daylight!=null && !daylight.shutterFirstUseful, "daylight remains AE");
    Iris26909ShutterIsoMath.Plan lowAnalog=solve(ss,4331,50,12800,100,400,true,false);
    energy(lowAnalog,ss,4331);
    check(lowAnalog.shutterNs>tele.shutterNs,"low analog capability chooses slower SS");
    Iris26909ShutterIsoMath.Plan dark=solve(ss,24000,50,12800,100,3200,true,false);
    energy(dark,ss,24000);
    check(dark.shutterNs>=90000000L,"very dark can reach 1/10");
    Iris26909ShutterIsoMath.Plan moving=solve(ss,4331,50,12800,100,3200,true,true);
    energy(moving,ss,4331);
    check(moving.shutterNs<=tele.shutterNs,"camera motion hint should not slow shutter");
    Iris26909ShutterIsoMath.Plan missing=solve(ss,4331,50,12800,Double.NaN,0,false,false);
    energy(missing,ss,4331);
    check(Iris26909ShutterIsoMath.solveSceneLensAware(0,100,50,12800,100000,1000000000L,1000000000L,100,3200,false,false)==null,"invalid AE blocked");
    Random r=new Random(26964);
    for (int k=0;k<10000;k++) {
      int min=50+r.nextInt(200),max=Math.max(4000,min*16);
      long halS=100000L+r.nextInt(99000000), halIso=50+r.nextInt(2000);
      double en=(double)halS*halIso;
      if (en>100000000.0*max || en<100000.0*min) continue;
      Iris26909ShutterIsoMath.Plan p=solve(halS,(int)halIso,min,max,8+r.nextDouble()*230,min*(2+r.nextInt(60)),r.nextBoolean(),r.nextBoolean());
      if (p!=null) {
        check(p.shutterNs>=100000L && p.shutterNs<=100000000L,"random shutter");
        check(p.iso>=min && p.iso<=max,"random iso");
        double err=Math.abs(Math.log((double)p.shutterNs*p.iso/en));
        check(err<0.045,"random energy "+err);
      }
    }
    System.out.printf("PASS %d real Java source checks; tele=%dns ISO=%d; main=%dns ISO=%d; ultra=%dns ISO=%d; dark=%dns ISO=%d%n",tests,tele.shutterNs,tele.iso,main.shutterNs,main.iso,ultra.shutterNs,ultra.iso,dark.shutterNs,dark.iso);
  }
}
