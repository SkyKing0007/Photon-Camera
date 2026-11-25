// SPDX-FileCopyrightText: 2026 RawLens contributors
// SPDX-License-Identifier: GPL-3.0-or-later

package com.hinnka.mycamera.processor.experimentc.lkr2420

import kotlin.math.floor
import kotlin.math.min

data class LensShadingModel(
    val rows: Int,
    val columns: Int,
    /** Camera2 order: map point, then R, G-even, G-odd, B. */
    val gains: FloatArray,
    val activeArray: IntRectSnapshot,
    val alreadyApplied: Boolean = false
) {
    init {
        require(rows > 0 && columns > 0) { "Lens-shading map dimensions must be positive" }
        require(gains.size == rows * columns * CHANNEL_COUNT) {
            "Lens-shading map size does not match its dimensions"
        }
        require(gains.all { it.isFinite() && it >= 1f }) {
            "Camera2 lens-shading gains must be finite and at least 1.0"
        }
        require(activeArray.width > 0 && activeArray.height > 0) {
            "Lens-shading active array must be non-empty"
        }
    }

    fun gainAt(sensorX: Int, sensorY: Int, color: CfaColor, greenRow: Int = sensorY): Float {
        if (alreadyApplied) return 1f
        val channel = when (color) {
            CfaColor.RED -> 0
            CfaColor.GREEN -> if (greenRow and 1 == 0) 1 else 2
            CfaColor.BLUE -> 3
        }
        val nx = if (activeArray.width == 1) 0f else
            (sensorX - activeArray.left).toFloat() / (activeArray.width - 1).toFloat()
        val ny = if (activeArray.height == 1) 0f else
            (sensorY - activeArray.top).toFloat() / (activeArray.height - 1).toFloat()
        val mapX = nx.coerceIn(0f, 1f) * (columns - 1)
        val mapY = ny.coerceIn(0f, 1f) * (rows - 1)
        val x0 = floor(mapX).toInt()
        val y0 = floor(mapY).toInt()
        val x1 = min(x0 + 1, columns - 1)
        val y1 = min(y0 + 1, rows - 1)
        val tx = mapX - x0
        val ty = mapY - y0
        val top = gain(y0, x0, channel) * (1f - tx) + gain(y0, x1, channel) * tx
        val bottom = gain(y1, x0, channel) * (1f - tx) + gain(y1, x1, channel) * tx
        return top * (1f - ty) + bottom * ty
    }

    private fun gain(row: Int, column: Int, channel: Int): Float =
        gains[((row * columns + column) * CHANNEL_COUNT) + channel]

    private companion object {
        const val CHANNEL_COUNT = 4
    }
}

