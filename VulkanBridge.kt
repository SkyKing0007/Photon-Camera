package com.unspektrawesome.vulkan

import android.hardware.HardwareBuffer

/** Vulkan availability/diagnostic probes declared by the original 1.2.5 APK. */
object VulkanBridge {
    // Original 1.2.5 DEX <clinit> loads this exact native library before probes.
    init { System.loadLibrary("unspektrawesome_vulkan") }

    external fun nativeProbeVulkan(buffer: HardwareBuffer?): String

    external fun nativeGetDiagnosticString(): String
}
