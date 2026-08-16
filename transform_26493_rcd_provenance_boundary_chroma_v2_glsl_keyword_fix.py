#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, tempfile, shutil

SHADER = Path('app/src/main/assets/shaders/motionv2/rcd26489_write.glsl')
HOST = Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java')
EXPECTED = {
    SHADER: '78b9894e40d584b9bc9abce69c13cdd7057a51fc99e825c6581183d762c882ec',
    HOST: 'd7530dde2fe75bea616683f18c08918e583381e7baaaa3feb393cc3a4b823a7f',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def apply(root: Path):
    for rel,h in EXPECTED.items():
        p=root/rel
        if not p.is_file(): raise SystemExit(f'missing exact V5B target: {rel}')
        a=sha(p)
        if a!=h: raise SystemExit(f'V5B target hash mismatch {rel}: {a} expected {h}')

    sp=root/SHADER
    s=sp.read_text()
    s=s.replace(
        'precision highp image2D;\n',
        'precision highp image2D;\nprecision highp sampler2D;\n',1)
    s=s.replace(
        'layout(rgba16f, binding = 9) writeonly uniform highp image2D OutputRgb;\n',
        'layout(rgba16f, binding = 9) writeonly uniform highp image2D OutputRgb;\n'
        'uniform highp sampler2D HighlightProvenance;\n',1)

    anchor='''float raw(ivec2 p){return cfa[idxAt(p)];}\n'''
    if s.count(anchor)!=1: raise SystemExit('shader raw() anchor mismatch')
    helper=r'''float raw(ivec2 p){return cfa[idxAt(p)];}

/* IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER
 * V5B RCD reconstruction remains authoritative. This is a final-write-only
 * safeguard for the one residual failure now proven by trophies, chandelier,
 * thin bright branches and the repeated bright shutter slats:
 *   high-luminance NORMAL/SHORT_VALIDATED <-> CENSORED boundaries can retain
 *   one-pixel green<->magenta opponent-color zippering after demosaic.
 *
 * Hard invariants:
 * - no CENSORED provenance nearby -> exact V5B RGB
 * - no trusted provenance nearby -> exact V5B RGB
 * - not a bright highlight -> exact V5B RGB
 * - no sign-reversing, locally incoherent opponent chroma -> exact V5B RGB
 * - no blur, no geometry change, no global desaturation
 *
 * The only AHD-inspired idea used here is local homogeneity: horizontal and
 * vertical neighbor pairs compete as a *confirmation* of coherent chroma.
 * It does not replace RCD or choose a new demosaic reconstruction.
 */
const float PROVENANCE_NORMAL = 0.0;
const float PROVENANCE_CENSORED = 1.0;
const float PROVENANCE_SHORT_VALIDATED = 2.0;
float provenanceGlobal(ivec2 gp){
    ivec2 safe=clamp(gp,ivec2(0),rawSize-ivec2(1));
    return texelFetch(HighlightProvenance,safe>>1,0).r;
}
bool isCensored(float s){return abs(s-PROVENANCE_CENSORED)<0.25;}
bool isTrusted(float s){return !isCensored(s);}
vec3 rcdRgb(ivec2 p){
    int i=idxAt(p);
    return max(vec3(red[i],green[i],blue[i]),vec3(0.0))
            /max(calculationWb,vec3(1.0e-6));
}
float rgbMean(vec3 v){return (v.r+v.g+v.b)/3.0;}
vec2 opponent(vec3 v){
    float m=max(rgbMean(v),1.0e-4);
    return vec2(v.r-v.g,v.b-v.g)/m;
}
vec3 fromMeanOpponent(float m,vec2 o){
    vec2 d=o*m;
    float g=m-(d.x+d.y)/3.0;
    return max(vec3(g+d.x,g,g+d.y),vec3(0.0));
}
float max3(vec3 v){return max(v.r,max(v.g,v.b));}

vec3 stabilizeHighlightBoundary(ivec2 lp,ivec2 gp,vec3 current){
    /* Cheapest/strongest identity gate first: ordinary pixels do no provenance work. */
    float peak=max3(current);
    float highlightGate=smoothstep(0.78,0.96,peak);
    if(highlightGate<=0.0) return current;

    /* Provenance is packed 2x2, so +/-2 full-resolution samples inspect exactly
     * the four adjacent ownership cells without widening the correction region. */
    float s0=provenanceGlobal(gp);
    float sxm=provenanceGlobal(gp+ivec2(-2,0));
    float sxp=provenanceGlobal(gp+ivec2(2,0));
    float sym=provenanceGlobal(gp+ivec2(0,-2));
    float syp=provenanceGlobal(gp+ivec2(0,2));
    bool hasCensored=isCensored(s0)||isCensored(sxm)||isCensored(sxp)||isCensored(sym)||isCensored(syp);
    bool hasTrusted=isTrusted(s0)||isTrusted(sxm)||isTrusted(sxp)||isTrusted(sym)||isTrusted(syp);
    if(!hasCensored || !hasTrusted) return current;

    vec3 l=rcdRgb(lp+ivec2(-1,0));
    vec3 r=rcdRgb(lp+ivec2(1,0));
    vec3 u=rcdRgb(lp+ivec2(0,-1));
    vec3 d=rcdRgb(lp+ivec2(0,1));
    float cm=max(rgbMean(current),1.0e-4);
    vec2 co=opponent(current);
    float coMag=length(co);
    if(coMag<0.018) return current;

    vec2 lo=opponent(l), ro=opponent(r), uo=opponent(u), doo=opponent(d);
    vec2 hg=0.5*(lo+ro), vg=0.5*(uo+doo);
    float hLuma=(abs(rgbMean(l)-cm)+abs(rgbMean(r)-cm))/(2.0*cm);
    float vLuma=(abs(rgbMean(u)-cm)+abs(rgbMean(d)-cm))/(2.0*cm);
    float hPair=length(lo-ro);
    float vPair=length(uo-doo);
    float hCost=hLuma+0.55*hPair;
    float vCost=vLuma+0.55*vPair;
    vec2 guide=hCost<=vCost?hg:vg;
    float guideCost=min(hCost,vCost);
    float guideMag=length(guide);
    if(guideMag<0.012) return current;

    float cosine=dot(co,guide)/max(coMag*guideMag,1.0e-6);
    float opposition=smoothstep(0.18,0.72,-cosine);
    float pairCoherence=1.0-smoothstep(0.10,0.36,guideCost);
    float currentCensored=isCensored(s0)?1.0:0.0;
    float authority=mix(0.32,0.64,currentCensored);
    float strength=authority*highlightGate*opposition*pairCoherence;
    if(strength<=0.0) return current;

    vec3 coherentRgb=fromMeanOpponent(cm,guide);
    return mix(current,coherentRgb,clamp(strength,0.0,0.64));
}
'''
    s=s.replace(anchor,helper,1)

    old='''    if(boundary) rgb=ppg(lp); else {int i=idxAt(lp);rgb=max(vec3(red[i],green[i],blue[i]),vec3(0.0));}\n    rgb/=max(calculationWb,vec3(1.0e-6));\n    imageStore(OutputRgb,gp,vec4(rgb,1.0));\n'''
    new='''    if(boundary) {\n        rgb=ppg(lp)/max(calculationWb,vec3(1.0e-6));\n    } else {\n        rgb=rcdRgb(lp);\n        rgb=stabilizeHighlightBoundary(lp,gp,rgb);\n    }\n    imageStore(OutputRgb,gp,vec4(rgb,1.0));\n'''
    if s.count(old)!=1: raise SystemExit('shader write anchor mismatch')
    s=s.replace(old,new,1)
    # GLSL ES reserves `coherent` as a memory qualifier. 26493 V1/V2 used
    # it as a local variable name, which glslang correctly rejected before runtime.
    # Keep the mathematical operation identical but hard-fail if that reserved
    # identifier ever reappears as a declaration.
    if 'vec3 coherent=' in s or 'vec2 coherent=' in s or 'float coherent=' in s:
        raise SystemExit('reserved GLSL identifier coherent used as variable')
    if 'vec3 coherentRgb=fromMeanOpponent(cm,guide);' not in s:
        raise SystemExit('26493 coherentRgb portability fix missing')
    sp.write_text(s)

    hp=root/HOST
    h=hp.read_text()
    oldh='''                    glProg.useAssetProgram("motionv2/rcd26489_write", true);\n                    glProg.setBufferCompute("CfaBuf", cfa);\n'''
    newh='''                    glProg.useAssetProgram("motionv2/rcd26489_write", true);\n                    /* IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER_BINDING\n                     * Read-only provenance confirms the tiny region where final-write\n                     * chroma stabilization is allowed. It does not alter provenance.\n                     */\n                    glProg.setTexture("HighlightProvenance",\n                            postPipeline.motionV2HighlightProvenanceTexture);\n                    glProg.setBufferCompute("CfaBuf", cfa);\n'''
    if h.count(oldh)!=1: raise SystemExit('host write-stage anchor mismatch')
    h=h.replace(oldh,newh,1)
    hp.write_text(h)

    # Strict scope and preservation markers.
    if 'IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER' not in sp.read_text():
        raise SystemExit('26493 shader marker missing')
    if 'IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER_BINDING' not in hp.read_text():
        raise SystemExit('26493 host marker missing')
    print('26493 V3 TRANSFORM PASS files=2 V5B_RCD_CORE_UNCHANGED=true correction=finalWriteOnly glslReservedKeywordFix=coherentRgb')


def self_test():
    # Synthetic behavioral model of the hard gating idea. Not a GLSL compiler test.
    import math
    def smooth(a,b,x):
        t=max(0,min(1,(x-a)/(b-a)))
        return t*t*(3-2*t)
    def strength(cur, guide, peak, censored, cost):
        cm=math.hypot(*cur); gm=math.hypot(*guide)
        if cm<.018 or gm<.012: return 0
        cos=(cur[0]*guide[0]+cur[1]*guide[1])/max(cm*gm,1e-6)
        opp=smooth(.18,.72,-cos)
        coh=1-smooth(.10,.36,cost)
        return (.64 if censored else .32)*smooth(.78,.96,peak)*opp*coh
    assert strength((.12,-.10),(-.10,.09),.99,True,.03)>.45, 'zipper should activate'
    assert strength((.12,-.10),(.10,-.08),.99,True,.03)==0, 'coherent real chroma must not activate'
    assert strength((.12,-.10),(-.10,.09),.60,True,.03)==0, 'non-highlight must not activate'
    assert strength((.01,-.005),(-.01,.005),.99,True,.03)==0, 'tiny chroma must not activate'
    print('26493 MODEL SELF-TEST PASS zipper=true coherentIdentity=true lowlightIdentity=true lowChromaIdentity=true')

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--self-test': self_test()
    elif len(sys.argv)==2: apply(Path(sys.argv[1]).resolve())
    else: raise SystemExit('usage: transform_26493_rcd_provenance_boundary_chroma_v1.py --self-test | <repo-root>')
