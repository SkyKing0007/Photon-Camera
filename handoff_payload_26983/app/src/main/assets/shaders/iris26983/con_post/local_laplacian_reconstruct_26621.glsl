precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D LocalBand;
uniform sampler2D CoarseReconstruction;
out float Output;

/* IRIS_26621_MATCHED_PYRAMID_RECONSTRUCTION
 * Use the same phase-matched EXPAND operator used to form every Laplacian band. This keeps
 * reconstruction algebraically consistent and avoids bilinear coarse-cell geometry. */
float irisCoarseAt(sampler2D tex,ivec2 p){
    ivec2 sz=textureSize(tex,0);
    return texelFetch(tex,clamp(p,ivec2(0),sz-ivec2(1)),0).r;
}
void irisAxis(int fineCoord,out int base,out float wm,out float wc,out float wp){
    base=fineCoord/2;
    if((fineCoord&1)==0){wm=0.125;wc=0.750;wp=0.125;}
    else{wm=0.0;wc=0.5;wp=0.5;}
}
float irisExpand(sampler2D tex,ivec2 p){
    int bx,by;float wxm,wxc,wxp,wym,wyc,wyp;
    irisAxis(p.x,bx,wxm,wxc,wxp);irisAxis(p.y,by,wym,wyc,wyp);
    float sum=0.0;
    sum+=irisCoarseAt(tex,ivec2(bx-1,by-1))*(wxm*wym);
    sum+=irisCoarseAt(tex,ivec2(bx  ,by-1))*(wxc*wym);
    sum+=irisCoarseAt(tex,ivec2(bx+1,by-1))*(wxp*wym);
    sum+=irisCoarseAt(tex,ivec2(bx-1,by  ))*(wxm*wyc);
    sum+=irisCoarseAt(tex,ivec2(bx  ,by  ))*(wxc*wyc);
    sum+=irisCoarseAt(tex,ivec2(bx+1,by  ))*(wxp*wyc);
    sum+=irisCoarseAt(tex,ivec2(bx-1,by+1))*(wxm*wyp);
    sum+=irisCoarseAt(tex,ivec2(bx  ,by+1))*(wxc*wyp);
    sum+=irisCoarseAt(tex,ivec2(bx+1,by+1))*(wxp*wyp);
    return sum;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    Output=texelFetch(LocalBand,p,0).r+irisExpand(CoarseReconstruction,p);
}
