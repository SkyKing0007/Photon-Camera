package com.particlesdevs.photoncamera.capture;

import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.params.OutputConfiguration;
import android.hardware.camera2.params.SessionConfiguration;
import android.os.Build;
import android.view.Surface;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Executor;

/**
 * Neutral Camera2 preflight for B/SR ON and C/SR ON, never a processing owner.
 * No existing OutputConfiguration or live session is mutated by a query.
 * A positive HAL query is only permission to try the exact plan on normal session creation,
 * not proof of a configured stream, live frame, matched RAW, or correct display geometry.
 * CaptureController binds the configured session to the presentation fence.
 */
public final class Iris26983DirectPreviewPlan {
    public enum Topology { SHARED_PRIVATE, SEPARATE_PRIVATE }
    public final Topology topology;
    public final Surface gl, direct, raw;
    public final String physicalOutputId;
    public final SessionConfiguration configuration;
    private Iris26983DirectPreviewPlan(Topology topology, Surface gl, Surface direct, Surface raw,
                                      String physicalOutputId, SessionConfiguration config) {
        this.topology=topology; this.gl=gl; this.direct=direct; this.raw=raw;
        this.physicalOutputId=physicalOutputId; this.configuration=config;
    }
    public static boolean eligible(String experiment, boolean superRes, boolean jpegOrHeic) {
        return superRes && jpegOrHeic && ("B".equals(experiment) || "C".equals(experiment));
    }
    /** Exact original session outputs, including RAW and optional YUV, are preserved.
     * A caller must use a configured direct TextureView surface whose configured size is the same as
     * the GL camera input size and whose transform has been validated on this route.
     */
    public static Iris26983DirectPreviewPlan query(CameraDevice device,
            List<OutputConfiguration> original, Surface gl, Surface direct, Surface raw,
            String physicalOutputId, int glWidth, int glHeight, int directWidth, int directHeight,
            boolean allowExtraPrivateStream, Executor executor,
            CameraCaptureSession.StateCallback callback) {
        if (Build.VERSION.SDK_INT < 29 || device==null || original==null || executor==null || callback==null ||
                gl==null || direct==null || raw==null || gl==direct || direct==raw || gl==raw ||
                !gl.isValid() || !direct.isValid() || !raw.isValid() || glWidth<=0 || glHeight<=0 ||
                glWidth!=directWidth || glHeight!=directHeight) return null;
        int previewIndex=-1, rawCount=0;
        for (int i=0; i<original.size(); i++) {
            OutputConfiguration out=original.get(i);
            if (out==null || out.getSurfaces().contains(direct)) return null;
            if (out.getSurfaces().contains(raw)) rawCount++;
            if (out.getSurfaces().contains(gl)) {
                if (previewIndex!=-1 || out.getSurfaces().size()!=1) return null;
                previewIndex=i;
            }
        }
        if (previewIndex<0 || rawCount!=1) return null;
        for (Topology kind : Topology.values()) {
            if (kind==Topology.SEPARATE_PRIVATE && !allowExtraPrivateStream) continue;
            try {
                List<OutputConfiguration> outputs=new ArrayList<>(original);
                if (kind==Topology.SHARED_PRIVATE) {
                    // The predecessor preview configuration is a simple Surface with physical ID.
                    // Construct a new group, never call enableSurfaceSharing on the live group.
                    OutputConfiguration preview=new OutputConfiguration(gl);
                    if (physicalOutputId!=null) preview.setPhysicalCameraId(physicalOutputId);
                    preview.enableSurfaceSharing();
                    preview.addSurface(direct);
                    outputs.set(previewIndex,preview);
                } else {
                    OutputConfiguration extra=new OutputConfiguration(direct);
                    if (physicalOutputId!=null) extra.setPhysicalCameraId(physicalOutputId);
                    outputs.add(extra);
                }
                SessionConfiguration prospective=new SessionConfiguration(
                        SessionConfiguration.SESSION_REGULAR,Collections.unmodifiableList(outputs),executor,callback);
                if (device.isSessionConfigurationSupported(prospective)) {
                    return new Iris26983DirectPreviewPlan(kind,gl,direct,raw,physicalOutputId,prospective);
                }
            } catch (CameraAccessException | RuntimeException unsupported) {
                // HAL query unsupported, wrong format/size/usage, closed device, etc.
                // Do not mutate or rebuild the existing session here.
            }
        }
        return null;
    }
}
