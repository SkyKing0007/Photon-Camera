import com.particlesdevs.photoncamera.capture.Iris26909ShutterIsoMath;
public final class Photon26913BrightnessRegression {
    private static final long MS = 1_000_000L;
    static void check(boolean yes, String why) {
        if (!yes) throw new AssertionError(why);
    }
    static Iris26909ShutterIsoMath.Plan choose(long ns, int iso, int min, int max,
                                               long shutterMax, long flicker) {
        return Iris26909ShutterIsoMath.solveBrightnessAware(ns,iso,min,max,100_000L,
                shutterMax,1_000_000_000L,flicker);
    }
    static void energy(Iris26909ShutterIsoMath.Plan p,long ns,int iso) {
        check(p!=null,"missing plan");
        check(Math.abs((double)p.shutterNs*p.iso/(ns*(double)iso)-1.0)<0.04,"energy mismatch");
        check(p.shutterNs<=100*MS,"over 1/10s max");
        check(p.iso>=50 && p.iso<2000,"ISO not bounded");
        check(p.frameDurationNs>=p.shutterNs,"frame duration shorter than shutter");
    }
    public static void main(String[] args) {
        // Recovered actual successful 26912 18:40 indoor measurement.
        long room = 8_333_000L; int halIso = 1114;
        var p=choose(room,halIso,50,6400,1_000_000_000L,0);
        energy(p,room,halIso);
        check(p.shutterNs>=35*MS && p.shutterNs<=45*MS,"indoor should be ~1/24s");
        check(p.iso>=205 && p.iso<=250,"indoor should not crank ISO");
        check(p.shutterFirstUseful,"indoor physical pair must engage");
        // HAL itself cannot dictate faster 1/120 s or 1/10 s with same energy.
        var halSlow=choose(100*MS,93,50,6400,1_000_000_000L,0);
        check(halSlow!=null && halSlow.shutterFirstUseful && halSlow.shutterNs<50*MS,
                "Iris must own both slower and faster than HAL shutter allocations");
        // Actual darker 26912 18:23 scene: remain at 1/10s, prioritize gain.
        var dark=choose(13_356_031L,3097,50,6400,1_000_000_000L,0);
        energy(dark,13_356_031L,3097);
        check(dark.shutterNs==100*MS && dark.iso>=400 && dark.iso<=430,
                "dark must retain full shutter/low gain priority");
        // Brighter room: 1/60-like shutter, without large gain increase.
        var brighter=choose(8_000_000L,500,50,6400,1_000_000_000L,0);
        energy(brighter,8_000_000L,500);
        check(brighter.shutterNs>=14*MS && brighter.shutterNs<=20*MS,
                "bright interior should use ~1/60s");
        check(brighter.iso<=250,"bright interior excessive gain");
        // Bright daylight: sensor ISO minimum, no mandatory high-ISO target.
        var daylight=choose(4*MS,80,50,6400,1_000_000_000L,0);
        energy(daylight,4*MS,80);
        check(daylight.shutterNs<10*MS && daylight.iso<=110,
                "daylight should keep ISO low and shorten shutter");
        check(p.shutterNs>brighter.shutterNs && brighter.shutterNs>daylight.shutterNs,
                "nonmonotonic exposure selection");
        // Huge low-light energy beyond 1/10s x sensor ISO must fail closed.
        check(choose(200*MS,8000,50,6400,1_000_000_000L,0)==null,
                "invalid dark scene should fail closed");
        // Sensor cannot supply exposure at requested short cap without ISO spike.
        check(choose(room,halIso,50,100,20*MS,0)==null,
                "ISO budget must reject infeasible sensor");
        // Respect hardware min/max, explicit 10ms proven flicker period.
        var flicker=choose(room,halIso,50,6400,1_000_000_000L,10*MS);
        energy(flicker,room,halIso);
        check(flicker.shutterNs % (10*MS)==0,"explicit flicker-period snapping failed");
        check(choose(0,100,50,6400,1_000_000_000L,0)==null,"invalid exposure accepted");
        check(choose(room,halIso,0,6400,1_000_000_000L,0)==null,"invalid ISO min accepted");
        // The historical 26909 allocation still exists unchanged.
        var old=Iris26909ShutterIsoMath.solve(room,halIso,50,6400,
                100_000L,1_000_000_000L,1_000_000_000L,0L);
        check(old!=null && old.shutterNs==100*MS,"historical 26909 semantics changed");
        System.out.println("PASS 26913 actual room, darker, brighter, daylight, hard caps, "
                + "energy fidelity, 1/10s dark, ISO bound, flicker, historic math");
    }
}
