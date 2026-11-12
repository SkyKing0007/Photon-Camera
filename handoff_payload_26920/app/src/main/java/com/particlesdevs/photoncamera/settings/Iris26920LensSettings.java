package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.concurrent.ConcurrentHashMap;

/** Physical-lens Experiment B SR selection, snapshotted with each admitted RAW timestamp. */
public final class Iris26920LensSettings {
    private static final String FILE = "iris26920_lucas_kanade_physical";
    private static final ConcurrentHashMap<Long, Snapshot> BY_TIMESTAMP = new ConcurrentHashMap<>();
    private static final int MAX_PENDING = 4096;
    private static final class Snapshot {
        final long lens;
        final boolean enabled;
        Snapshot(long lens, boolean enabled) { this.lens = lens; this.enabled = enabled; }
    }
    private Iris26920LensSettings() { }
    public static long hash(String physical) {
        if (physical == null || physical.trim().isEmpty())
            throw new IllegalArgumentException("26920 missing physical camera ID");
        long result = 1469598103934665603L;
        for (int i=0;i<physical.length();++i) {
            result = (result ^ physical.charAt(i)) * 1099511628211L;
        }
        return result == 0L ? 1L : result;
    }
    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    private static String key(String physical) {
        return "physical_" + Iris26856ABSettings.identity(physical, null);
    }
    public static boolean get(Context context, String physical) {
        return prefs(context).getBoolean(key(physical), false);
    }
    public static void set(Context context, String physical, boolean on) {
        prefs(context).edit().putBoolean(key(physical), on).apply();
    }
    /** Called on actual admitted NORMAL RAW, never on intermediate preview frames. */
    public static void freezeNormal(Context context, String physical, long timestamp,
                                    boolean experimentB, boolean superResAtShutter) {
        if (timestamp <= 0L || physical == null || physical.isEmpty())
            throw new IllegalArgumentException("26920 missing timestamp or physical-lens provenance");
        boolean on = experimentB && superResAtShutter && get(context, physical);
        Snapshot old = BY_TIMESTAMP.putIfAbsent(timestamp, new Snapshot(hash(physical), on));
        if (old != null && (old.lens != hash(physical) || old.enabled != on))
            throw new IllegalStateException("26920 inconsistent RAW timestamp settings");
        if (BY_TIMESTAMP.size() > MAX_PENDING) {
            // Only raw timestamps older than the current capture can be retired;
            // do not silently evict the just frozen frame.
            for (Long t : BY_TIMESTAMP.keySet()) if (t < timestamp - 12_000_000_000L)
                BY_TIMESTAMP.remove(t);
            if (BY_TIMESTAMP.size() > MAX_PENDING)
                throw new IllegalStateException("26920 pending per-frame snapshot overflow");
        }
    }
    /** Synchronous read of shutter-frozen intent, NOT a mutable preference read. */
    public static boolean frozenForReference(long timestamp, String physical) {
        Snapshot entry = BY_TIMESTAMP.get(timestamp);
        if (entry == null || entry.lens != hash(physical))
            throw new IllegalStateException("26920 missing physical-lens shutter snapshot for RAW reference " + timestamp);
        return entry.enabled;
    }
}
