package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

/**
 * Experiment C ABI bridge for the original DngSdkColorSpec's DNG metadata overloads.
 * This is NOT the donor's full RawMetadata implementation. The active Camera2 path
 * invokes only the original array-based color calculations; no DNG parser or
 * missing donor metadata value is fabricated. Replace this bridge with the exact
 * donor RawMetadata once its complete engine dependency closure is integrated.
 */
internal data class RawMetadata(
    val whiteBalanceGains: FloatArray,
    val colorCorrectionMatrix: FloatArray = FloatArray(9),
    val cameraWhite: FloatArray = floatArrayOf(1f,1f,1f),
    val whitePointXy: FloatArray? = null,
    val colorTemperature: Float? = null,
    val cameraCalibration: RawCameraCalibration? = null,
)
