// SPDX-FileCopyrightText: 2026 RawLens contributors
// SPDX-License-Identifier: GPL-3.0-or-later

package com.hinnka.mycamera.processor.experimentc.lkr2420

import java.nio.ByteBuffer
import java.nio.ByteOrder

enum class CfaColor { RED, GREEN, BLUE }

/** Standard Camera2 2x2 Bayer arrangements, expressed at the full-sensor origin. */
enum class BayerPattern(private val cells: List<CfaColor>) {
    RGGB(listOf(CfaColor.RED, CfaColor.GREEN, CfaColor.GREEN, CfaColor.BLUE)),
    GRBG(listOf(CfaColor.GREEN, CfaColor.RED, CfaColor.BLUE, CfaColor.GREEN)),
    GBRG(listOf(CfaColor.GREEN, CfaColor.BLUE, CfaColor.RED, CfaColor.GREEN)),
    BGGR(listOf(CfaColor.BLUE, CfaColor.GREEN, CfaColor.GREEN, CfaColor.RED));

    fun colorAt(sensorX: Int, sensorY: Int): CfaColor =
        cells[((sensorY and 1) shl 1) or (sensorX and 1)]

    /**
     * Cell ordinals in [cells] order (RED=0, GREEN=1, BLUE=2), read-only.
     * The hot merge loops hoist this array and index it directly instead of
     * dispatching [colorAt] per tap: identical routing, no enum traffic.
     */
    internal val cellOrdinals = IntArray(4) { cells[it].ordinal }

    /** Ordinal twin of [colorAt]: identical routing as an Int, no enum dispatch. */
    fun colorOrdinalAt(sensorX: Int, sensorY: Int): Int =
        cellOrdinals[((sensorY and 1) shl 1) or (sensorX and 1)]

    fun shifted(sensorX: Int, sensorY: Int): BayerPattern {
        val shiftedCells = List(4) { index ->
            colorAt(sensorX + (index and 1), sensorY + (index shr 1))
        }
        return entries.first { it.cells == shiftedCells }
    }

    companion object {
        fun fromCamera2(value: Int): BayerPattern = when (value) {
            0 -> RGGB
            1 -> GRBG
            2 -> GBRG
            3 -> BGGR
            4 -> throw UnsupportedOperationException("Camera2 CFA RGB is not a 2x2 Bayer mosaic")
            5 -> throw UnsupportedOperationException("Camera2 CFA MONO is not supported by AMaZE")
            6 -> throw UnsupportedOperationException("Camera2 CFA NIR is not supported by AMaZE")
            else -> throw UnsupportedOperationException("Unknown Camera2 CFA arrangement $value")
        }
    }
}

data class IntRectSnapshot(val left: Int, val top: Int, val right: Int, val bottom: Int) {
    val width: Int get() = right - left
    val height: Int get() = bottom - top
}

