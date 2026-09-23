package com.unspektrawesome.diagnostics;

import android.util.Log;

import androidx.annotation.Keep;

/**
 * JNI load-time contract required by the exact Unspektrawesome 1.1.2 native library.
 *
 * The native JNI_OnLoad resolves this exact class name and the exact static method descriptor
 * recordNative(int, String, String): void before VulkanRenderer can be used. Keep both names
 * stable and never allow a native diagnostic callback to throw back across JNI.
 */
@Keep
public final class InternalLogRecorder {
    private static final String FALLBACK_TAG = "UnspektrawesomeNative";

    private InternalLogRecorder() {}

    @Keep
    public static void recordNative(int priority, String tag, String message) {
        try {
            Log.println(priority,
                    tag == null || tag.isEmpty() ? FALLBACK_TAG : tag,
                    message == null ? "" : message);
        } catch (Throwable ignored) {
            // Diagnostics must never destabilize JNI/native rendering.
        }
    }
}
