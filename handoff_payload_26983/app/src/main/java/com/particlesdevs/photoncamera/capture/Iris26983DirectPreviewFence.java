package com.particlesdevs.photoncamera.capture;

/**
 * Neutral handoff fence for a preconfigured Camera2 GL+direct session.
 * Camera handler owns the actual requests. A result is NOT display proof. The view owner
 * must acknowledge a NEW frame from this exact generation before GL is quiesced, and vice versa.
 * This pure state machine never creates/reconfigures a Camera2 session or changes capture targets.
 * Platform display/presentation callbacks are bound by CaptureController.
 */
public final class Iris26983DirectPreviewFence {
    public enum State { GL, WARM_DIRECT, DIRECT, WARM_GL }
    public enum Owner { B, C }
    public static final class Ticket {
        public final long generation, capture;
        public final Owner owner;
        private Ticket(long generation, long capture, Owner owner) {
            this.generation=generation; this.capture=capture; this.owner=owner;
        }
    }
    private long generation;
    private Object session;
    private boolean proven;
    private Ticket active;
    private State state=State.GL;
    private long lastCapture;
    public synchronized void bind(Object session, long generation, boolean configuredAndRawVerified) {
        if (session==null || generation<=this.generation) throw new IllegalArgumentException("stale preview generation");
        this.session=session; this.generation=generation; proven=configuredAndRawVerified;
        active=null; state=State.GL; lastCapture=0;
    }
    public synchronized Ticket begin(Object session, long generation, long capture, Owner owner,
                                     boolean superRes, boolean geometryVerified, boolean snapshotFrozen) {
        if (!matches(session,generation) || !proven || owner==null || !superRes || !geometryVerified ||
                !snapshotFrozen || state!=State.GL || active!=null || capture<=lastCapture) return null;
        lastCapture=capture; active=new Ticket(generation,capture,owner); state=State.WARM_DIRECT;
        return active;
    }
    /** Called only after direct producer presentation is proven AND the GL-target removal was accepted. */
    public synchronized boolean directPresented(Object session, Ticket ticket, boolean newDirectFrame,
                                                boolean glTargetRemovalAccepted) {
        if (!valid(session,ticket) || state!=State.WARM_DIRECT || !newDirectFrame || !glTargetRemovalAccepted)
            return false;
        state=State.DIRECT; return true;
    }
    /** The caller first restores GL to repeating targets; keep direct visible until NEW GL frame. */
    public synchronized boolean beginRestore(Object session, Ticket ticket, boolean glTargetRestored) {
        if (!valid(session,ticket) || !glTargetRestored || state==State.GL || state==State.WARM_GL) return false;
        state=State.WARM_GL; return true;
    }
    public synchronized boolean glPresented(Object session, Ticket ticket, boolean newGlFrame,
                                            boolean directTargetRemovalAccepted) {
        if (!valid(session,ticket) || state!=State.WARM_GL || !newGlFrame || !directTargetRemovalAccepted)
            return false;
        state=State.GL; active=null; return true;
    }
    /** Cancel a failed warmup/restore only after the original request is accepted. No fresh-frame claim. */
    public synchronized boolean abortToGl(Object session,Ticket ticket,boolean originalTargetAccepted){
        if(!valid(session,ticket)||!originalTargetAccepted)return false;state=State.GL;active=null;return true;
    }
    /** On session loss, surface destruction or generation invalidation: the old ticket is retired. */
    public synchronized boolean invalidate(Object session,long generation) {
        if (!matches(session,generation)) return false;
        this.session=null; proven=false; active=null; state=State.GL; return true;
    }
    private boolean matches(Object session,long generation) {
        return session!=null && this.session==session && this.generation==generation;
    }
    private boolean valid(Object session,Ticket ticket) {
        return ticket!=null && ticket==active && matches(session,ticket.generation);
    }
    public synchronized State state() { return state; }
    public synchronized boolean mayQuiesceGl() { return state==State.DIRECT; }
}
