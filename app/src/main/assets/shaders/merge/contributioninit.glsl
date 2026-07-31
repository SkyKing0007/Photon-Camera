#define LAYOUT //
LAYOUT
precision highp float;
layout(r32f, binding = 0) uniform highp writeonly image2D outTexture;
uniform float initialContribution;

void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);

    imageStore(
            outTexture,
            xy,
            vec4(
                    initialContribution,
                    0.0,
                    0.0,
                    1.0
            )
    );
}
