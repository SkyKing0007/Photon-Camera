precision highp float;
precision mediump sampler2D;

uniform sampler2D GlobalMappedLog;
uniform float referenceLog;
uniform float sigmaEv;
uniform float edgeSlope;
out float Output;

/* IRIS_26621_TRUE_LOCAL_LAPLACIAN_REMAP
 * Fast Local-Laplacian intensity slice. alpha=1 exactly preserves small/detail
 * log-luminance differences. Only deviations outside sigmaEv use the gentler
 * edge slope. The remap is continuous, monotonic and symmetric around referenceLog. */
float irisRemap(float x){
    float d=x-referenceLog;
    float a=abs(d);
    float mapped=a<=sigmaEv ? a : sigmaEv+edgeSlope*(a-sigmaEv);
    return referenceLog+(d<0.0?-mapped:mapped);
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    Output=irisRemap(texelFetch(GlobalMappedLog,p,0).r);
}
