package com.particlesdevs.photoncamera.processing.experimentc;

import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.Consumer;

/** Independent C RAW owner. Unproven timestamps NEVER enter the burst spool.
 * Callers serialize all methods on the shutter owner. Preview/duplicate images
 * are closed, not counted. Bounded provisional leases leave HAL headroom. */
public final class Iris26976CRawTicketJoin<T> implements AutoCloseable {
    private final int target, pendingLimit;
    private final Consumer<T> release;
    private final TreeMap<Long,T> pending = new TreeMap<>();
    private final HashSet<Long> started = new HashSet<>(), delivered = new HashSet<>();
    private long lastStart;
    private boolean closed;
    public Iris26976CRawTicketJoin(int target, int pendingLimit, Consumer<T> release) {
        if (target < 2 || target > 30 || pendingLimit < 1 || release == null)
            throw new IllegalArgumentException("C RAW ticket bounds");
        this.target=target; this.pendingLimit=Math.min(target,pendingLimit); this.release=release;
    }
    /** Exact tagged start; returns only the matching staged lease, if present. */
    public T start(long timestamp) {
        if (closed || timestamp <= lastStart || started.size() >= target || !started.add(timestamp))
            throw new IllegalArgumentException("C RAW invalid start ticket");
        lastStart=timestamp;
        Iterator<Map.Entry<Long,T>> it=pending.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<Long,T> entry=it.next();
            if (entry.getKey()>=timestamp) break;
            T old=entry.getValue(); it.remove(); release.accept(old);
        }
        T match=pending.remove(timestamp);
        if (match!=null) delivered.add(timestamp);
        if (started.size()==target) clearPending();
        return match;
    }
    /** Either transfer one proved RAW to caller, stage provisionally, or close. */
    public T image(long timestamp, T image) {
        if (image==null) throw new IllegalArgumentException("C null RAW lease");
        if (!closed && started.contains(timestamp) && delivered.add(timestamp)) return image;
        if (closed || timestamp<=lastStart || timestamp<=0 || started.size()==target || pending.containsKey(timestamp)) {
            release.accept(image); return null;
        }
        pending.put(timestamp,image);
        // Keep the newest unknown leases: old unproved preview deliveries
        // cannot indefinitely occupy HAL slots. Never count them as RAW frames.
        while(pending.size()>pendingLimit) release.accept(pending.pollFirstEntry().getValue());
        return null;
    }
    private void clearPending() {
        while(!pending.isEmpty()) release.accept(pending.pollFirstEntry().getValue());
    }
    public int acceptedCount() { return delivered.size(); }
    public int pendingCount() { return pending.size(); }
    @Override public void close() { closed=true; clearPending(); }
}
