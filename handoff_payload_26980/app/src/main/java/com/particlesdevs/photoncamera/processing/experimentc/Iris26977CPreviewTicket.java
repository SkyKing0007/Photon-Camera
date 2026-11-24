package com.particlesdevs.photoncamera.processing.experimentc;

import android.graphics.Bitmap;
import android.os.SystemClock;
import android.view.PixelCopy;

/** One asynchronous ungraded C viewfinder reference; ownership transfers once to the RAW session. */
public final class Iris26977CPreviewTicket implements AutoCloseable {
    private Bitmap bitmap;
    private boolean completed, closed, transferred;
    private int result = Integer.MIN_VALUE;
    public synchronized void complete(int status, Bitmap value) {
        if (closed || completed || status != PixelCopy.SUCCESS || value == null) {
            if (value != null && value != bitmap && !value.isRecycled()) value.recycle();
        } else bitmap = value;
        if (!closed && !completed) { completed = true; result = status; notifyAll(); }
    }
    /** Copy only a completed, actually captured preview. Ownership stays with the epoch. */
    public synchronized Iris26977CPreviewTicket copyIfReady(java.util.function.Function<Bitmap,Bitmap> copier) {
        if(closed || !completed || bitmap==null || bitmap.isRecycled()) return null;
        Bitmap copy=copier.apply(bitmap);
        if(copy==null || copy==bitmap || copy.isRecycled()) return null;
        Iris26977CPreviewTicket ticket=new Iris26977CPreviewTicket();
        ticket.complete(PixelCopy.SUCCESS,copy);
        return ticket;
    }
    public synchronized boolean isReady() {
        return !closed && completed && bitmap!=null && !bitmap.isRecycled();
    }
    public synchronized void transfer() {
        if (closed || transferred) throw new IllegalStateException("C preview ownership unavailable");
        transferred = true;
    }
    public synchronized boolean isTransferred() { return transferred; }
    /** Worker only. A timeout or PixelCopy error is explicit, never a synthetic reference. */
    public synchronized Bitmap await(long timeoutMs) throws InterruptedException {
        long deadline = SystemClock.elapsedRealtime() + timeoutMs;
        while (!closed && !completed) {
            long remaining = deadline - SystemClock.elapsedRealtime();
            if (remaining <= 0) break;
            wait(remaining);
        }
        if (closed || !completed || bitmap == null || bitmap.isRecycled())
            throw new IllegalStateException("C shutter preview unavailable: PixelCopy result=" + result);
        return bitmap;
    }
    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
        bitmap = null; notifyAll();
    }
}
