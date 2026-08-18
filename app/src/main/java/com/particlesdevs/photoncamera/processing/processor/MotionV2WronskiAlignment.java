package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26483_BJZHOU_ONLINE_LEVELWISE_LK_ALIGNMENT
 *
 * Adapted from the current RAWmax/MGC execution architecture rather than legacy
 * Hdrx/PyramidMerging: one immutable reference pyramid, reference-only gradient /
 * Hessian products prepared once at every level, then one frame-sequential
 * coarse-to-fine LK pass per auxiliary using reusable scratch textures.
 *
 * Safety invariants remain Iris-owned: the reference geometry is authoritative;
 * no unaligned alternate is ever returned; consumers still receive a dense flow
 * texture owned by MotionV2Alignment.Result and may zero unsafe evidence later.
 */
public final class MotionV2WronskiAlignment {
    /* IRIS_26487_WRONSKI_DEFERRED_GPU_CHAIN_NO_PER_DISPATCH_FINISH */
    private static final String TAG = "MotionV2WronskiAlign";
    private static final int[] STEP = new int[] {1,2,4,4};
    // Same finest->coarsest level schedule used by current RAWmax/MGC.
    private static final int[] TILE = new int[] {32,32,16,8};
    private static final int[] ITERATIONS = new int[] {2,3,3,3};

    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p,int d){
        return new Point(Math.max(1,(p.x+d-1)/d),Math.max(1,(p.y+d-1)/d));
    }
    private static Point[] levelSizes(Point rawHalf){
        Point[] s=new Point[4];s[0]=new Point(rawHalf);
        for(int l=1;l<4;l++)s[l]=divCeil(s[l-1],STEP[l]);
        return s;
    }
    private static Point grid(Point level,int tile){
        return new Point(Math.max(1,(level.x+tile-1)/tile),Math.max(1,(level.y+tile-1)/tile));
    }
    private static void closeTexture(GLTexture t){if(t!=null)try{t.close();}catch(Throwable ignored){}}
    private static void closeArray(GLTexture[] a){if(a!=null)for(GLTexture t:a)closeTexture(t);}

    private static final class AlignmentScratch implements AutoCloseable {
        final GLTexture[] guide=new GLTexture[4];
        final GLTexture[] gaussianTmp=new GLTexture[4];
        final GLTexture[] flow=new GLTexture[4];
        final GLTexture[] selected=new GLTexture[4];
        GLTexture mergeGrid;
        boolean active;

        AlignmentScratch(Point rawHalf){
            Point[] level=levelSizes(rawHalf);
            try{
                guide[0]=new GLTexture(level[0],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                for(int l=1;l<4;l++){
                    gaussianTmp[l]=new GLTexture(level[l-1],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                    guide[l]=new GLTexture(level[l],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                }
                for(int l=0;l<4;l++){
                    flow[l]=new GLTexture(grid(level[l],TILE[l]),new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    if(l<3)selected[l]=new GLTexture(grid(level[l],TILE[l]),new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                }
                mergeGrid=new GLTexture(grid(level[0],8),new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            }catch(Throwable t){close();throw t;}
        }
        void begin(){if(active)throw new IllegalStateException("Wronski alignment scratch overlap");active=true;}
        void end(){active=false;}
        @Override public void close(){active=false;closeArray(guide);closeArray(gaussianTmp);closeArray(flow);closeArray(selected);closeTexture(mergeGrid);mergeGrid=null;}
    }

    public static final class PreparedReference implements AutoCloseable {
        private final Point rawHalf;
        private final int cfaPattern;
        private final float signalScale;
        private GLTexture[] levels;
        private GLTexture[] gradients;
        private GLTexture[] inverseHessians;
        private AlignmentScratch scratch;

        private PreparedReference(Point rawHalf,int cfaPattern,float signalScale,
                GLTexture[] levels,GLTexture[] gradients,GLTexture[] inverseHessians,
                AlignmentScratch scratch){
            this.rawHalf=new Point(rawHalf);this.cfaPattern=cfaPattern;this.signalScale=signalScale;
            this.levels=levels;this.gradients=gradients;this.inverseHessians=inverseHessians;this.scratch=scratch;
        }
        @Override public void close(){
            closeArray(levels);levels=null;closeArray(gradients);gradients=null;
            closeArray(inverseHessians);inverseHessians=null;
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
            glProg.setTexture("InputCfa",cfa);glProg.setTextureCompute("OutputGuide",guide[0],true);glProg.computeAutoDeferred(level[0],1);
            for(int l=1;l<4;l++){
                tmp[l]=new GLTexture(level[l-1],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                guide[l]=new GLTexture(level[l],new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",0);
                glProg.setTexture("InputGuide",guide[l-1]);glProg.setTextureCompute("OutputGuide",tmp[l],true);glProg.computeAutoDeferred(level[l-1],1);
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",1);
                glProg.setTexture("InputGuide",tmp[l]);glProg.setTextureCompute("OutputGuide",guide[l],true);glProg.computeAutoDeferred(level[l],1);
                tmp[l].close();tmp[l]=null;
            }
            return guide;
        }catch(Throwable t){closeArray(tmp);closeArray(guide);throw t;}
    }

    private static void fillGuidePyramid(PreparedReference p,GLProg glProg,GLTexture cfa){
        AlignmentScratch s=p.scratch;Point[] level=levelSizes(p.rawHalf);
        glProg.setDefine("CFAPATTERN",p.cfaPattern);glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/alignment_guide",true);
        glProg.setVar("guideScale",1);glProg.setVar("signalScale",Math.max(p.signalScale,1.0e-6f));
        glProg.setTexture("InputCfa",cfa);glProg.setTextureCompute("OutputGuide",s.guide[0],true);glProg.computeAutoDeferred(level[0],1);
        for(int l=1;l<4;l++){
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",0);
            glProg.setTexture("InputGuide",s.guide[l-1]);glProg.setTextureCompute("OutputGuide",s.gaussianTmp[l],true);glProg.computeAutoDeferred(level[l-1],1);
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian",true);glProg.setVar("factor",STEP[l]);glProg.setVar("direction",1);
            glProg.setTexture("InputGuide",s.gaussianTmp[l]);glProg.setTextureCompute("OutputGuide",s.guide[l],true);glProg.computeAutoDeferred(level[l],1);
        }
    }

    public static PreparedReference prepareReference(Point rawHalf,int cfaPattern,float signalScale,float snr,GLProg glProg,GLTexture referenceCfa){
        long start=System.currentTimeMillis();GLTexture[] ref=null,grad=null,hess=null;AlignmentScratch scratch=null;
        try{
            Point[] level=levelSizes(rawHalf);ref=buildGuidePyramid(rawHalf,cfaPattern,signalScale,glProg,referenceCfa);
            grad=new GLTexture[4];hess=new GLTexture[4];
            for(int l=0;l<4;l++){
                grad[l]=new GLTexture(level[l],new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_ica_reference_gradient",true);glProg.setVar("levelSize",level[l]);
                glProg.setTexture("ReferenceGuide",ref[l]);glProg.setTextureCompute("OutputGradient",grad[l],true);glProg.computeAutoDeferred(level[l],1);
                Point g=grid(level[l],TILE[l]);hess[l]=new GLTexture(g,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_ica_reference_hessian",true);glProg.setVar("levelSize",level[l]);glProg.setVar("tileSize",TILE[l]);
                glProg.setTexture("ReferenceGradient",grad[l]);glProg.setTextureCompute("OutputInverseHessian",hess[l],true);glProg.computeAutoDeferred(g,1);
            }
            scratch=new AlignmentScratch(rawHalf);
            Log.d(TAG,"IRIS_26483_REFERENCE_PRODUCTS_ALL_LEVELS elapsedMs="+(System.currentTimeMillis()-start)
                    +" levels=4 steps=1,2,4,4 tileStrides=32,32,16,8 lkIterations=2,3,3,3 referenceProductsPreparedOnce=true");
            return new PreparedReference(rawHalf,cfaPattern,signalScale,ref,grad,hess,scratch);
        }catch(Throwable t){closeArray(ref);closeArray(grad);closeArray(hess);if(scratch!=null)scratch.close();throw t;}
    }

    public static MotionV2Alignment.Result alignPrepared(PreparedReference p,GLProg glProg,GLTexture alterCfa){
        if(p==null||p.levels==null||p.scratch==null)throw new IllegalStateException("Wronski prepared reference is closed");
        long start=System.currentTimeMillis();Point[] level=levelSizes(p.rawHalf);AlignmentScratch s=p.scratch;GLTexture dense=null;GLTexture previous=null;
        s.begin();
        try{
            fillGuidePyramid(p,glProg,alterCfa);
            for(int l=3;l>=0;l--){
                Point g=grid(level[l],TILE[l]);GLTexture out=s.flow[l];GLTexture initial=previous;
                if(previous!=null){GLTexture selected=s.selected[l];glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_lk_select_candidate",true);glProg.setVar("levelSize",level[l]);glProg.setVar("coarseGridSize",grid(level[l+1],TILE[l+1]));glProg.setVar("coarseTileSize",TILE[l+1]);glProg.setVar("targetTileSize",TILE[l]);glProg.setVar("coarseToTargetScale",(float)STEP[l+1]);glProg.setTexture("ReferenceGuide",p.levels[l]);glProg.setTexture("MovingGuide",s.guide[l]);glProg.setTexture("CoarseFlow",previous);glProg.setTextureCompute("OutputFlow",selected,true);glProg.computeAutoDeferred(g,1);initial=selected;}
                glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_lk_refine_level",true);
                glProg.setVar("levelSize",level[l]);glProg.setVar("tileSize",TILE[l]);glProg.setVar("hasInitial",initial!=null?1:0);
                glProg.setVar("initialToCurrentScale",1.0f);glProg.setVar("iterations",ITERATIONS[l]);
                glProg.setTexture("ReferenceGuide",p.levels[l]);glProg.setTexture("MovingGuide",s.guide[l]);
                glProg.setTexture("InitialFlow",initial!=null?initial:p.levels[l]);glProg.setTexture("ReferenceGradient",p.gradients[l]);glProg.setTexture("InverseHessian",p.inverseHessians[l]);
                glProg.setTextureCompute("OutputFlow",out,true);glProg.computeAutoDeferred(g,1);previous=out;
            }
            Point mergeGridSize=grid(level[0],8);glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_lk_select_candidate",true);glProg.setVar("levelSize",level[0]);glProg.setVar("coarseGridSize",grid(level[0],TILE[0]));glProg.setVar("coarseTileSize",TILE[0]);glProg.setVar("targetTileSize",8);glProg.setVar("coarseToTargetScale",1.0f);glProg.setTexture("ReferenceGuide",p.levels[0]);glProg.setTexture("MovingGuide",s.guide[0]);glProg.setTexture("CoarseFlow",previous);glProg.setTextureCompute("OutputFlow",s.mergeGrid,true);glProg.computeAutoDeferred(mergeGridSize,1);previous=s.mergeGrid;
            dense=new GLTexture(p.rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
            glProg.setLayout(8,8,1);glProg.useAssetProgram("motionv2/mfsr_flow_expand",true);glProg.setVar("outputSize",p.rawHalf);glProg.setVar("tileSize",8);glProg.setVar("interpolationTolerance",1.0f/16.0f);
            glProg.setTexture("TileFlow",previous);glProg.setTextureCompute("OutputFlow",dense,true);glProg.computeAutoDeferred(p.rawHalf,1);
            GLTexture keep=dense;dense=null;
            Log.d(TAG,"IRIS_26484_BJZHOU_COMPLETE_FLOW_CHAIN elapsedMs="+(System.currentTimeMillis()-start)
                    +" levels=4 steps=1,2,4,4 tileStrides=32,32,16,8 lkIterations=2,3,3,3 blockSearchPasses=0"
                    +" referenceProductsPreparedOnce=true sequentialScratchReuse=true denseFlowFrameOwned=true");
            return new MotionV2Alignment.Result(keep,0.0f,0.0f,1.0f,0.0f);
        }finally{s.end();if(dense!=null)dense.close();}
    }

    public static MotionV2Alignment.Result align(Point rawHalf,int cfaPattern,float signalScale,float snr,GLProg glProg,GLTexture referenceCfa,GLTexture alterCfa){
        try(PreparedReference p=prepareReference(rawHalf,cfaPattern,signalScale,snr,glProg,referenceCfa)){
            return alignPrepared(p,glProg,alterCfa);
        }
    }
}
