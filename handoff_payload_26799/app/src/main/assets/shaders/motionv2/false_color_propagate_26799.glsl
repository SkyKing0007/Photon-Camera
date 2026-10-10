precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D ClassMask;
uniform sampler2D PrevConnected;
uniform int iris26799Iteration;
layout(std430, binding=1) buffer iris26799Stats {
    uint iris26799Counters[20];
};
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
    if(connected&&!already&&!seed&&iris26799Iteration>=0&&iris26799Iteration<8){
        atomicAdd(iris26799Counters[6+iris26799Iteration],1u);
    }
    Output=connected?1.0:0.0;
}
