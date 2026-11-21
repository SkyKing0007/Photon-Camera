package com.hinnka.mycamera.processor

/**
 * Experiment C-only geometric port of bjzhou/PhotonCamera 1.29.0
 * MgcRawLkPyramidPlan.kt (Git blob e9887340f8b3e8c447c6ec747c7188b6a01b96c0).
 *
 * No A/B alignment code is imported or invoked. The schedule is frozen before any
 * frame enters the C-only temporal solver. This is geometry, not the LK shader.
 */
internal class Iris26972CDonorSabreLkPyramidPlan(
    rawWidth: Int,
    rawHeight: Int,
    val maximumTileSize: Int,
) {
    data class Level(
        val width: Int,
        val height: Int,
        val scale: Int,
        val downsample: Int,
        val tileSize: Int,
        val gridWidth: Int,
        val gridHeight: Int,
    )

    val levels: List<Level>

    init {
        require(rawWidth > 0 && rawHeight > 0)
        require(maximumTileSize == 16 || maximumTileSize == 32 || maximumTileSize == 64)
        val fineWidth = (rawWidth + 1) / 2
        val fineHeight = (rawHeight + 1) / 2
        val result = ArrayList<Level>()
        var scale = 1
        var tileLimit = 64
        var tileSize = maximumTileSize
        while (scale < 256) {
            val finest = result.isEmpty()
            val downsample = if (finest) 1 else if (result.size == 1) 2 else 4
            val levelWidth = if (finest) fineWidth else
                (result.last().width - 1 + downsample / 2) / downsample + 1
            val levelHeight = if (finest) fineHeight else
                (result.last().height - 1 + downsample / 2) / downsample + 1
            val margin = if (finest) 1 else 3
            val gridWidth = (levelWidth - margin) / tileSize - 1
            val gridHeight = (levelHeight - margin) / tileSize - 1
            if (gridWidth <= 0 || gridHeight <= 0) break
            result += Level(levelWidth, levelHeight, scale,
                downsample, tileSize, gridWidth, gridHeight)
            scale *= if (finest) 2 else 4
            tileSize = minOf(tileSize, tileLimit).coerceAtLeast(8)
            tileLimit /= 4
        }
        require(result.isNotEmpty()) { "C RAW dimensions cannot support pinned donor LK tiles" }
        levels = result
    }

    val maximumDisplacement: Float
        get() = levels.mapIndexed { index, level ->
            level.scale * if (index == 0) 2 else 3
        }.sum().toFloat()
}
