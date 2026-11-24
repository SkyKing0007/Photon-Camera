package com.hinnka.mycamera.processor.experimentc.original129.lut

/** Original pinned shader required by donor RAW adjustments; optional preview/creative shaders excluded. */
object Shaders {
    val SIMPLE_VERTEX_SHADER = """
        #version 300 es
        in vec4 aPosition;
        in vec2 aTexCoord;
        out vec2 vTexCoord;
        void main() {
            gl_Position = aPosition;
            vTexCoord = aTexCoord;
        }
    """.trimIndent()
}
