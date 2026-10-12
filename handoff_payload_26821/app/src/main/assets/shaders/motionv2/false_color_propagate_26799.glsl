precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D ClassMask;
uniform sampler2D PrevConnected;
uniform int iris26799Iteration;
/* IRIS_26816_TELEMETRY_SSBO_RETIRED: image classification/propagation unchanged. */
out float Output;

/* IRIS_26799_TRUE_BOUNDED_CONNECTED_PROPAGATION
 * Every accepted weak/plateau pixel becomes part of PrevConnected for the following pass.
 * Eight fixed ping-pong iterations provide true bounded connectivity without unbounded flood fill.
 */
float fetchMask(sampler2D tex,ivec2 p){
    ivec2 sz=textureSize(tex,0);p=clamp(p,ivec2(0),sz-ivec2(1));return texelFetch(tex,p,0).r;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float cls=fetchMask(ClassMask,p);
    bool candidate=cls>=0.35;
    bool seed=cls>=0.75;
    bool neutralParentDirect=cls>=0.90&&cls<=0.94;
    float prev=fetchMask(PrevConnected,p);
    bool already=prev>=0.75;
    bool neighbor=false;
    for(int oy=-1;oy<=1;oy++){
        for(int ox=-1;ox<=1;ox++){
            if(ox==0&&oy==0)continue;
            neighbor=neighbor||(fetchMask(PrevConnected,p+ivec2(ox,oy))>=0.75);
        }
    }
    bool connected=seed||(candidate&&(already||neighbor));

    /* IRIS_26821_CONNECTED_STATE_CONFIDENCE_SEPARATION
     * R8 stays the sole mask carrier, but connectivity and classifier confidence are no longer
     * conflated. Values >=0.75 are CONNECTED. Direct classifier candidates that have not reached
     * a seed retain their original 0.40/0.55 code below 0.75. Connected plateau/weak candidates
     * are re-encoded into disjoint connected ranges, so all eight inherited propagation passes
     * can carry connectivity while render can still recover the original evidence class.
     * Existing connected candidates retain their first connection-distance code instead of being
     * rewritten on later passes. */
    float outCode=cls;
    if(connected){
        if(neutralParentDirect){
            outCode=0.92;
        }else if(cls>=0.99){
            outCode=1.0;
        }else if(cls>=0.80){
            outCode=0.86;
        }else if(cls>=0.50){
            if(already&&prev>=0.775&&prev<0.835){
                outCode=prev;
            }else{
                float iter=clamp(float(iris26799Iteration)/7.0,0.0,1.0);
                outCode=mix(0.83,0.78,iter);
            }
        }else{
            outCode=(already&&prev>=0.75&&prev<0.775)?prev:0.76;
        }
    }
    Output=outCode;
}
