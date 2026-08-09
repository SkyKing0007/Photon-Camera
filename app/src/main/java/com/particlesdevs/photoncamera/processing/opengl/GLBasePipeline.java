package com.particlesdevs.photoncamera.processing.opengl;

import android.graphics.Point;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.api.Settings;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.render.Parameters;

import java.io.File;
import java.io.FileInputStream;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Properties;

import static android.opengl.GLES20.GL_FRAMEBUFFER;
import static android.opengl.GLES20.GL_FRAMEBUFFER_BINDING;
import static android.opengl.GLES20.glBindFramebuffer;
import static android.opengl.GLES20.glGetIntegerv;
import static com.particlesdevs.photoncamera.processing.opengl.GLCoreBlockProcessing.checkEglError;
import static com.particlesdevs.photoncamera.util.FileManager.sPHOTON_TUNING_DIR;

public class GLBasePipeline implements AutoCloseable {
    public final ArrayList<Node> Nodes = new ArrayList<>();
    public GLInterface glint = null;
    private long timeStart;
    private static final String TAG = "BasePipeline";
    private final int[] bind = new int[1];
    public GLTexture main1,main2,main3,main4, main5;
    public Settings mSettings;
    public Parameters mParameters;
    public Properties mProp;
    private final boolean loggedTuning = false;
    private final String Name;
    public Point workSize;
    public float noiseS;
    public float noiseO;
    private String currentProg;

    public int texnum = 0;

    public GLBasePipeline(String name){
        Name = name;
        Properties properties = new Properties();
        try {
            File init = new File(sPHOTON_TUNING_DIR, "PhotonCameraTuning.ini");
            if(!init.exists()) {
                init.createNewFile();
                /*InputStream inputStream = PhotonCamera.getAssetLoader().getInputStream("tuning/PhotonCameraTuning.ini");
                byte[] buffer = new byte[inputStream.available()];
                inputStream.read(buffer);
                OutputStream outputStream = new FileOutputStream(init);
                outputStream.write(buffer);
                outputStream.close();*/
            }
            properties.load(new FileInputStream(init));
        } catch (Exception e) {
            Log.e("PostPipeline","Error at loading properties");
            e.printStackTrace();
        }
        mProp = properties;
    }
    public GLTexture getMain(){
        if(texnum == 1) {
            texnum = 2;
            return main2;
        } else {
            texnum = 1;
            return main1;
        }
    }

    // Swaps main3 with main1 and main2
    public GLTexture swap3() {
        if(texnum == 1) {
            GLTexture temp = main1;
            main1 = main3;
            main3 = temp;
            return main1;
        } else {
            GLTexture temp = main2;
            main2 = main3;
            main3 = temp;
            return main2;
        }
    }

    private void tuningLog(String name, String value){
        if(loggedTuning) Log.d("Tuning",name+" = "+ value);
    }
    public boolean getTuning(String name, boolean Default){
        tuningLog(Name+"_"+name,String.valueOf(Default));
        return Boolean.parseBoolean(mProp.getProperty(Name+"_"+name,String.valueOf(Default)));
    }
    public float getTuning(String name,float Default){
        tuningLog(Name+"_"+name,String.valueOf(Default));
        return Float.parseFloat(mProp.getProperty(Name+"_"+name,String.valueOf(Default)));
    }
    public float[] getTuning(String name,float[] Default){
        String ins = Arrays.toString(Default).replace("[","").replace("]","");
        tuningLog(Name+"_"+name,ins);
        String inp = mProp.getProperty(Name+"_"+name, ins);
        String[] divided = inp.split(",");
        float[] output = new float[Default.length];
        for(int i = 0; i<divided.length;i++){
            output[i] = Float.parseFloat(divided[i]);
        }
        return output;
    }
    public double getTuning(String name,double Default){
        tuningLog(Name+"_"+name,String.valueOf(Default));
        return Double.parseDouble(mProp.getProperty(Name+"_"+name,String.valueOf(Default)));
    }
    public short getTuning(String name,short Default){
        tuningLog(Name+"_"+name,String.valueOf(Default));
        return Short.parseShort(mProp.getProperty(Name+"_"+name,String.valueOf(Default)));
    }
    public int getTuning(String name,int Default){
        tuningLog(Name+"_"+name,String.valueOf(Default));
        return Integer.parseInt(mProp.getProperty(Name+"_"+name,String.valueOf(Default)));
    }

    public void startTimeMeasure() {
        timeStart = System.currentTimeMillis();
    }

    public void endTimeMeasure(String Name) {
        Log.d("Pipeline", "Node:" + Name + " elapsed:" + (System.currentTimeMillis() - timeStart) + " ms");
    }

    public void add(Node in) {
        if (Nodes.size() != 0) in.previousNode = Nodes.get(Nodes.size() - 1);
        in.basePipeline = this;
        in.glInt = glint;
        in.glUtils = glint.glUtils;
        in.glProg = glint.glProgram;
        Nodes.add(in);
    }

    private void lastI() {
        glGetIntegerv(GL_FRAMEBUFFER_BINDING, bind, 0);
        checkEglError("glGetIntegerv");
    }

    private void lastR() {
        glBindFramebuffer(GL_FRAMEBUFFER, bind[0]);
        checkEglError("glBindFramebuffer");
    }

    /* IRIS_26387_WHITE_STAGE_DIAGNOSTIC */
    private void iris26387LogTextureStats(String stage, GLTexture source) {
        if (source == null || glint == null || glint.glProgram == null) return;
        int[] oldFramebuffer = new int[1];
        GLTexture probe = null;
        try {
            android.opengl.GLES30.glGetIntegerv(android.opengl.GLES30.GL_FRAMEBUFFER_BINDING, oldFramebuffer, 0);
            android.graphics.Point ps = new android.graphics.Point(32, 24);
            probe = new GLTexture(ps, new GLFormat(GLFormat.DataType.FLOAT_32, 4), null,
                    android.opengl.GLES20.GL_NEAREST, android.opengl.GLES20.GL_CLAMP_TO_EDGE);
            glint.glProgram.useProgram(
                    "precision highp float;\n"
                    + "uniform sampler2D InputBuffer;\n"
                    + "uniform vec2 OutputSize;\n"
                    + "out vec4 Output;\n"
                    + "void main(){ vec2 uv=(gl_FragCoord.xy-vec2(0.5))/OutputSize; Output=texture(InputBuffer,uv); }\n");
            glint.glProgram.setTexture("InputBuffer", source);
            glint.glProgram.setVar("OutputSize", (float)ps.x, (float)ps.y);
            glint.glProgram.drawBlocks(probe);
            glint.glProgram.closed = true;
            probe.BufferLoad();
            java.nio.ByteBuffer bytes = probe.textureBuffer(new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
            bytes.order(java.nio.ByteOrder.nativeOrder());
            java.nio.FloatBuffer fb = bytes.asFloatBuffer();
            java.util.ArrayList<Float> values = new java.util.ArrayList<>();
            double sum = 0.0;
            float min = Float.POSITIVE_INFINITY;
            float max = Float.NEGATIVE_INFINITY;
            int nonFinite = 0;
            while (fb.remaining() >= 4) {
                float v = (fb.get() + fb.get() + fb.get() + fb.get()) * 0.25f;
                if (Float.isFinite(v)) {
                    values.add(v); sum += v; min = Math.min(min,v); max = Math.max(max,v);
                } else nonFinite++;
            }
            if (values.isEmpty()) {
                Log.d("IRIS26387", "IRIS_26387_STAGE_STATS stage=" + stage + " finite=0 nonFinite=" + nonFinite);
                return;
            }
            java.util.Collections.sort(values);
            int n = values.size();
            float p01 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.01f))));
            float p10 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.10f))));
            float p50 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.50f))));
            float p90 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.90f))));
            float p99 = values.get(Math.min(n-1, Math.max(0, Math.round((n-1)*0.99f))));
            String line = "IRIS_26387_STAGE_STATS stage=" + stage + " samples=" + n
                    + " nonFinite=" + nonFinite + " min=" + min + " mean=" + (sum/n)
                    + " max=" + max + " p01=" + p01 + " p10=" + p10
                    + " p50=" + p50 + " p90=" + p90 + " p99=" + p99
                    + " format=" + source.mFormat + " size=" + source.mSize.x + "x" + source.mSize.y;
            Log.d("IRIS26387", line);
            try { com.particlesdevs.photoncamera.util.MotionTrace.processingState("WHITE_STAGE_26387", line); }
            catch (Throwable ignored) {}
        } catch (Throwable t) {
            Log.e("IRIS26387", "IRIS_26387_STAGE_STATS stage=" + stage + " error=" + t.getClass().getSimpleName());
        } finally {
            if (probe != null) try { probe.close(); } catch (Throwable ignored) {}
            android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, oldFramebuffer[0]);
        }
    }

    public GLImage runAll() {
        lastI();
        for (int i = 0; i < Nodes.size(); i++) {
            prepareNode(Nodes.get(i),i);
            startTimeMeasure();
            Nodes.get(i).Run();
            endTimeMeasure(Nodes.get(i).Name);
            if (i != Nodes.size() - 1) {
                drawProgramTexture(Nodes.get(i));
            }
            if (mParameters != null
                    && com.particlesdevs.photoncamera.app.PhotonCamera
                            .getSettings().selectedMode
                            == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {
                String iris26387Stage = Nodes.get(i).getClass().getSimpleName();
                if ("Bayer2Float".equals(iris26387Stage)
                        || "ExposureFusionBayer2".equals(iris26387Stage)
                        || "Demosaic3".equals(iris26387Stage)
                        || "ESD3D2".equals(iris26387Stage)
                        || "ABLC".equals(iris26387Stage)
                        || "Initial".equals(iris26387Stage)) {
                    iris26387LogTextureStats(iris26387Stage, Nodes.get(i).WorkingTexture);
                }
            }
            Nodes.get(i).AfterRun();
        }
        if(texnum == 1){
            if (main2 != null) main2.close();
        }else {
            if (main1 != null) main1.close();
        }
        glint.glProcessing.drawBlocksToOutput();
        if(texnum == 1){
            if (main1 != null) main1.close();
        }else {
            if (main2 != null) main2.close();
        }
        if (main3 != null) main3.close();
        glint.glProgram.close();
        Nodes.clear();
        return glint.glProcessing.mOut;
    }

    public ByteBuffer runAllRaw() {
        lastI();
        for (int i = 0; i < Nodes.size(); i++) {
            prepareNode(Nodes.get(i),i);
            startTimeMeasure();
            Nodes.get(i).Run();
            if (i != Nodes.size() - 1) {
                Log.d(TAG, "i:" + i + " size:" + Nodes.size());
                drawProgramTexture(Nodes.get(i));
            }
            Nodes.get(i).AfterRun();
            endTimeMeasure(Nodes.get(i).Name);
        }
        glint.glProgram.drawBlocks(Nodes.get(Nodes.size() - 1).GetProgTex());
        if(texnum == 1){
            if (main2 != null) main2.close();
        }else {
            if (main1 != null) main1.close();
        }
        glint.glProcessing.drawBlocksToOutput();
        if(texnum == 1){
            if (main1 != null) main1.close();
        }else {
            if (main2 != null) main2.close();
        }
        if (main3 != null) main3.close();
        glint.glProgram.close();
        Nodes.clear();
        return glint.glProcessing.mOutBuffer;
    }

    private void drawProgramTexture(Node node) {
        if(!glint.glProgram.closed) {
            glint.glProgram.drawBlocks(node.GetProgTex());
            glint.glProgram.closed = true;
        }
    }

    private void prepareNode(Node node, int index) {
        node.mProp = mProp;
        node.BeforeCompile();
        node.Compile();
        node.BeforeRun();
        if (index == Nodes.size() - 1) {
            lastR();
        }
    }

    @Override
    public void close() {
        if(glint != null) {
            if (glint.glProcessing != null) glint.glProcessing.close();
            if (glint.glContext != null) glint.glContext.close();
            if (glint.glProgram != null) glint.glProgram.close();
        }
        GLTexture.notClosed();
    }
}
