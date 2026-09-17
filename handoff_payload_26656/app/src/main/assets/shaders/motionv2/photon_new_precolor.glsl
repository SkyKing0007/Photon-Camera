precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform sampler2D ExposureCurve;
uniform vec3 neutralPoint;
uniform float adaptiveWhitePoint;
out vec3 Output;
const vec3 PHOTON_LUMA=vec3(0.299,0.587,0.114);
float sampleExposureCurve(float x){return texture(ExposureCurve,vec2(clamp(x,0.0,1.0),0.5)).r;}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0));
    float aw=max(adaptiveWhitePoint,1.0);
    vec3 photonInput=(cameraRgb/max(neutralPoint,vec3(1.0e-6)))/aw;
    float br=dot(photonInput,PHOTON_LUMA);
    if(br<=1.0e-8){Output=vec3(0.0);return;}
    float mapped=sampleExposureCurve(br);
    float scalar=mapped/(br+1.0e-3);
    /* Photon later multiplies by NEUTRALPOINT in its color stage. Iris color expects cameraRGB,
       so emit the algebraically equivalent cameraRGB/aw * scalar and leave Iris color unchanged. */
    Output=(cameraRgb/aw)*scalar;
}
