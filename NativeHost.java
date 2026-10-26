package com.unspektrawesome;

import android.app.Application;
import android.content.Context;
import com.particlesdevs.photoncamera.app.PhotonCamera;

/**
 * Application-context bridge needed by the actual 1.2.5 Vulkan JNI.
 *
 * Original DEX exports precisely a public static
 * NativeHost.application(): android.app.Application.  In Iris the shell's
 * existing Application owns the context; never instantiate the standalone
 * UnspektrAwesome application or a second Camera2/capture lifecycle.
 */
public final class NativeHost {
    private NativeHost() {}

    public static Application application() {
        Context context = PhotonCamera.getApplicationContextStatic();
        if (!(context instanceof Application)) {
            throw new IllegalStateException("Spektra native host requested before Iris application initialization");
        }
        return (Application) context;
    }
}
