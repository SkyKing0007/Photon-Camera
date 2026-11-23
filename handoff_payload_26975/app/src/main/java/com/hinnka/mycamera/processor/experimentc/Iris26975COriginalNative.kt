package com.hinnka.mycamera.processor.experimentc

/** Only source of native-library ownership for the pinned original 1.29.0 classes. */
internal object Iris26975COriginalNative {
    init {
        // Original JNI_OnLoad must execute before the C-private JNI tail-call shim.
        System.loadLibrary("iris26972c129")
        System.loadLibrary("iris26975c_original129_jni")
    }
    fun ensureLoaded() = Unit
}
