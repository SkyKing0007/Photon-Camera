package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

import android.opengl.GLES30
import com.hinnka.mycamera.processor.Iris26972CAdobeAcr3

/**
 * Experiment C **integration adapters**, not bjzhou original classes. The six independently
 * verified donor tone sources next to this file are original package-header-only transplants.
 * Unsupported creative engines are intentionally uncallable. Do NOT treat this temporary
 * closure as complete donor RAW, PGTM, MGC, or HDR, and do NOT enable publication with it.
 */
internal class RawToneMappingParameters(
    val blacks: Float = 0f,
    val whites: Float = 0f,
) {
    init {
        require(blacks == 0f && whites == 0f) {
            "Experiment C Adobe default tone: unsupported black/white adjustment"
        }
    }
}

/** Selected AdobeCurve-only default adjustments; all other tone engines are fail-closed. */
internal object RawToneMappingGl {
    fun bindRawToneMappingUniforms(program: Int, params: RawToneMappingParameters) {
        check(params.blacks == 0f && params.whites == 0f)
        GLES30.glUniform1f(GLES30.glGetUniformLocation(program, "uBlacks"), 0f)
        GLES30.glUniform1f(GLES30.glGetUniformLocation(program, "uWhites"), 0f)
    }
}

/** C-only interface to the already-verified byte-exact 1025-sample original ACR3 table. */
internal object ACR3Curve {
    fun samples(): FloatArray = Iris26972CAdobeAcr3.samples()
}

internal class SpectralFilmLut(val graph: Any? = null)
internal class HncsRenderPlan
internal class LumixRenderPlan
internal class CanonRenderPlan
internal class LeicaRenderPlan
internal class FotufilmRenderRequest
internal class FotufilmMeterCells

private const val REJECT_UNSELECTED = "Experiment C supports original Adobe Curve only"
private val UNSUPPORTED_TONE_SHADER = RawEngineToneShaderDefinition(
    engineUniforms = "",
    engineFunctions = "__C_NON_ADOBE_ENGINE_CANNOT_COMPILE__",
)

internal open class UnselectedRawToneAlgorithm(quad:RawFullscreenQuad):
    RawRenderingEngineToneAlgorithm(quad, UNSUPPORTED_TONE_SHADER)

internal class AgXToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class SpektrafilmToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class DarktableSigmoidToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class DarktableFilmicToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class HncsToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class LumixToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class CanonToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)
internal class LeicaToneAlgorithm(q:RawFullscreenQuad):UnselectedRawToneAlgorithm(q)

internal class SpektrafilmGraphToneStage(q:RawFullscreenQuad) {
    fun render(input:RawEngineTonePass.Input):RawEngineTonePass.Output? = error(REJECT_UNSELECTED)
    fun discardInactiveGraph() = Unit
    fun measureMaximum(input:RawEngineTonePass.Input,l:Int,t:Int,w:Int,h:Int):Float = error(REJECT_UNSELECTED)
    fun release() = Unit
}
internal class SpektrafilmScannerPass(q:RawFullscreenQuad) {
    fun render(input:RawEngineTonePass.Input,tone:SpektrafilmToneAlgorithm):RawEngineTonePass.Output? = error(REJECT_UNSELECTED)
    fun release() = Unit
}
internal class FotufilmToneStage(q:RawFullscreenQuad) {
    val inputAlgorithm = UnselectedRawToneAlgorithm(q)
    fun render(input:RawEngineTonePass.Input):RawEngineTonePass.Output? = error(REJECT_UNSELECTED)
    fun meterTile(input:RawEngineTonePass.Input,x:Int,y:Int,w:Int,h:Int,size:Int):FotufilmMeterCells = error(REJECT_UNSELECTED)
    fun prewarm():Boolean = error(REJECT_UNSELECTED)
    fun release() = Unit
}

internal object AgXToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object SpektrafilmToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object DarktableSigmoidToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object DarktableFilmicToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object HncsToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object LumixToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object CanonToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object LeicaToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
internal object FotufilmInputToneShader { val DEFINITION:RawEngineToneShaderDefinition get()=error(REJECT_UNSELECTED) }
