import com.particlesdevs.photoncamera.capture.Iris26908ShutterFirst;
public final class Photon26908ShutterRegression {
  static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
  static long choose(long t,int iso,int minIso,int fps,long motion,long flicker){return Iris26908ShutterFirst.choose(t,iso,minIso,100000L,1_000_000_000L,fps,motion,flicker);}
  public static void main(String[] ignored){
    check(choose(8333333L,12000,100,10,100000000L,0)==100000000L,"auto maximum 1/10s");
    check(choose(8333333L,12000,100,30,100000000L,0)<=33333333L,"never exceed existing 30fps floor");
    check(choose(8333333L,12000,100,15,25000000L,0)<=25000000L,"gyro motion ceiling");
    check(choose(8333333L,12000,100,10,100000000L,10_000_000L)%10_000_000L==0L,"50 Hz flicker snap");
    check(choose(8333333L,12000,100,10,100000000L,8333333L)%8333333L==0L,"60 Hz flicker snap");
    check(choose(8333333L,400,100,10,100000000L,0)>8333333L,"shutter is first priority");
    check(choose(0L,400,100,15,100000000L,0)==0L,"bad metadata no-op");
    check(Iris26908ShutterFirst.AUTO_SLOWEST_NS==100000000L,"automatic hard cap");
    System.out.println("PASS Photon 26908 actual shutter math: cap, FPS, motion, flicker, invalid, shutter-first");
  }
}
