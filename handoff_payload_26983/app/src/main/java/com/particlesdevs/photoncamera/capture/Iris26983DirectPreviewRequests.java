package com.particlesdevs.photoncamera.capture;

import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CaptureRequest;
import android.os.Handler;
import android.os.Looper;
import android.view.Surface;
import java.util.HashSet;
import java.util.Set;

/**
 * Camera-handler-only target swap. Leaves the original RAW/YUV and all builder keys untouched.
 * Caller must hold the existing session/route generation and verify the plan was really configured.
 * Never builds a new camera session, never mutates still/burst requests. This is an integration
 * primitive, not evidence that the SurfaceView path is already wired or compatible on device.
 */
public final class Iris26983DirectPreviewRequests {
    public enum Targets { GL, BOTH, DIRECT }
    private Iris26983DirectPreviewRequests() {}
    public static CaptureRequest submit(CameraCaptureSession session,
            CaptureRequest.Builder builder, Iris26983DirectPreviewPlan plan,
            Targets targets, Set<Surface> ownedTargets, CameraCaptureSession.CaptureCallback callback,
            Handler handler) throws CameraAccessException {
        if (session==null || builder==null || plan==null || targets==null || ownedTargets==null || handler==null ||
                Looper.myLooper()!=handler.getLooper() || !plan.gl.isValid() || !plan.direct.isValid() ||
                !plan.raw.isValid()) throw new IllegalArgumentException("26983 invalid preview request owner");
        final CaptureRequest before=builder.build();
        // Camera2 does not expose CaptureRequest.getTargets() in the public SDK.
        // The caller must supply its complete handler-confined target inventory.
        Set<Surface> original=new HashSet<>(ownedTargets);
        if (!original.contains(plan.raw) || (!original.contains(plan.gl) && !original.contains(plan.direct)))
            throw new IllegalStateException("26983 missing original RAW or preview target");
        Set<Surface> wanted=new HashSet<>(original);
        wanted.remove(plan.gl); wanted.remove(plan.direct);
        if (targets!=Targets.DIRECT) wanted.add(plan.gl);
        if (targets!=Targets.GL) wanted.add(plan.direct);
        if (wanted.equals(original)) return before;
        try {
            change(builder,original,wanted);
            CaptureRequest next=builder.build();
            session.setRepeatingRequest(next,callback,handler);
            ownedTargets.clear(); ownedTargets.addAll(wanted);
            return next;
        } catch (CameraAccessException | RuntimeException failed) {
            // Keep the old live request and the builder in agreement; recovery is mandatory if
            // the device rejects the restore. Never report direct preview active after failure.
            try {
                // Both preview targets are under our sole ownership; never touch RAW/YUV.
                if(original.contains(plan.gl)) builder.addTarget(plan.gl); else builder.removeTarget(plan.gl);
                if(original.contains(plan.direct)) builder.addTarget(plan.direct); else builder.removeTarget(plan.direct);
                ownedTargets.clear(); ownedTargets.addAll(original);
                session.setRepeatingRequest(before,callback,handler);
            } catch (CameraAccessException | RuntimeException restoreFailed) {
                failed.addSuppressed(restoreFailed);
                throw new IllegalStateException("26983 preview rollback failed; camera recovery required",failed);
            }
            throw failed;
        }
    }
    private static void change(CaptureRequest.Builder builder,Set<Surface> current,Set<Surface> wanted) {
        // Add first so a builder cannot momentarily lose its last preview target.
        for(Surface target:wanted) if(!current.contains(target)) builder.addTarget(target);
        for(Surface target:current) if(!wanted.contains(target)) builder.removeTarget(target);
    }
}
