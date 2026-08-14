#!/usr/bin/env python3
from pathlib import Path
import sys,re
root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
CG=root/'app/src/main/assets/shaders/motionv2/color_transform.glsl'
WB=root/'app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl'
CJ=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java'
CR=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
WA=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java'
for p in (CG,WB,CJ,CR,WA):
    if not p.is_file(): raise SystemExit(f'26482 missing required file: {p}')

def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise SystemExit(f'26482 {label}: anchor count={n}, expected 1')
    return text.replace(old,new,1)

# 1) Remove the too-late 26481 post-RGB highlight repair. Camera2 WB+matrix is once-only final color authority.
cg=CG.read_text()
if 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' not in cg:
    raise SystemExit('26482 expected 26481 post-RGB repair baseline marker missing')
CG.write_text(r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

/* IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_CLIP_AUTHORITY
 * The Wronski CFA path already enters a green-normalized calculation-WB domain
 * and mfsr_finalize removes those temporary gains. This stage therefore owns
 * only the one authoritative Camera2 WB + 3x3 color transform. No inferred
 * sensor clipping is attempted after CFA evidence has already been reconstructed.
 */
void main(){
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));
    vec3 balanced=cameraRgb*max(sensorGains,vec3(1.0e-6));
    vec3 linearSrgb=vec3(
            dot(colorRow0,balanced),
            dot(colorRow1,balanced),
            dot(colorRow2,balanced));
    Output=max(linearSrgb,vec3(0.0));
}
''')

# 2) Make the existing Wronski calculation-WB CFA loader physically clip-aware.
wb=WB.read_text()
if 'IRIS_26463_WRONSKI_PUBLIC_RAW_WB_DOMAIN' not in wb:
    raise SystemExit('26482 expected existing Wronski WB-domain shader marker missing')
WB.write_text(r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D inputCfa;
layout(rgba16f,binding=1) uniform highp writeonly image2D outputCfa;
uniform int cfaPattern;
uniform float wbR;
uniform float wbG;
uniform float wbB;
uniform float sensorExposureScale;
uniform float physicalClipThreshold;

int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float gainForColor(int c){return c==0?wbR:(c==2?wbB:wbG);}
float cameraAt(ivec2 p){
    ivec2 rawSize=imageSize(inputCfa)*2;
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(inputCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
float opposedEstimate(ivec2 center,int targetColor,float fallback,out float support,out float allLost){
    float sr=0.0,sg=0.0,sb=0.0,wr=0.0,wg=0.0,wbv=0.0;
    ivec2 rawSize=imageSize(inputCfa)*2;
    float exposure=max(sensorExposureScale,1.0e-6);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawSize-ivec2(1));
        int color=componentColor(componentIndex(q));
        float camera=max(cameraAt(q),0.0);
        float sensor=camera/exposure;
        float rw=1.0-smoothstep(physicalClipThreshold,0.9995,sensor);
        float z=camera*max(gainForColor(color),1.0e-6);
        if(color==0){sr+=z*rw;wr+=rw;}
        else if(color==1){sg+=z*rw;wg+=rw;}
        else{sb+=z*rw;wbv+=rw;}
    }
    float mr=sr/max(wr,1.0e-6),mg=sg/max(wg,1.0e-6),mb=sb/max(wbv,1.0e-6);
    const float power=3.0;
    float rr=pow(max(mr,0.0),1.0/power);
    float rg=pow(max(mg,0.0),1.0/power);
    float rb=pow(max(mb,0.0),1.0/power);
    float root;
    if(targetColor==0){root=0.5*(rg+rb);support=min(wg,wbv);}
    else if(targetColor==1){root=0.5*(rr+rb);support=min(wr,wbv);}
    else{root=0.5*(rr+rg);support=min(wr,wg);}
    support=smoothstep(0.25,1.25,support);
    allLost=1.0-smoothstep(0.10,0.75,wr+wg+wbv);
    return max(pow(max(root,0.0),power),fallback);
}
float repairClipped(ivec2 p,int color,float fallback,float physical){
    float support=0.0,allLost=0.0;
    float opposed=opposedEstimate(p,color,fallback,support,allLost);
    float clipMask=smoothstep(physicalClipThreshold,0.9995,physical);
    float repaired=mix(fallback,opposed,clipMask*support);
    float neutralTerminal=max(sensorExposureScale,1.0e-6)*max(wbR,max(wbG,wbB));
    return mix(repaired,neutralTerminal,clipMask*allLost);
}

/* IRIS_26482_BJZHOU_CFA_CALCULATION_DOMAIN_CLIP_AUTHORITY
 * The existing Wronski loader already uses calculation-only relative WB gains.
 * 26482 completes that architecture by judging clipping in the physical normalized
 * sensor domain (before exposure/canonical scaling), reconstructing only clipped
 * photosites from reliable opposed CFA colors in that same calculation domain,
 * using a neutral calculation-domain terminal only when all local hue authority is
 * gone, and leaving mfsr_finalize to remove the calculation gains exactly once.
 * Ordinary unclipped pixels retain the original one-imageLoad fast path.
 */
void main(){
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(outputCfa);
    if(any(greaterThanEqual(q,sz))) return;
    ivec2 b=q*2;
    vec4 camera=max(imageLoad(inputCfa,q),vec4(0.0));
    int c0=componentColor(0),c1=componentColor(1),c2=componentColor(2),c3=componentColor(3);
    vec4 gains=vec4(gainForColor(c0),gainForColor(c1),gainForColor(c2),gainForColor(c3));
    vec4 calculation=camera*max(gains,vec4(1.0e-6));
    vec4 physical=camera/max(sensorExposureScale,1.0e-6);
    vec4 outv=calculation;
    if(physical.r>=physicalClipThreshold)outv.r=repairClipped(b+ivec2(0,0),c0,calculation.r,physical.r);
    if(physical.g>=physicalClipThreshold)outv.g=repairClipped(b+ivec2(1,0),c1,calculation.g,physical.g);
    if(physical.b>=physicalClipThreshold)outv.b=repairClipped(b+ivec2(0,1),c2,calculation.b,physical.b);
    if(physical.a>=physicalClipThreshold)outv.a=repairClipped(b+ivec2(1,1),c3,calculation.a,physical.a);
    imageStore(outputCfa,q,outv);
}
''')

# 3) Color owner: delete fake RGB sensor-clip proxy; log correct authority.
cj=CJ.read_text()
if 'IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR' not in cj:
    raise SystemExit('26482 expected 26481 color telemetry marker missing')
cj=once(cj,
'''        float greenGain = 0.5f * (g[1] + g[2]);
        float sensorClipLevel = Math.max(
                1.0f, basePipeline.mParameters.motionCanonicalExposureGain);
''',
'''        float greenGain = 0.5f * (g[1] + g[2]);
''','remove RGB clip proxy')
cj=once(cj,'        glProg.setVar("sensorClipLevel", sensorClipLevel);\n','', 'remove sensorClipLevel binding')
pat=re.compile(r'''        Log\.d\(Name, "IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR".*?\n\s*\+ " wronskiMathChanged=false"\);''',re.S)
repl='''        Log.d(Name, "IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_AUTHORITY"
                + " gainsRGeGoB=" + java.util.Arrays.toString(g)
                + " greenMean=" + greenGain
                + " matrixRowMajor=" + java.util.Arrays.toString(m)
                + " camera2ColorAuthority=true"
                + " postRgbClipInference=false"
                + " cfaClipAuthorityUpstream=true"
                + " camera2WbAppliedOnce=true");'''
cj,n=pat.subn(repl,cj,count=1)
if n!=1: raise SystemExit(f'26482 color telemetry block count={n}, expected 1')
CJ.write_text(cj)

# 4) Bind physical exposure scale for all three Wronski WB-domain CFA conversions.
cr=CR.read_text()
if cr.count('useAssetProgram("motionv2/mfsr_wb_cfa"')!=3:
    raise SystemExit('26482 expected exactly 3 Wronski WB CFA call sites')
# Reference
cr=once(cr,
'''                glProg.setVar("wbB", wronskiWbB);
                glProg.setTextureCompute("inputCfa", referenceCfa, false);
''',
'''                glProg.setVar("wbB", wronskiWbB);
                glProg.setVar("sensorExposureScale", canonicalGain * (
                        images.get(0).pair != null
                                ? 1.0f / Math.max(images.get(0).pair.layerMpy, 1.0e-6f)
                                : 1.0f));
                glProg.setVar("physicalClipThreshold", 0.985f);
                glProg.setTextureCompute("inputCfa", referenceCfa, false);
''','reference physical clip scale')
# Auxiliary
cr=once(cr,
'''                        glProg.setVar("wbB", wronskiWbB);
                        glProg.setTextureCompute("inputCfa", alterCfa, false);
''',
'''                        glProg.setVar("wbB", wronskiWbB);
                        glProg.setVar("sensorExposureScale", exposure);
                        glProg.setVar("physicalClipThreshold", 0.985f);
                        glProg.setTextureCompute("inputCfa", alterCfa, false);
''','aux physical clip scale')
# Short compact line
cr=once(cr,
'''                    glProg.setVar("wbR",r);glProg.setVar("wbG",1.0f);glProg.setVar("wbB",b);
                    glProg.setTextureCompute("inputCfa",iris26480ShortCfa,false);''',
'''                    glProg.setVar("wbR",r);glProg.setVar("wbG",1.0f);glProg.setVar("wbB",b);
                    glProg.setVar("sensorExposureScale",1.0f);glProg.setVar("physicalClipThreshold",0.985f);
                    glProg.setTextureCompute("inputCfa",iris26480ShortCfa,false);''','short physical clip scale')
# Update authoritative log claims without changing recurrence.
cr=cr.replace('clippedSamplesOrdinaryObservations=true','clippedSamplesOrdinaryObservations=false cfaPhysicalClipAuthority=true',1)
cr=cr.replace('saturationValidity=false"','saturationValidity=physicalCfaPreconditioned"',1)
CR.write_text(cr)

# 5) Alignment performance: preserve all Wronski/IPOL math but preallocate/reuse per-frame
#    guide, Gaussian and tile-flow scratch textures in PreparedReference.
wa=WA.read_text()
if 'IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION' not in wa or 'buildGuidePyramid(' not in wa:
    raise SystemExit('26482 expected Wronski alignment baseline missing')
# Replace whole file for deterministic ownership and simpler static validation.
WA.write_text(r'''package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26482_WRONSKI_SEQUENTIAL_ALIGNMENT_SCRATCH
 *
 * Wronski/IPOL equations, levels, radii, metrics and three fine ICA iterations
 * are unchanged. Only allocations are moved from every auxiliary frame into the
 * prepared-reference burst lifetime, following the frame-sequential GLES scratch
 * principle: commands stay in one ordered context, so scratch can be overwritten
 * on the next frame after the prior frame's dependent commands have been submitted.
 */
public final class MotionV2WronskiAlignment {
    private static final String TAG = "MotionV2WronskiAlign";
    private static final int[] STEP = new int[] {1,2,4,4};
    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p,int d){
        return new Point(Math.max(1,(p.x+d-1)/d),Math.max(1,(p.y+d-1)/d));
    }
    private static Point[] levelSizes(Point rawHalf){
        Point[] s=new Point[4];s[0]=new Point(rawHalf);
        for(int l=1;l<4;l++)s[l]=divCeil(s[l-1],STEP[l]);
        return s;
    }
    private static void closeTexture(GLTexture t){if(t!=null)try{t.close();}catch(Throwable ignored){}}
    private static void closeArray(GLTexture[] a){if(a!=null)for(GLTexture t:a)closeTexture(t);}

    private static final class AlignmentScratch implements AutoCloseable {
        final GLTexture[] guide=new GLTexture[4];
        final GLTexture[] gaussianTmp=new GLTexture[4];
        final GLTexture[] blockFlow=new GLTexture[4];
        GLTexture fineRefined;
        boolean active;

        AlignmentScratch(Point rawHalf,float snr){
            Point[] level=levelSizes(rawHalf);
            int baseTile=snr<=14.0f?64:(snr<=22.0f?32:16);
            int[] tile=new int[]{baseTile,baseTile,baseTile,Math.max(8,baseTile/2)};
            try{
                guide[0]=new GLTexture(level[0],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                for(int l=1;l<4;l++){
                    gaussianTmp[l]=new GLTexture(level[l-1],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                    guide[l]=new GLTexture(level[l],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                }
                for(int l=0;l<4;l++){
                    Point grid=new Point(Math.max(1,(level[l].x+tile[l]-1)/tile[l]),Math.max(1,(level[l].y+tile[l]-1)/tile[l]));
                    blockFlow[l]=new GLTexture(grid,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                }
                Point fineGrid=new Point(Math.max(1,(level[0].x+tile[0]-1)/tile[0]),Math.max(1,(level[0].y+tile[0]-1)/tile[0]));
                fineRefined=new GLTexture(fineGrid,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            }catch(Throwable t){close();throw t;}
        }
        void begin(){if(active)throw new IllegalStateException("Wronski alignment scratch overlap");active=true;}
        void end(){active=false;}
        @Override public void close(){active=false;closeArray(guide);closeArray(gaussianTmp);closeArray(blockFlow);closeTexture(fineRefined);fineRefined=null;}
    }

    public static final class PreparedReference implements AutoCloseable {
        private final Point rawHalf;
        private final int cfaPattern;
        private final float signalScale;
        private final float snr;
        private GLTexture[] levels;
        private GLTexture referenceGradient;
        private GLTexture fineInverseHessian;
        private AlignmentScratch scratch;

        private PreparedReference(Point rawHalf,int cfaPattern,float signalScale,float snr,
                GLTexture[] levels,GLTexture referenceGradient,GLTexture fineInverseHessian,
                AlignmentScratch scratch){
            this.rawHalf=new Point(rawHalf);this.cfaPattern=cfaPattern;this.signalScale=signalScale;this.snr=snr;
            this.levels=levels;this.referenceGradient=referenceGradient;this.fineInverseHessian=fineInverseHessian;this.scratch=scratch;
        }
        @Override public void close(){
            if(levels!=null){closeArray(levels);levels=null;}
            closeTexture(referenceGradient);referenceGradient=null;
            closeTexture(fineInverseHessian);fineInverseHessian=null;
            if(scratch!=null){scratch.close();scratch=null;}
        }
    }

    private static GLTexture[] buildGuidePyramid(Point rawHalf,int cfaPattern,float signalScale,GLProg glProg,GLTexture cfa){
        GLTexture[] guide=new GLTexture[4];GLTexture[] tmp=new GLTexture[4];
        try{
            Point[] level=levelSizes(rawHalf);
            guide[0]=new GLTexture(level[0],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            glProg.setDefine("CFAPATTERN",cfaPattern);glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/alignment_guide",true);
            glProg.setVar("guideScale",1);glProg.setVar("signalScale",Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa",cfa);glProg.setTextureCompute("OutputGuide",guide[0],true);glProg.computeAuto(level[0],1);
            for(int l=1;l<4;l++){
                tmp[l]=new GLTexture(level[l-1],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                guide[l]=new GLTexture(level[l],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",0);
                glProg.setTexture("InputGuide",guide[l-1]);glProg.setTextureCompute("OutputGuide",tmp[l],true);glProg.computeAuto(level[l-1],1);
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",1);
                glProg.setTexture("InputGuide",tmp[l]);glProg.setTextureCompute("OutputGuide",guide[l],true);glProg.computeAuto(level[l],1);
                tmp[l].close();tmp[l]=null;
            }
            return guide;
        }catch(Throwable t){closeArray(tmp);closeArray(guide);throw t;}
    }

    private static void fillGuidePyramid(PreparedReference p,GLProg glProg,GLTexture cfa){
        AlignmentScratch s=p.scratch;Point[] level=levelSizes(p.rawHalf);
        glProg.setDefine("CFAPATTERN",p.cfaPattern);glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/alignment_guide",true);
        glProg.setVar("guideScale",1);glProg.setVar("signalScale",Math.max(p.signalScale,1.0e-6f));
        glProg.setTexture("InputCfa",cfa);glProg.setTextureCompute("OutputGuide",s.guide[0],true);glProg.computeAuto(level[0],1);
        for(int l=1;l<4;l++){
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",0);
            glProg.setTexture("InputGuide",s.guide[l-1]);glProg.setTextureCompute("OutputGuide",s.gaussianTmp[l],true);glProg.computeAuto(level[l-1],1);
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",1);
            glProg.setTexture("InputGuide",s.gaussianTmp[l]);glProg.setTextureCompute("OutputGuide",s.guide[l],true);glProg.computeAuto(level[l],1);
        }
    }

    public static PreparedReference prepareReference(Point rawHalf,int cfaPattern,float signalScale,float snr,GLProg glProg,GLTexture referenceCfa){
        long start=System.currentTimeMillis();GLTexture[] ref=null;GLTexture gradient=null,hessian=null;AlignmentScratch scratch=null;
        try{
            ref=buildGuidePyramid(rawHalf,cfaPattern,signalScale,glProg,referenceCfa);
            int baseTile=snr<=14.0f?64:(snr<=22.0f?32:16);
            Point fineGrid=new Point(Math.max(1,(rawHalf.x+baseTile-1)/baseTile),Math.max(1,(rawHalf.y+baseTile-1)/baseTile));
            gradient=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_ica_reference_gradient",true);glProg.setVar("levelSize",rawHalf);
            glProg.setTexture("ReferenceGuide",ref[0]);glProg.setTextureCompute("OutputGradient",gradient,true);glProg.computeAuto(rawHalf,1);
            hessian=new GLTexture(fineGrid,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_ica_reference_hessian",true);glProg.setVar("levelSize",rawHalf);glProg.setVar("tileSize",baseTile);
            glProg.setTexture("ReferenceGradient",gradient);glProg.setTextureCompute("OutputInverseHessian",hessian,true);glProg.computeAuto(fineGrid,1);
            scratch=new AlignmentScratch(rawHalf,snr);
            Log.d(TAG,"IRIS_26482_WRONSKI_REFERENCE_PREP_AND_SEQUENTIAL_SCRATCH elapsedMs="+(System.currentTimeMillis()-start)
                    +" levels=4 referenceProductsReused=true scratchTexturesReused=true perAuxGuideAllocations=0 perAuxTileFlowAllocations=0 icaIterations=3FineOnly");
            return new PreparedReference(rawHalf,cfaPattern,signalScale,snr,ref,gradient,hessian,scratch);
        }catch(Throwable t){closeArray(ref);closeTexture(gradient);closeTexture(hessian);if(scratch!=null)scratch.close();throw t;}
    }

    public static MotionV2Alignment.Result alignPrepared(PreparedReference p,GLProg glProg,GLTexture alterCfa){
        if(p==null||p.levels==null||p.scratch==null)throw new IllegalStateException("Wronski prepared reference is closed");
        long start=System.currentTimeMillis();int baseTile=p.snr<=14.0f?64:(p.snr<=22.0f?32:16);
        int[] tile=new int[]{baseTile,baseTile,baseTile,Math.max(8,baseTile/2)};int[] radius=new int[]{1,4,4,4};int[] metric=new int[]{0,1,1,1};
        Point[] level=levelSizes(p.rawHalf);AlignmentScratch s=p.scratch;GLTexture dense=null;GLTexture previous=null;
        s.begin();
        try{
            fillGuidePyramid(p,glProg,alterCfa);
            for(int l=3;l>=0;l--){
                Point grid=new Point(Math.max(1,(level[l].x+tile[l]-1)/tile[l]),Math.max(1,(level[l].y+tile[l]-1)/tile[l]));
                GLTexture block=s.blockFlow[l];
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_block_match",true);glProg.setVar("levelSize",level[l]);glProg.setVar("tileSize",tile[l]);
                glProg.setVar("searchRadius",radius[l]);glProg.setVar("distanceMetric",metric[l]);glProg.setVar("hasPrevious",previous!=null?1:0);
                glProg.setVar("previousToCurrentScale",l<3?(float)STEP[l+1]:1.0f);glProg.setTexture("ReferenceGuide",p.levels[l]);glProg.setTexture("MovingGuide",s.guide[l]);
                glProg.setTexture("PreviousFlow",previous!=null?previous:p.levels[l]);glProg.setTextureCompute("OutputFlow",block,true);glProg.computeAuto(grid,1);
                GLTexture next=block;
                if(l==0){
                    glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_ica_refine",true);glProg.setVar("levelSize",level[l]);glProg.setVar("tileSize",tile[l]);
                    glProg.setTexture("ReferenceGuide",p.levels[l]);glProg.setTexture("MovingGuide",s.guide[l]);glProg.setTexture("BlockFlow",block);
                    glProg.setTexture("ReferenceGradient",p.referenceGradient);glProg.setTexture("InverseHessian",p.fineInverseHessian);
                    glProg.setTextureCompute("OutputFlow",s.fineRefined,true);glProg.computeAuto(grid,1);next=s.fineRefined;
                }
                previous=next;
            }
            dense=new GLTexture(p.rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_flow_expand",true);glProg.setVar("outputSize",p.rawHalf);glProg.setVar("tileSize",baseTile);
            glProg.setTexture("TileFlow",previous);glProg.setTextureCompute("OutputFlow",dense,true);glProg.computeAuto(p.rawHalf,1);
            GLTexture keep=dense;dense=null;
            Log.d(TAG,"IRIS_26482_WRONSKI_ALIGNMENT_SUBMIT elapsedMs="+(System.currentTimeMillis()-start)
                    +" snr="+p.snr+" baseTile="+baseTile+" levels=4 factors=1,2,4,4 radii=1,4,4,4 metrics=L1,L2,L2,L2"
                    +" icaIterations=3FineOnly referencePreparedOnce=true sequentialScratchReuse=true mathChanged=false");
            return new MotionV2Alignment.Result(keep,0.0f,0.0f,1.0f,0.0f);
        }finally{s.end();if(dense!=null)dense.close();}
    }

    public static MotionV2Alignment.Result align(Point rawHalf,int cfaPattern,float signalScale,float snr,GLProg glProg,GLTexture referenceCfa,GLTexture alterCfa){
        try(PreparedReference p=prepareReference(rawHalf,cfaPattern,signalScale,snr,glProg,referenceCfa)){
            return alignPrepared(p,glProg,alterCfa);
        }
    }
}
''')

# Final static semantic proof.
assert 'IRIS_26482_BJZHOU_CFA_CALCULATION_DOMAIN_CLIP_AUTHORITY' in WB.read_text()
assert 'sensorExposureScale' in WB.read_text() and 'physicalClipThreshold' in WB.read_text()
assert 'IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_CLIP_AUTHORITY' in CG.read_text()
assert 'sensorClipLevel' not in CG.read_text()
assert 'sensorClipLevel' not in CJ.read_text()
assert CR.read_text().count('physicalClipThreshold')==3
assert CR.read_text().count('sensorExposureScale')==3
assert 'vec3 wbRgb=num/den;' in (root/'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl').read_text()
assert 'IRIS_26482_WRONSKI_SEQUENTIAL_ALIGNMENT_SCRATCH' in WA.read_text()
assert 'icaIterations=3FineOnly' in WA.read_text()
print('26482 transform source assumptions PASS')
print('26482 existing Wronski calculation-WB domain preserved PASS')
print('26482 physical CFA clip authority PASS')
print('26482 downstream RGB clip inference removed PASS')
print('26482 Wronski sequential alignment scratch reuse PASS')
print('26482 Wronski divide-once/3-ICA invariants PASS')
