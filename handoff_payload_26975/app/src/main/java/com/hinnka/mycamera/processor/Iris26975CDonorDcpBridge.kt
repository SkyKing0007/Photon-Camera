package com.hinnka.mycamera.processor

import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.original129.raw.ColorSpace
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpDefaultBlackRender
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpHueSatMap
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpRenderPlan
import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpTextureResources

/**
 * A C-only type/GL boundary for *real supplied* DCP HueSat/Look profile tables.
 * No profile is invented or inferred from a physical camera ID. The source plan
 * must supply the DCP table values, dimensions and exact DNG linear/sRGB encoding.
 *
 * A normal Camera2 RAW has no DCP tables and takes the original donor null-plan
 * route. When DCP tables exist, HueSat is applied by the donor linear RCD shader
 * BEFORE the Adobe profile exposure ramp, while LookTable is applied by the
 * donor Adobe tone shader AFTER that ramp. No creative LUT is added here.
 *
 * PGTM assets must be handled separately: this bridge does not manufacture a
 * ProfileGainTableMap or claim full original donor RAW/JPEG-R parity.
 */
internal object Iris26975CDonorDcpBridge {
    internal data class Binding(
        val dcpRenderPlan: DcpRenderPlan?,
        val linearHueSat: DcpHueSatMap?,
    )

    fun resolve(plan: Iris26972CColorDeveloper.Plan): Binding {
        val hue = plan.hueSat?.let(::toDonor)
        val look = plan.look?.let(::toDonor)
        if (hue == null && look == null) return Binding(null, null)
        val original = DcpRenderPlan(
            profileName = "Camera2/DNG supplied profile: ${plan.physicalCameraId}",
            workingColorSpace = ColorSpace.ProPhoto,
            baselineExposureOffset = 0f, // Not inferred from HueSat/Look content.
            defaultBlackRender = DcpDefaultBlackRender.Auto,
            supportsOverrange = plan.profileExposure.supportOverrange,
            colorCorrectionMatrix = plan.sensorToProfileRows.copyOf(),
            cameraWhite = plan.cameraWhite.copyOf(),
            hueSatMap = hue,
            lookTable = look,
            toneCurveLut = null, // Original Adobe ACR3 default, never a creative LUT.
        )
        return Binding(original, hue)
    }

    private fun toDonor(map: Iris26972CColorDeveloper.ProfileMap): DcpHueSatMap {
        map.validate()
        val original = DcpHueSatMap(
            hueDivisions = map.hueBins,
            satDivisions = map.saturationBins,
            valueDivisions = map.valueBins,
            values = map.values.copyOf(),
            encoding = map.encoding,
        )
        require(original.isValid) { "Experiment C supplied DCP map has invalid donor dimensions" }
        return original
    }

    /** Bind on the original RawLinearRcdPass's sampler ABI, not a second DCP shader. */
    fun bindLinearHueSat(
        program: Int,
        textures: DcpTextureResources,
        hue: DcpHueSatMap?,
    ) {
        val active = hue?.takeIf(DcpHueSatMap::isValid)
        GLES30.glUniform1i(
            GLES30.glGetUniformLocation(program, "uLinearDcpHueSatEnabled"),
            if (active != null) 1 else 0,
        )
        GLES30.glUniform3i(
            GLES30.glGetUniformLocation(program, "uLinearDcpHueSatDivisions"),
            active?.hueDivisions ?: 1,
            active?.satDivisions ?: 1,
            active?.valueDivisions ?: 1,
        )
        GLES30.glUniform1i(
            GLES30.glGetUniformLocation(program, "uLinearDcpHueSatEncoding"),
            active?.encoding ?: DcpHueSatMap.ENCODING_LINEAR,
        )
        GLES30.glUniform1i(
            GLES30.glGetUniformLocation(program, "uLinearDcpHueSatMap"), 2,
        )
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
        GLES30.glBindTexture(
            GLES30.GL_TEXTURE_3D,
            active?.let(textures::ensureHueSatTexture) ?: textures.ensureDummyTexture(),
        )
    }
}
