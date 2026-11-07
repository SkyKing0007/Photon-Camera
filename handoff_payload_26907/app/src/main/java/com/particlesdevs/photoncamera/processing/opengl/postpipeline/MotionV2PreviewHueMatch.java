package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.opengl.GLES30;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.BufferUtils;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_FRAMEBUFFER;
import static android.opengl.GLES20.GL_FRAMEBUFFER_BINDING;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26907_SHUTTER_PREVIEW_HUE_ONLY
 * B Photo SuperRes-OFF only, opt-in strictly by measured and registered shutter-preview RGB.
 * Does not change capture AE, global WB, tone, exposure, gamut authority or saturation scaling.
 * Unknown geometry, unmatched scene, poor confidence or failed GPU probe is identity.
 */
public final class MotionV2PreviewHueMatch extends Node {
    private GLTexture hueDeltaTexture;
    public MotionV2PreviewHueMatch() { super("", "MotionV2PreviewHueMatch"); }
    @Override public void Compile() {}

    public static void inspectAtExistingMatcher(Bitmap preview,GLTexture source,GLProg program,
                                                Parameters params) {
        params.motionV2PreviewHueLut26907 = null;
        if (!params.motionV2Active || params.irisNightActive || params.motionV2SuperResOutputEnabled
                || params.motionV2HighZoomRgbPrepared || preview == null || preview.isRecycled()) return;
        if (source == null || source.mSize.x <= 0 || source.mSize.y <= 0) return;
        int pw=preview.getWidth(),ph=preview.getHeight();
        if(pw<48||ph<48||pw>256||ph>256)return;
        // Preview's native orientation may differ by 90 degrees from the RAW carrier.
        boolean rawLandscape=source.mSize.x>source.mSize.y;
        boolean previewLandscape=pw>ph;
        boolean turn=rawLandscape!=previewLandscape;
        int rw=turn?ph:pw,rh=turn?pw:ph;
        int[] framebuffer=new int[1],viewport=new int[4];
        GLTexture probe=null;
        try{
            GLES30.glGetIntegerv(GL_FRAMEBUFFER_BINDING,framebuffer,0);
            GLES30.glGetIntegerv(GLES30.GL_VIEWPORT,viewport,0);
            probe=new GLTexture(new Point(rw,rh),new GLFormat(GLFormat.DataType.FLOAT_32,4),null,
                    GL_NEAREST,GL_CLAMP_TO_EDGE);
            program.useProgram("precision highp float;\n"
                    +"precision highp sampler2D;\n"
                    +"uniform sampler2D InputBuffer;\n"
                    +"uniform vec2 OutputSize;\n"
                    +"out vec4 Output;\n"
                    +"void main(){vec2 uv=(gl_FragCoord.xy-vec2(0.5))/OutputSize;"
                    +"Output=texture(InputBuffer,clamp(uv,vec2(0.0),vec2(1.0)));}\n");
            program.setTexture("InputBuffer",source);
            program.setVar("OutputSize",(float)rw,(float)rh);
            program.drawBlocks(probe);
            program.closed=true;
            probe.BufferLoad();
            ByteBuffer readback=probe.textureBuffer(new GLFormat(GLFormat.DataType.FLOAT_32,4),true);
            readback.order(ByteOrder.nativeOrder());
            FloatBuffer buffer=readback.asFloatBuffer();
            if(buffer.remaining()!=rw*rh*4)throw new IllegalStateException("26907 RGB probe byte mismatch");
            float[] raw=new float[rw*rh*4];buffer.get(raw);
            int[] display=new int[pw*ph];preview.getPixels(display,0,pw,0,0,pw,ph);
            MotionV2PreviewHueCalibration.Decision result=
                    MotionV2PreviewHueCalibration.measure(display,pw,ph,raw,rw,rh);
            if(result.valid){
                params.motionV2PreviewHueLut26907=result.deltaRad;
            }
            Log.i("Iris26907Hue","IRIS_26907_PREVIEW_HUE_MEASURE"
                    +" valid="+result.valid+" reason="+result.reason
                    +" align="+result.alignment+" orientation="+result.orientation
                    +" dx="+result.dx+" dy="+result.dy
                    +" matched="+result.correspondingPixels
                    +" hueBins="+result.supportedBins
                    +" correctionMeasured=true fixedRotation=false"
                    +" brightnessContrastExposureUnchanged=true");
        }catch(Throwable t){
            params.motionV2PreviewHueLut26907=null;
            Log.w("Iris26907Hue","IRIS_26907_PREVIEW_HUE_BYPASS reason="
                    +t.getClass().getSimpleName()+" unchanged=true");
        }finally{
            if(probe!=null)try{probe.close();}catch(Throwable ignored){}
            GLES30.glBindFramebuffer(GL_FRAMEBUFFER,framebuffer[0]);
            GLES30.glViewport(viewport[0],viewport[1],viewport[2],viewport[3]);
            program.closed=true;
        }
    }

    @Override public void AfterRun() {
        if(hueDeltaTexture!=null){hueDeltaTexture.close();hueDeltaTexture=null;}
        basePipeline.mParameters.motionV2PreviewHueLut26907=null;
    }

    @Override public void Run(){
        if(!basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)
            throw new IllegalStateException("26907 PreviewHueMatch outside B Photo");
        float[] lut=basePipeline.mParameters.motionV2PreviewHueLut26907;
        if(lut==null){
            WorkingTexture=previousNode.WorkingTexture;
            glProg.closed=true;
            return;
        }
        if(lut.length!=MotionV2PreviewHueCalibration.BINS)
            throw new IllegalStateException("26907 bad hue lookup size");
        if(hueDeltaTexture!=null)throw new IllegalStateException("26907 hue lookup double-owned");
        for(float d:lut)if(!Float.isFinite(d)||Math.abs(d)>0.47f)
            throw new IllegalStateException("26907 invalid hue lookup value");
        try{
            hueDeltaTexture=new GLTexture(new Point(lut.length,1),
                    new GLFormat(GLFormat.DataType.FLOAT_32,1),BufferUtils.getFrom(lut),
                    GL_NEAREST,GL_CLAMP_TO_EDGE);
            glProg.useAssetProgram("motionv2/preview_hue_match_26907");
            glProg.setTexture("InputBuffer",previousNode.WorkingTexture);
            glProg.setTexture("HueDeltas",hueDeltaTexture);
            WorkingTexture=basePipeline.getMain();
            glProg.drawBlocks(WorkingTexture);
            glProg.closed=true;
        }finally{
            if(hueDeltaTexture!=null){hueDeltaTexture.close();hueDeltaTexture=null;}
            basePipeline.mParameters.motionV2PreviewHueLut26907=null;
        }
        Log.i(Name,"IRIS_26907_PREVIEW_HUE_APPLIED"
                +" hueOnly=true actualPreviewMeasured=true"
                +" sdrToneUnchanged=true saturationUnchanged=true"
                +" nativeReconstructionUnchanged=true dngUnchanged=true");
    }
}
