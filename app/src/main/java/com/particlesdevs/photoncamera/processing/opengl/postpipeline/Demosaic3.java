package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.FileManager;

public class Demosaic3 extends Node {
    public  Demosaic3() {
        super("", "Demosaic");
    }

    @Override
    public void Compile() {}
    
    @Tunable(title = "Grad Size", category = "Demosaic", max = 5.0f, defaultValue = 1.5f)
    float gradSize = 1.5f;
    
    @Tunable(title = "Fuse Min", category = "Demosaic", max = 1.0f, defaultValue = 0.0f)
    float fuseMin = 0.f;
    
    @Tunable(title = "Fuse Max", category = "Demosaic", max = 2.0f, defaultValue = 1.0f)
    float fuseMax = 1.f;
    
    @Tunable(title = "Fuse Shift", category = "Demosaic", min = -2.0f, max = 2.0f, defaultValue = -0.5f)
    float fuseShift = -0.5f;
    
    @Tunable(title = "Fuse Multiply", category = "Demosaic", max = 20.0f, defaultValue = 6.0f)
    float fuseMpy = 6.0f;
    
    @Tunable(title = "Green Min", category = "Demosaic", max = 0.001f, defaultValue = 0.00000001f, step = 0.00000001f)
    float greenMin = 1e-8f;
    
    @Tunable(title = "Green Max", category = "Demosaic", max = 2.0f, defaultValue = 1.0f)
    float greenMax = 1.0f;
    
    @Override
    public void Run() {
        // Values are automatically injected in BeforeRun()!
        /*
         * IRIS_26405_MAIN_MOTION_IQ_LAB
         * Important audit result: legacy Grad/Fuse Java fields are orphaned
         * in active Demosaic3. Main menu therefore controls the constants that
         * are actually used by p0ig/p12ec/p12fc/p2ed2.
         */
        /*
         * IRIS_26409_MOTION_V2_CLEAN_DEMOSAIC_BASELINE
         * V2 starts from the fixed Demosaic3 defaults. Do not let current
         * Motion IQ-Lab experiments compensate for upstream RAW geometry.
         */
        boolean iris26405DemosaicLab =
                !basePipeline.mParameters.motionV2Active
                        && com.particlesdevs.photoncamera.settings.MotionIqLab.active();
        float iris26405GradientAlpha =
                iris26405DemosaicLab
                        ? com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                "demosaic_gradient_alpha", 3.75f)
                        : 3.75f;
        float iris26405GreenEdgeThreshold =
                iris26405DemosaicLab
                        ? com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                "demosaic_green_edge_threshold", 1.30f)
                        : 1.30f;
        float iris26405GreenRefineThreshold =
                iris26405DemosaicLab
                        ? com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                "demosaic_green_refine_threshold", 1.30f)
                        : 1.30f;
        float iris26405FinalAlpha =
                iris26405DemosaicLab
                        ? com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                "demosaic_final_alpha", 3.75f)
                        : 3.75f;
        float iris26405FinalThreshold =
                iris26405DemosaicLab
                        ? com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                "demosaic_final_threshold", 1.90f)
                        : 1.90f;
        float iris26405FinalBeta =
                iris26405DemosaicLab
                        ? com.particlesdevs.photoncamera.settings.MotionIqLab.getFloat(
                                "demosaic_final_beta", 0.42f)
                        : 0.42f;


        GLTexture glTexture;
        glTexture = previousNode.WorkingTexture;
        //Gradients
        GLTexture outp;
        int tile = 8;
        startT();
        /*
         * IRIS_26389_DEMOSAIC_IG_PING_PONG
         * Keep the IG/gradient guide in an independent texture so the final
         * RGB pass never reads and writes basePipeline.main3 simultaneously.
         */
        GLTexture iris26389IgGuide =
                new GLTexture(basePipeline.main3.mSize,
                        basePipeline.main3.mFormat,
                        null);
        WorkingTexture = iris26389IgGuide;
        glProg.setLayout(tile,tile,1);
        glProg.setDefine("IRIS_LAB_GRADIENT_ALPHA", iris26405GradientAlpha);
        glProg.useAssetProgram("demosaic/demosaicp0ig",true);
        glProg.setTextureCompute("inTexture", glTexture,false);
        glProg.setTextureCompute("outTexture", WorkingTexture,true);
        glProg.computeManual(WorkingTexture.mSize.x/tile,WorkingTexture.mSize.y/tile,1);
        endT("demosaicp0ig");

        //Colour channels
        startT();
        outp = basePipeline.getMain();
        glProg.setLayout(tile,tile,1);
        glProg.setDefine("IRIS_LAB_GREEN_EDGE_THRESHOLD", iris26405GreenEdgeThreshold);
        glProg.useAssetProgram("demosaic/demosaicp12ec",true);
        glProg.setTextureCompute("inTexture",glTexture, false);
        glProg.setTextureCompute("igTexture",iris26389IgGuide, false);
        glProg.setTextureCompute("outTexture",outp, true);
        glProg.computeManual(WorkingTexture.mSize.x/tile,WorkingTexture.mSize.y/tile,1);
        endT("demosaicp12ec");

        startT();
        glProg.setLayout(tile,tile,1);
        glProg.setDefine("IRIS_LAB_GREEN_REFINE_THRESHOLD", iris26405GreenRefineThreshold);
        glProg.useAssetProgram("demosaic/demosaicp12fc",true);
        glProg.setTextureCompute("inTexture",glTexture, false);
        glProg.setTextureCompute("igTexture",iris26389IgGuide, false);
        /*
         * IRIS_26389_DEMOSAIC_GREEN_PING_PONG
         * demosaicp12fc must not read and write the same image.
         */
        GLTexture iris26389RefinedGreen =
                new GLTexture(outp.mSize, outp.mFormat, null);
        glProg.setTextureCompute("greenTexture",outp, false);
        glProg.setTextureCompute("outTexture",iris26389RefinedGreen, true);
        glProg.computeManual(
                iris26389RefinedGreen.mSize.x/tile,
                iris26389RefinedGreen.mSize.y/tile,
                1);
        endT("demosaicp12fc");
        //glProg.drawBlocks(WorkingTexture);

        startT();
        WorkingTexture = basePipeline.main3;
        glProg.setDefine("greenmin",greenMin);
        glProg.setDefine("greenmax",greenMax);
        glProg.setLayout(tile,tile,1);
        //glProg.useFileProgram(FileManager.sPHOTON_TUNING_DIR + "demosaicp2ec.glsl",true);
        glProg.setDefine("IRIS_LAB_FINAL_ALPHA", iris26405FinalAlpha);
        glProg.setDefine("IRIS_LAB_FINAL_THRESHOLD", iris26405FinalThreshold);
        glProg.setDefine("IRIS_LAB_FINAL_BETA", iris26405FinalBeta);
        glProg.useAssetProgram("demosaic/demosaicp2ed2",true);
        glProg.setTextureCompute("inTexture", glTexture,false);
        glProg.setTextureCompute("greenTexture", iris26389RefinedGreen,false);
        glProg.setTextureCompute("igTexture", iris26389IgGuide,false);
        glProg.setTextureCompute("outTexture", WorkingTexture,true);
        glProg.setVar("neutral", basePipeline.mParameters.whitePoint[0], basePipeline.mParameters.whitePoint[1], basePipeline.mParameters.whitePoint[1], basePipeline.mParameters.whitePoint[2]);
        //glProg.setVar("neutral", 1.f, 1.f, 1.f, 1.f);
        glProg.computeManual(WorkingTexture.mSize.x/tile,WorkingTexture.mSize.y/tile,1);
        glProg.close();

        iris26389RefinedGreen.close();
        iris26389IgGuide.close();

        endT("demosaicp2ec");
        WorkingTexture = basePipeline.swap3();
    }
}
