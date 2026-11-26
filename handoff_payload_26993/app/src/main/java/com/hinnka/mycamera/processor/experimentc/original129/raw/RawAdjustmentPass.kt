package com.hinnka.mycamera.processor.experimentc.original129.raw

import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.original129.lut.ShadowsHighlightsShader
import com.hinnka.mycamera.processor.experimentc.original129.lut.ToneBaseGl
import com.hinnka.mycamera.processor.experimentc.original129.utils.PLog
import kotlin.math.max

/** Applies the optional linear-domain shadows/highlights and black/white adjustments. */
internal class RawAdjustmentPass(
    private val quad: RawFullscreenQuad,
) {
    data class Input(
        val textureId: Int,
        val targetFramebufferId: Int,
        val targetTextureId: Int,
        val width: Int,
        val height: Int,
        val highlights: Float,
        val shadows: Float,
        val blacks: Float,
        val whites: Float,
        val iris26993COffShadowLift: Boolean = false,
    )

    data class Output(
        val textureId: Int,
        val width: Int,
        val height: Int,
    )

    private var program = 0
    private var loggedUniformLocations = false
    private val toneBase = ToneBaseGl(TAG)

    fun render(input: Input): Output? {
        val activeProgram = getOrCreateProgram()
        if (activeProgram == 0) {
            PLog.e(TAG, "Unable to create RAW adjustment program")
            return null
        }

        PLog.d(
            TAG,
            "RAW adjustments: highlights=${input.highlights} shadows=${input.shadows} " +
                "blacks=${input.blacks} whites=${input.whites} " +
                "source=${input.textureId} target=${input.targetTextureId} " +
                "size=${input.width}x${input.height} iris26993COffShadowLift=${input.iris26993COffShadowLift}",
        )
        val shadowsHighlightsActive =
            ShadowsHighlightsShader.isActive(input.highlights, input.shadows)
        if (shadowsHighlightsActive &&
            toneBase.prepare(input.width, input.height) &&
            toneBase.bindLevel0()
        ) {
            draw(input, activeProgram, toneBaseOnly = true)
            toneBase.buildLevels { quad.draw(it) }
        }
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, input.targetFramebufferId)
        GLES30.glViewport(0, 0, input.width, input.height)
        GLES30.glClear(GLES30.GL_COLOR_BUFFER_BIT)
        draw(input, activeProgram, toneBaseOnly = false)
        RawGlesProgram.logErrors("RawAdjustmentPass.render")
        return Output(input.targetTextureId, input.width, input.height)
    }

    private fun draw(input: Input, activeProgram: Int, toneBaseOnly: Boolean) {
        GLES30.glUseProgram(activeProgram)
        GLES30.glUniform1i(
            GLES30.glGetUniformLocation(activeProgram, "uToneBaseOnly"),
            if (toneBaseOnly) 1 else 0,
        )
        GLES30.glUniform1i(
            GLES30.glGetUniformLocation(activeProgram, "uIris26993COffShadowLift"),
            if (input.iris26993COffShadowLift) 1 else 0,
        )
        if (toneBaseOnly) {
            toneBase.bindPlaceholders(activeProgram)
        } else {
            toneBase.bind(activeProgram)
        }
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, input.textureId)
        GLES30.glUniform1i(
            GLES30.glGetUniformLocation(activeProgram, "uInputTexture"),
            0,
        )
        GLES30.glUniform2f(
            GLES30.glGetUniformLocation(activeProgram, "uTexelSize"),
            1f / max(1, input.width),
            1f / max(1, input.height),
        )

        val highlightsLocation = GLES30.glGetUniformLocation(activeProgram, "uHighlights")
        val shadowsLocation = GLES30.glGetUniformLocation(activeProgram, "uShadows")
        ShadowsHighlightsShader.bindUniformLocations(
            highlightsLocation = highlightsLocation,
            shadowsLocation = shadowsLocation,
            highlights = input.highlights,
            shadows = input.shadows,
        )
        if (!loggedUniformLocations) {
            loggedUniformLocations = true
            PLog.d(
                TAG,
                "RAW Shadows/Highlights uniforms: uHighlightsLoc=$highlightsLocation " +
                    "uShadowsLoc=$shadowsLocation",
            )
        }
        GLES30.glUniform1f(
            GLES30.glGetUniformLocation(activeProgram, "uBlacks"),
            input.blacks.coerceIn(-1f, 1f),
        )
        GLES30.glUniform1f(
            GLES30.glGetUniformLocation(activeProgram, "uWhites"),
            input.whites.coerceIn(-1f, 1f),
        )
        quad.bindIdentityTextureMatrix(activeProgram)
        quad.draw(activeProgram)
    }

    fun release() {
        if (program != 0) {
            GLES30.glDeleteProgram(program)
            program = 0
        }
        toneBase.release()
    }

    private fun getOrCreateProgram(): Int {
        if (program == 0) {
            program = quad.createProgram(FRAGMENT_SHADER, "rawAdjustment")
        }
        return program
    }

    companion object {
        private const val TAG = "RawAdjustmentPass"

        val FRAGMENT_SHADER = """
            #version 300 es
            precision highp float;
            precision highp sampler2D;

            in vec2 vTexCoord;
            out vec4 fragColor;

            uniform sampler2D uInputTexture;
            uniform vec2 uTexelSize;
            uniform float uHighlights;
            uniform float uShadows;
            uniform float uBlacks;
            uniform float uWhites;
            uniform int uToneBaseOnly;
            uniform int uIris26993COffShadowLift;

            ${ShadowsHighlightsShader.GLSL}

            const vec3 BW_LUMA = vec3(0.2126, 0.7152, 0.0722);
            const float BW_EPSILON = 0.000001;

            float blackInputLevel(float blacks) {
                float value = clamp(blacks, -1.0, 1.0);
                return value < 0.0 ? -value * 0.18 : -value * 0.12;
            }

            float whiteInputLevel(float whites) {
                float value = clamp(whites, -1.0, 1.0);
                return value > 0.0 ? mix(1.0, 0.72, value) : mix(1.0, 1.55, -value);
            }

            float applyInputLevelsToLuma(float luma, float blacks, float whites) {
                float blackLevel = blackInputLevel(blacks);
                float whiteLevel = max(whiteInputLevel(whites), blackLevel + 0.05);
                return max((luma - blackLevel) / max(whiteLevel - blackLevel, BW_EPSILON), 0.0);
            }

            vec3 applyBlackWhiteLevels(vec3 color) {
                float blacks = clamp(uBlacks, -1.0, 1.0);
                float whites = clamp(uWhites, -1.0, 1.0);
                if (abs(blacks) < 0.001 && abs(whites) < 0.001) return color;

                vec3 positiveColor = max(color, vec3(0.0));
                float luma = dot(positiveColor, BW_LUMA);
                float adjustedLuma = applyInputLevelsToLuma(luma, blacks, whites);
                if (luma <= BW_EPSILON) return vec3(adjustedLuma);
                return color * (adjustedLuma / luma);
            }

            // IRIS_26993_C_OFF_SHADOW_LIFT: monotone PCHIP in log2 SDR luminance.
            // This is a pointwise render adjustment, not capture EV, not PGTM.
            float iris26993ShadowEv(float y) {
                if (y <= 0.0005 || y >= 0.65) return 0.0;
                float x = log2(y);
                if (x < -9.9657842847) {
                    float t = x - (-10.9657842847);
                    return max(0.0, ((-0.2010256410 * t + (0.4810256410)) * t + (0.0000000000)) * t + (0.0000000000));
                }
                if (x < -8.9657842847) {
                    float t = x - (-9.9657842847);
                    return max(0.0, ((-0.0487313462 * t + (0.1897569873)) * t + (0.3589743590)) * t + (0.2800000000));
                }
                if (x < -8.3808217839) {
                    float t = x - (-8.9657842847);
                    return max(0.0, ((-1.3768960838 * t + (0.9910946223)) * t + (0.5922942948)) * t + (0.7800000000));
                }
                if (x < -7.6438561898) {
                    float t = x - (-8.3808217839);
                    return max(0.0, ((-0.1764916334 * t + (-0.0344586027)) * t + (0.3383571100)) * t + (1.1900000000));
                }
                if (x < -6.6438561898) {
                    float t = x - (-7.6438561898);
                    return max(0.0, ((0.1792592593 * t + (-0.3992592593)) * t + (0.0000000000)) * t + (1.3500000000));
                }
                if (x < -5.6438561898) {
                    float t = x - (-6.6438561898);
                    return max(0.0, ((0.0237037037 * t + (-0.0829629630)) * t + (-0.2607407407)) * t + (1.1300000000));
                }
                if (x < -4.6438561898) {
                    float t = x - (-5.6438561898);
                    return max(0.0, ((0.2718954248 * t + (-0.3163398693)) * t + (-0.3555555556)) * t + (0.8100000000));
                }
                if (x < -3.6438561898) {
                    float t = x - (-4.6438561898);
                    return max(0.0, ((-0.0573109244 * t + (0.1198599440)) * t + (-0.1725490196)) * t + (0.4100000000));
                }
                if (x < -2.6438561898) {
                    float t = x - (-3.6438561898);
                    return max(0.0, ((-0.0021978022 * t + (0.0069597070)) * t + (-0.1047619048)) * t + (0.3000000000));
                }
                if (x < -1.6438561898) {
                    float t = x - (-2.6438561898);
                    return max(0.0, ((-0.0061416359 * t + (0.0085775333)) * t + (-0.0974358974)) * t + (0.2000000000));
                }
                if (x < -0.8624964763) {
                    float t = x - (-1.6438561898);
                    return max(0.0, ((0.0047385084 * t + (-0.0084120687)) * t + (-0.0987057385)) * t + (0.1050000000));
                }
                if (x < -0.6214883767) {
                    float t = x - (-0.8624964763);
                    return max(0.0, ((1.7954642879 * t + (-0.4350384417)) * t + (-0.1031725365)) * t + (0.0250000000));
                }
                return 0.0;
            }
            vec3 iris26993LiftShadows(vec3 color) {
                float y = dot(color, vec3(0.2126, 0.7152, 0.0722));
                float ev = iris26993ShadowEv(y);
                if (ev <= 0.0) return color;
                float peak = max(color.r, max(color.g, color.b));
                // Uniform channel gain, never clip or dim an existing channel.
                float gain = min(exp2(ev), max(1.0, 1.0 / max(peak, 0.00000001)));
                return color * gain;
            }

            void main() {
                vec3 color = texture(uInputTexture, vTexCoord).rgb;
                if (uToneBaseOnly != 0) {
                    fragColor = vec4(shLogLuminance(color), 0.0, 0.0, 1.0);
                    return;
                }
                color = applyShadowsHighlightsLinear(color, vTexCoord);
                color = applyBlackWhiteLevels(color);
                if (uIris26993COffShadowLift != 0) color = iris26993LiftShadows(color);
                fragColor = vec4(color, 1.0);
            }
        """.trimIndent()
    }
}
