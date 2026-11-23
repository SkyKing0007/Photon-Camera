package com.hinnka.mycamera.processor

import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.security.MessageDigest

/**
 * Strict parser for bjzhou's default Standard PLUT V1 (33^3 RGB UINT16).
 * Pinned source: donor APK assets/luts/digital/standard.plut, SHA below.
 *
 * Donor LutParser.parseBinary consumes little-endian RGB16 and
 * LutConfig.toFloatBuffer() normalizes each component by 65535. The donor
 * uploader uses GL_RGB16F/GL_RGB/GL_FLOAT -- NOT GL_RGB16 unorm.
 * An asset with a different digest is never silently substituted for this
 * donor preset. The binary asset itself is not bundled in this checkpoint:
 * individual LUT assets may have separate copyright/license notices.
 */
internal object Iris26975CDonorStandardPlut {
    const val PRESET_ID = "standard"
    const val SIZE = 33
    const val SHA256 = "af276cbb33fc023ad3c93330efefcbda5d3918a42bcf01a79ffa633e3abe5a0d"
    private const val MAGIC = 0x54554C50
    private const val COMPONENTS = SIZE * SIZE * SIZE * 3
    private const val HEADER_BYTES = 16

    data class Data(val rgbFloat32: FloatBuffer, val size: Int = SIZE) {
        init { require(size == SIZE && rgbFloat32.isDirect && rgbFloat32.remaining() == COMPONENTS) }
    }

    fun readExactDonorAsset(source: InputStream): Data {
        val binary=source.use(InputStream::readBytes)
        require(binary.size == HEADER_BYTES + COMPONENTS * 2) {
            "C pinned donor Standard LUT missing or invalid length"
        }
        val digest=MessageDigest.getInstance("SHA-256").digest(binary)
            .joinToString("") { "%02x".format(it.toInt() and 255) }
        require(digest == SHA256) { "C donor Standard LUT bytes differ from pinned bjzhou asset" }
        val header=ByteBuffer.wrap(binary).order(ByteOrder.LITTLE_ENDIAN)
        require(header.int == MAGIC && header.int == 1 && header.int == SIZE && header.int == 1) {
            "C unsupported donor PLUT header, expected version-1 RGB16 33^3"
        }
        val result=ByteBuffer.allocateDirect(COMPONENTS * 4)
            .order(ByteOrder.nativeOrder()).asFloatBuffer()
        repeat(COMPONENTS){
            result.put((header.short.toInt() and 0xffff)/65535f)
        }
        result.flip()
        return Data(result)
    }

    /**
     * Pinned donor LutImageProcessor default-layer GLSL specialization:
     * - sRGB input and curve (PLUT V1, no stored transfer/gamut); no recipe
     * - mask=0, intensity=1, no nonzero baseline/creative adjustments
     * - original trilinear GL_RGB16F sampled in encoded sRGB coordinates
     * Real selected capture metadata must prove this exact case before use.
     */
    val defaultSrgbShader = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision mediump sampler3D;
        in vec2 vTexCoord;
        layout(location=0) out vec4 fragColor;
        uniform sampler2D uBeforeLutEncodedSrgb;
        uniform sampler3D uOriginalStandardLut;
        vec3 srgbToLinear(vec3 s) {
            return mix(s/12.92, pow((s+0.055)/1.055, vec3(2.4)),
                step(vec3(0.04045),s));
        }
        vec3 linearToSrgb(vec3 linear) {
            vec3 c=max(linear,vec3(0.0));
            return mix(c*12.92,1.055*pow(c,vec3(1.0/2.4))-0.055,
                step(vec3(0.0031308),c));
        }
        void main() {
            vec3 inputEncoded=texture(uBeforeLutEncodedSrgb,vTexCoord).rgb;
            vec3 linearInput=srgbToLinear(inputEncoded);
            // Donor prepareLutLinearInput + applyLutColorSpace are identities for
            // PLUT v1 sRGB; applyLutCurve encodes to sRGB before the 3D lookup.
            vec3 lutInput=linearToSrgb(linearInput);
            vec3 uvw=lutInput*(32.0/33.0)+vec3(0.5/33.0);
            fragColor=vec4(clamp(texture(uOriginalStandardLut,uvw).rgb,0.0,1.0),1.0);
        }
    """.trimIndent()
}
