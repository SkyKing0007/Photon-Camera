precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D LtmGainBuffer;
out vec3 Output;

/* IRIS_26618_GUIDED_BASE_DETAIL_LTM_APPLY
 * One common scalar preserves RGB chromaticity.  Genuine extended-HDR samples are
 * faded back to unity so the local operator cannot erase physically reconstructed
 * >1 headroom that 26614 UHDR publication is responsible for carrying.
 */
void main() {
    ivec2 imageSize = textureSize(InputBuffer, 0);
    vec2 uv = gl_FragCoord.xy / vec2(max(imageSize, ivec2(1)));
    vec3 rgb = max(texture(InputBuffer, uv).rgb, vec3(0.0));
    float localGain = clamp(texture(LtmGainBuffer, uv).r, 0.50, 1.0);
    float sourcePeak = max(rgb.r, max(rgb.g, rgb.b));
    float preserveHdr = smoothstep(0.95, 1.05, sourcePeak);
    float appliedGain = mix(localGain, 1.0, preserveHdr);
    Output = rgb * appliedGain;
}
