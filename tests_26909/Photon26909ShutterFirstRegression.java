import com.particlesdevs.photoncamera.capture.Iris26909ShutterIsoMath;
public final class Photon26909ShutterFirstRegression {
  static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
  static Iris26909ShutterIsoMath.Plan sol(long t, int iso, int minIso, int maxIso, long maxNs, long maxFrameNs, long flicker) {
    return Iris26909ShutterIsoMath.solve(t,iso,minIso,maxIso,100_000L,maxNs,maxFrameNs,flicker);
  }
  public static void main(String[] ignored) {
    var tele=sol(8_333_000,6413,100,12800,1_000_000_000L,1_000_000_000L,0);
    check(tele!=null && tele.shutterFirstUseful,"user 26908 telephoto must activate");
    check(tele.shutterNs==100_000_000L,"1/10 sec maximum");
    check(tele.iso>=525&&tele.iso<=550,"telephoto should use ~ISO 534, was "+tele.iso);
    check(Math.abs(Math.log((tele.shutterNs*(double)tele.iso)/tele.targetEnergy))<0.02,"do not alter AE brightness/highlights");
    check(tele.frameDurationNs>=tele.shutterNs,"never request physically impossible >10fps");
    var rawr=sol(58_823_529L,382,100,12800,1_000_000_000L,1_000_000_000L,0);
    check(rawr!=null&&rawr.shutterNs==100_000_000L && rawr.iso>=220&&rawr.iso<=230,"RAWR-like 1/17 scenario");
    var mid=sol(20_000_000L,1600,100,12800,70_000_000L,70_000_000L,0);
    check(mid!=null&&mid.shutterNs<=70_000_000L&&mid.frameDurationNs<=70_000_000L,"sensor frameDuration caps override policy");
    var bright=sol(2_000_000L,100,100,12800,1_000_000_000L,1_000_000_000L,0);
    check(bright!=null && !bright.shutterFirstUseful,"bright scene remains HAL AE");
    check(sol(0,6413,100,12800,1_000_000_000L,1_000_000_000L,0)==null,"invalid shutter rejects");
    check(sol(8_333_000L,6413,100,200,8_333_000L,8_333_000L,0)==null,"sensor unable to satisfy fixed exposure rejects rather than darkens");
    var flicker=sol(8_333_000L,6413,100,12800,1_000_000_000L,1_000_000_000L,8_333_333L);
    check(flicker!=null&&flicker.shutterNs%8_333_333L==0,"60Hz snap without exceeding 1/10");
    var iso50=sol(8_333_000L,1000,50,12800,1_000_000_000L,1_000_000_000L,0);
    check(iso50!=null&&iso50.iso<100,"support lower sensor ISO on other phones");
    var max100=sol(300_000_000L,100,100,12800,1_000_000_000L,1_000_000_000L,0);
    check(max100!=null&&max100.shutterNs<=100_000_000L,"never request >1/10 sec even if HAL used longer");
    System.out.println("PASS 26909 real javac shutter/ISO: 26908 tele, RAWR 1/17, 1/10, energy, sensor limits, low ISO, no negative legacy motion cap");
  }
}
