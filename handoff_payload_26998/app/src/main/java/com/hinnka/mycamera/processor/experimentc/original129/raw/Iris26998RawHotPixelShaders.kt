package com.hinnka.mycamera.processor.experimentc.original129.raw

internal object Iris26998RawHotPixelShaders {
    val SUPPRESS = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;

        uniform highp usampler2D uRaw;
        uniform highp usampler2D uHotPixelMask;
        uniform ivec2 uImageSize;
        layout(location = 0) out highp uint oRaw;

        const int NEIGHBOR_COUNT = 12;
        const int CARDINAL_COUNT = 4;
        const ivec2 SAME_CFA_OFFSETS[NEIGHBOR_COUNT] = ivec2[NEIGHBOR_COUNT](
            ivec2(-2,  0), ivec2( 2,  0),
            ivec2( 0, -2), ivec2( 0,  2),
            ivec2(-2, -2), ivec2( 2, -2),
            ivec2(-2,  2), ivec2( 2,  2),
            ivec2(-4,  0), ivec2( 4,  0),
            ivec2( 0, -4), ivec2( 0,  4)
        );

        bool inside(ivec2 coord) {
            return all(greaterThanEqual(coord, ivec2(0))) && all(lessThan(coord, uImageSize));
        }

        bool maskedAt(ivec2 coord) {
            uvec4 packedMask = texelFetch(uHotPixelMask, ivec2(coord.x >> 2, coord.y), 0);
            return packedMask[coord.x & 3] != 0u;
        }

        uint medianOf(inout uint values[NEIGHBOR_COUNT], int count) {
            for (int i = 1; i < count; ++i) {
                uint value = values[i];
                int j = i - 1;
                while (j >= 0 && values[j] > value) {
                    values[j + 1] = values[j];
                    j -= 1;
                }
                values[j + 1] = value;
            }
            int middle = count / 2;
            if ((count & 1) != 0) return values[middle];
            return (values[middle - 1] + values[middle] + 1u) >> 1;
        }

        void main() {
            ivec2 coord = ivec2(gl_FragCoord.xy);
            uint original = texelFetch(uRaw, coord, 0).r;
            if (!maskedAt(coord)) {
                oRaw = original;
                return;
            }

            uint values[NEIGHBOR_COUNT];
            int count = 0;
            for (int i = 0; i < CARDINAL_COUNT; ++i) {
                ivec2 neighbor = coord + SAME_CFA_OFFSETS[i];
                if (inside(neighbor) && !maskedAt(neighbor)) {
                    values[count] = texelFetch(uRaw, neighbor, 0).r;
                    count += 1;
                }
            }
            if (count == 0) {
                for (int i = CARDINAL_COUNT; i < NEIGHBOR_COUNT; ++i) {
                    ivec2 neighbor = coord + SAME_CFA_OFFSETS[i];
                    if (inside(neighbor) && !maskedAt(neighbor)) {
                        values[count] = texelFetch(uRaw, neighbor, 0).r;
                        count += 1;
                    }
                }
            }
            oRaw = count == 0 ? original : medianOf(values, count);
        }
    """.trimIndent()
}
