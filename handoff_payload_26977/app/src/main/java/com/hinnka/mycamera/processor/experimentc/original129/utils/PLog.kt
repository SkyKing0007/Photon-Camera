package com.hinnka.mycamera.processor.experimentc.original129.utils

import com.particlesdevs.photoncamera.util.Log

/** C-private shell logging. This is not image-processing logic or an Iris A/B processor. */
internal object PLog {
    fun v(tag: String, message: String) { record("VERBOSE",tag,message); Log.v("Original129_$tag",message) }
    fun d(tag: String, message: String) { record("DEBUG",tag,message); Log.d("Original129_$tag",message) }
    fun i(tag: String, message: String) { record("INFO",tag,message); Log.i("Original129_$tag",message) }
    fun w(tag: String, message: String, throwable: Throwable? = null) {
        record("WARNING",tag,message); if (throwable == null) Log.w("Original129_$tag",message)
        else Log.w("Original129_$tag",message,throwable)
    }
    fun e(tag: String, message: String, throwable: Throwable? = null) {
        record("ERROR",tag,message); if (throwable == null) Log.e("Original129_$tag",message)
        else Log.e("Original129_$tag",message,throwable)
    }
    private fun record(level: String, tag: String, message: String) =
        DngCaptureDiagnostics.record(System.currentTimeMillis(),level,tag,message)
}
