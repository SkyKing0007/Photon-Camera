package com.hinnka.mycamera.processor.experimentc.original129.camera

/** C-owned donor RAW-frame gyro metadata; Iris still owns capture and gyro sampling. */
data class GyroExposureWindow(
    val startTimestampNs: Long,
    val endTimestampNs: Long,
    val sampleCount: Int,
    val integratedRotationRad: FloatArray,
    val angularEnergy: Float,
    val peakAngularVelocity: Float,
    val jerkEnergy: Float,
    val coverageRatio: Float,
)
