package com.particlesdevs.photoncamera.capture;

import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Iterator;

/**
 * IRIS_26935_B_ON_JPEG_PUBLICATION_GUARD.
 * One immutable owner token per B/SR-ON LKR batch. This model has no Android or
 * view references and survives CameraFragment recreation within the app process.
 * Never infer success from onProcessingFinished: only the verified JPG write can
 * publish success. Failure releases only when the processor is terminal.
 */
public final class Iris26935BOnSession {
    public interface Listener { void onBOnSession(long token, boolean busy, String event); }
    private static final Object LOCK = new Object();
    private static final ArrayList<WeakReference<Listener>> listeners = new ArrayList<>();
    private static long nextToken = 1L;
    private static long activeToken;
    private static boolean active;
    private static String activeOwner;
    private Iris26935BOnSession() { }

    public static boolean isActive() {
        synchronized (LOCK) { return active; }
    }
    public static long currentToken() {
        synchronized (LOCK) { return active ? activeToken : 0L; }
    }
    public static long arm() { return arm("B"); }
    public static String currentOwner() { synchronized(LOCK){return active?activeOwner:null;} }
    public static long arm(String owner) {
        if(!"B".equals(owner)&&!"C".equals(owner)) throw new IllegalArgumentException("SR owner");
        final long token;
        synchronized (LOCK) {
            if (active) throw new IllegalStateException("26935 overlapping B ON JPEG guard");
            token = nextToken++;
            activeToken = token;
            active = true;
            activeOwner = owner;
        }
        notifyListeners(token, true, "ARM");
        return token;
    }
    public static boolean complete(long token, boolean success, String event) {
        synchronized (LOCK) {
            if (!active || token != activeToken) return false;
            active = false;
            activeOwner = null;
        }
        notifyListeners(token, false, (success ? "SAVED:" : "FAILED:") + event);
        return true;
    }
    public static void subscribe(Listener listener) {
        if (listener == null) return;
        final long token;
        final boolean busy;
        synchronized (LOCK) {
            for (Iterator<WeakReference<Listener>> it = listeners.iterator(); it.hasNext();) {
                Listener existing = it.next().get();
                if (existing == null || existing == listener) it.remove();
            }
            listeners.add(new WeakReference<>(listener));
            token = activeToken;
            busy = active;
        }
        listener.onBOnSession(token, busy, "SUBSCRIBE");
    }
    public static void unsubscribe(Listener listener) {
        synchronized (LOCK) {
            for (Iterator<WeakReference<Listener>> it = listeners.iterator(); it.hasNext();) {
                Listener existing = it.next().get();
                if (existing == null || existing == listener) it.remove();
            }
        }
    }
    private static void notifyListeners(long token, boolean busy, String event) {
        ArrayList<Listener> snapshot = new ArrayList<>();
        synchronized (LOCK) {
            for (Iterator<WeakReference<Listener>> it = listeners.iterator(); it.hasNext();) {
                Listener listener = it.next().get();
                if (listener == null) it.remove(); else snapshot.add(listener);
            }
        }
        for (Listener listener : snapshot) {
            try { listener.onBOnSession(token, busy, event); }
            catch (RuntimeException ignored) {
                // A detached Activity must never stop the native JPEG owner.
            }
        }
    }
}
