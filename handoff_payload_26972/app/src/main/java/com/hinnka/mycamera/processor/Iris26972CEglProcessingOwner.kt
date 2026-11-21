package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLSurface
import android.opengl.GLES30

/** One isolated C capture EGL owner. Never borrow A/B's viewfinder or GL context. */
internal object Iris26972CEglProcessingOwner {
    private const val ES3_RENDERABLE_BIT = 0x40
    private const val COMPONENT = "26972 C real isolated GLES3 processing"

    internal fun <T> withNewContext(operation: () -> T): T {
        // The caller owns a NEW worker thread. Never terminate the process-wide
        // EGL_DEFAULT_DISPLAY: A/B may own other contexts on the same display.
        check(EGL14.eglGetCurrentContext() == EGL14.EGL_NO_CONTEXT) {
            "$COMPONENT worker must not steal an existing EGL context"
        }
        val display: EGLDisplay = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
        check(display != EGL14.EGL_NO_DISPLAY) { "$COMPONENT no EGL display" }
        var context: EGLContext = EGL14.EGL_NO_CONTEXT
        var surface: EGLSurface = EGL14.EGL_NO_SURFACE
        var current = false
        try {
            val version = IntArray(2)
            check(EGL14.eglInitialize(display, version, 0, version, 1)) {
                "$COMPONENT EGL initialization failed 0x${EGL14.eglGetError().toString(16)}"
            }
            val configAttrs = intArrayOf(
                EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT,
                EGL14.EGL_RENDERABLE_TYPE, ES3_RENDERABLE_BIT,
                EGL14.EGL_RED_SIZE, 8, EGL14.EGL_GREEN_SIZE, 8,
                EGL14.EGL_BLUE_SIZE, 8, EGL14.EGL_ALPHA_SIZE, 8,
                EGL14.EGL_NONE,
            )
            val configs = arrayOfNulls<EGLConfig>(1)
            val count = IntArray(1)
            check(EGL14.eglChooseConfig(display, configAttrs, 0, configs, 0, 1, count, 0) &&
                count[0] == 1 && configs[0] != null) { "$COMPONENT no GLES3 pbuffer config" }
            val config = checkNotNull(configs[0])
            context = EGL14.eglCreateContext(display, config, EGL14.EGL_NO_CONTEXT,
                intArrayOf(EGL14.EGL_CONTEXT_CLIENT_VERSION, 3, EGL14.EGL_NONE), 0)
            check(context != EGL14.EGL_NO_CONTEXT) { "$COMPONENT createContext failed" }
            surface = EGL14.eglCreatePbufferSurface(display, config,
                intArrayOf(EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE), 0)
            check(surface != EGL14.EGL_NO_SURFACE) { "$COMPONENT createPbuffer failed" }
            check(EGL14.eglMakeCurrent(display, surface, surface, context)) {
                "$COMPONENT makeCurrent failed 0x${EGL14.eglGetError().toString(16)}"
            }
            current = true
            val glVersion = GLES30.glGetString(GLES30.GL_VERSION) ?: ""
            require(glVersion.startsWith("OpenGL ES 3.")) {
                "$COMPONENT actual driver is not OpenGL ES3: $glVersion"
            }
            check(GLES30.glGetError() == GLES30.GL_NO_ERROR) {
                "$COMPONENT context GL error"
            }
            return operation()
        } finally {
            try {
                if (current) check(EGL14.eglMakeCurrent(display, EGL14.EGL_NO_SURFACE,
                    EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT)) {
                    "$COMPONENT failed to release current EGL owner"
                }
            } finally {
                try {
                    if (surface != EGL14.EGL_NO_SURFACE)
                        EGL14.eglDestroySurface(display, surface)
                } finally {
                    if (context != EGL14.EGL_NO_CONTEXT)
                        EGL14.eglDestroyContext(display, context)
                    EGL14.eglReleaseThread()
                }
            }
        }
    }
}
