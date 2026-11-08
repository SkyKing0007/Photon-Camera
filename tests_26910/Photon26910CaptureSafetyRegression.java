import com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety;

public final class Photon26910CaptureSafetyRegression {
    private static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError("26910: " + what);
    }
    public static void main(String[] args) {
        double physical = 100_000_000d * 645d;
        check(Iris26910CaptureSafety.targetEnergy(physical, 0f) == physical,
                "zero-protection manual should never rebase to stale HAL recipe");
        check(Math.abs(Iris26910CaptureSafety.targetEnergy(physical, -.5f) /
                physical - Math.pow(2, -.5)) < 1e-8,
                "a real negative highlight recipe must remain protective");
        check(Iris26910CaptureSafety.targetEnergy(physical, .75f) == physical,
                "positive recipe cannot raise physical NORMAL exposure");
        check(Double.isNaN(Iris26910CaptureSafety.targetEnergy(-1, 0)),
                "invalid physical energy rejected");
        check(Iris26910CaptureSafety.completionTimeoutMs(0,100_000_000L,false) == 1400,
                "complete ZSL burst retains fast success path");
        check(Iris26910CaptureSafety.completionTimeoutMs(8,100_000_000L,false) == 3500,
                "eight-frame short burst retains prior terminal budget");
        check(Iris26910CaptureSafety.completionTimeoutMs(30,100_000_000L,false) > 3500,
                "30-frame slow sensor burst receives real cadence time");
        check(Iris26910CaptureSafety.completionTimeoutMs(30,100_000_000L,false) <= 12000,
                "capture timeout bounded");
        check(!Iris26910CaptureSafety.attemptStalled(false,false,false,8000),
                "queued sensor request must never be retired before start");
        check(!Iris26910CaptureSafety.attemptStalled(true,false,false,1599),
                "started request deserves sensor+RAW result grace");
        check(Iris26910CaptureSafety.attemptStalled(true,false,false,1600),
                "genuine stuck started request is retryable");
        check(!Iris26910CaptureSafety.attemptStalled(true,true,false,1499),
                "completed result can await exact RAW delivery");
        check(Iris26910CaptureSafety.attemptStalled(true,true,false,1500),
                "RAW result missing beyond deadline is retryable");
        check(!Iris26910CaptureSafety.attemptStalled(true,true,true,10000),
                "completed exact slot cannot be retried");
        check(Iris26910CaptureSafety.lowLightPreviewLiftEv(100_000_000L,2560,.05f,0) > .65f,
                "verified dark telephoto should get display-only lift");
        check(Iris26910CaptureSafety.lowLightPreviewLiftEv(100_000_000L,2244,.02f,0) > .65f,
                "verified dark main should get display-only lift");
        check(Iris26910CaptureSafety.lowLightPreviewLiftEv(100_000_000L,300,.02f,0) == 0,
                "indoor low-ISO exposure should be unchanged");
        check(Iris26910CaptureSafety.lowLightPreviewLiftEv(100_000_000L,2560,.9f,0) == 0,
                "bright scene should be unchanged");
        check(Iris26910CaptureSafety.lowLightPreviewLiftEv(100_000_000L,2560,.02f,.01f) == 0,
                "clipped highlights must suppress extra presentation gain");
        check(Iris26910CaptureSafety.lowLightPreviewLiftEv(20_000_000L,6000,.02f,0) == 0,
                "fast shutter should be unchanged");
        System.out.println("PASS 26910 actual Java capture exact-energy, queued timing, dark/bright preview regressions");
    }
}
