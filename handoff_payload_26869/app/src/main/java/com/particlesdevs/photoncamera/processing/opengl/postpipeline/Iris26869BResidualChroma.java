package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;

/** IRIS_26869_B_ONLY_TONE_AWARE_CHROMA.
 * The post-profile, post-display-exposure, pre-render input lets this stage
 * see actual presentation-domain shadow magnitude. Exactly zero is a literal
 * bypass to the successful 26868 RAWR output. No temporal noise model is
 * fabricated or borrowed from A/Camera2; structure gating is conservative.
 */
public final class Iris26869BResidualChroma extends Node {
    private final float strength;
    public Iris26869BResidualChroma(float strength) {
        super("", "Iris26869BResidualChroma");
        if(!Float.isFinite(strength)||strength<=0f||strength>1f)
            throw new IllegalArgumentException("26869 invalid B-only chroma strength");
        this.strength=strength;
    }
    @Override public void Compile() { }
    @Override public void Run() {
        if(!basePipeline.mParameters.motionV2Active ||
            basePipeline.mParameters.motionV2ReconstructionOwner !=
                Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE)
            throw new IllegalStateException("26869 residual chroma outside native B");
        glProg.useAssetProgram("motionv2/iris_26869_b_residual_chroma");
        glProg.setTexture("InputBuffer",previousNode.WorkingTexture);
        glProg.setVar("cleanupStrength",strength);
        glProg.setVar("presentationGain",Math.max(0.0001f,basePipeline.mParameters.motionV2DisplayGain)*MotionV2Render.OUTPUT_EXPOSURE_SCALE);
        WorkingTexture=basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed=true;
        Log.d(Name,"IRIS_26869_B_TONE_CHROMA strength="+strength+
            " renderer=afterExposure beforeRender lumaUntouched=true");
    }
}
