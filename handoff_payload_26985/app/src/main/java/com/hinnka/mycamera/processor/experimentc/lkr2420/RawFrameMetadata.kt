// SPDX-FileCopyrightText: 2026 RawLens contributors
// SPDX-License-Identifier: GPL-3.0-or-later

package com.hinnka.mycamera.processor.experimentc.lkr2420

/** A defensive immutable wrapper for metadata arrays supplied by the camera HAL. */
class ImmutableFloatValues(values: FloatArray) {
    private val data = values.copyOf()
    val size: Int get() = data.size
    operator fun get(index: Int): Float = data[index]
    fun toFloatArray(): FloatArray = data.copyOf()
    fun toList(): List<Float> = data.toList()
}

class ImmutableDoubleValues(values: DoubleArray) {
    private val data = values.copyOf()
    val size: Int get() = data.size
    operator fun get(index: Int): Double = data[index]
    fun toDoubleArray(): DoubleArray = data.copyOf()
}

/** C-only immutable projection of exact physical RAW capture metadata. */
data class RawFrameMetadata(
    val cameraId: String,
    val exifOrientation: Int,
    val sensitivityIso: Int? = null,
    val exposureTimeNanos: Long? = null,
    val cfaPattern: BayerPattern? = null,
    val blackLevels: ImmutableFloatValues? = null,
    val whiteLevel: Float? = null,
    val neutralColorPoint: ImmutableDoubleValues? = null,
    val colorMatrix1: ImmutableDoubleValues? = null,
    val colorMatrix2: ImmutableDoubleValues? = null,
    val cameraCalibration1: ImmutableDoubleValues? = null,
    val cameraCalibration2: ImmutableDoubleValues? = null,
    val forwardMatrix1: ImmutableDoubleValues? = null,
    val forwardMatrix2: ImmutableDoubleValues? = null,
    val referenceIlluminant1: Int? = null,
    val referenceIlluminant2: Int? = null,
    val noiseProfile: ImmutableDoubleValues? = null,
    val aperture: Float? = null,
    val focalLengthMm: Float? = null,
    val focusDistanceM: Float? = null,
    val flashFired: Boolean? = null,
    val aeMode: Int? = null,
    val awbMode: Int? = null,
    val exposureCompensationEv: Double? = null,
    val digitalZoomRatio: Float? = null,
    val lensModel: String? = null,
    val lensMake: String? = null,
    val lensSpecification: ImmutableDoubleValues? = null,
    val compositeSourceCount: Int? = null,
    val compositeUsedCount: Int? = null
)
