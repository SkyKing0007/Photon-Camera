package com.particlesdevs.photoncamera.processing.opengl;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.opengl.GLUtils;
import com.particlesdevs.photoncamera.util.Log;

import androidx.annotation.NonNull;

import java.nio.Buffer;
import java.nio.ByteBuffer;
import java.util.LinkedHashMap;
import java.util.Map;

import static android.opengl.GLES31.*;
import static com.particlesdevs.photoncamera.processing.opengl.GLCoreBlockProcessing.checkEglError;
import static javax.microedition.khronos.opengles.GL11.GL_TEXTURE_2D;
import static javax.microedition.khronos.opengles.GL11.GL_TEXTURE_MAG_FILTER;
import static javax.microedition.khronos.opengles.GL11.GL_TEXTURE_MIN_FILTER;

public class GLTexture implements AutoCloseable {
    public Point mSize;
    public final int mGLFormat;
    public final int mTextureID;
    public int mBuffer;
    public boolean isBuffered = false;
    public final GLFormat mFormat;
    private static final Map<Integer, Long> liveTextureTokens = new LinkedHashMap<>();
    private static long nextTrackingToken = 1L;
    private final long mTrackingToken;
    private boolean mClosed = false;

    /* IRIS_26641_SHARED_GL_TEXTURE_OWNERSHIP
     * OpenGL texture object names and texture-unit indices are different namespaces. Track live
     * object names with a generation token; never reinterpret them as texture units or fixed array
     * slots. The generation token prevents an old wrapper from deleting a reused GL object name
     * after closeAll(), and dynamic tracking introduces no new live-texture cap. */
    private static synchronized long registerTexture(int textureId) {
        if (liveTextureTokens.containsKey(textureId)) {
            throw new IllegalStateException("Duplicate live GL texture object " + textureId);
        }
        long token = nextTrackingToken++;
        if (nextTrackingToken == 0L) nextTrackingToken = 1L;
        liveTextureTokens.put(textureId, token);
        return token;
    }

    private static synchronized boolean unregisterTexture(int textureId, long trackingToken) {
        Long current = liveTextureTokens.get(textureId);
        if (current == null || current.longValue() != trackingToken) return false;
        liveTextureTokens.remove(textureId);
        return true;
    }
    public GLTexture(GLTexture in,GLFormat format) {
        this(in.mSize,new GLFormat(format),null,in.mFormat.filter,in.mFormat.wrap,0);
    }
    public GLTexture(GLTexture in) {
        this(in.mSize,in.mFormat,null,in.mFormat.filter,in.mFormat.wrap,0);
    }
    public GLTexture(int sizeX, int sizeY, GLFormat glFormat, Buffer pixels) {
        this(new Point(sizeX, sizeY), new GLFormat(glFormat), pixels, GL_LINEAR, GL_CLAMP_TO_EDGE,0);
    }
    public GLTexture(int sizeX, int sizeY, GLFormat glFormat, Buffer pixels,int textureFilter, int textureWrapper) {
        this(new Point(sizeX, sizeY), new GLFormat(glFormat), pixels, textureFilter, textureWrapper,0);
    }
    public GLTexture(Point size, GLFormat glFormat, Buffer pixels,int textureFilter, int textureWrapper) {
        this(new Point(size), new GLFormat(glFormat), pixels, textureFilter, textureWrapper,0);
    }
    public GLTexture(Point size, GLFormat glFormat, Buffer pixels) {
        this(new Point(size), new GLFormat(glFormat), pixels, GL_LINEAR, GL_CLAMP_TO_EDGE,0);
    }
    public GLTexture(int sizeX, int sizeY, GLFormat glFormat,int level) {
        this(new Point(sizeX, sizeY), new GLFormat(glFormat), null, GL_LINEAR, GL_CLAMP_TO_EDGE,level);
    }
    public GLTexture(int sizeX, int sizeY, GLFormat glFormat) {
        this(new Point(sizeX, sizeY), new GLFormat(glFormat), null, GL_LINEAR, GL_CLAMP_TO_EDGE,0);
    }
    public GLTexture(int sizeX, int sizeY, GLFormat glFormat,int textureFilter, int textureWrapper) {
        this(new Point(sizeX, sizeY), new GLFormat(glFormat), null, textureFilter, textureWrapper,0);
    }
    public GLTexture(Point size, GLFormat glFormat,int level) {
        this(new Point(size), new GLFormat(glFormat), null, GL_LINEAR, GL_CLAMP_TO_EDGE,level);
    }
    public GLTexture(Point size, GLFormat glFormat) {
        this(new Point(size), new GLFormat(glFormat), null, glFormat.filter, glFormat.wrap,0);
    }
    public GLTexture(Point point, GLFormat glFormat, int textureFilter, int textureWrapper) {
        this(new Point(point),new GLFormat(glFormat),null,textureFilter,textureWrapper);
    }
    public GLTexture(GLImage bmp){
        this(bmp,0);
    }
    public GLTexture(GLImage bmp,int level){
        this(bmp,GL_LINEAR,GL_CLAMP_TO_EDGE,level);
    }
    public GLTexture(GLImage bmp, int textureFilter, int textureWrapper,int level) {
        this.mSize = bmp.size;
        this.mFormat = bmp.glFormat;
        this.mGLFormat = mFormat.getGLFormatInternal();
        bmp.byteBuffer.position(0);
        mFormat.filter = textureFilter;
        mFormat.wrap = textureWrapper;
        int[] TexID = new int[1];
        glGenTextures(1,TexID,0);
        Log.d("GLTexture","TexID:"+TexID[0] + " Size:"+mSize.x+"x"+mSize.y + " Format:"+mFormat.getGLFormatInternal() + " Filter:"+textureFilter + " Wrapper:"+textureWrapper);
        mTextureID = TexID[0];
        mTrackingToken = registerTexture(mTextureID);
        Log.d("GLTexture","getTexture:"+mTextureID);
        // Preserve the caller's current texture-unit binding while configuring this new object.
        int[] previousBinding = new int[1];
        glGetIntegerv(GL_TEXTURE_BINDING_2D, previousBinding, 0);
        glBindTexture(GL_TEXTURE_2D, mTextureID);
        //if(bmp.byteBuffer != null) {
            glTexStorage2D(GL_TEXTURE_2D, 1, mFormat.getGLFormatInternal(),  mSize.x, mSize.y);
            checkEglError("glTexStorage2D");
            if(bmp.byteBuffer != null) {
                glTexSubImage2D(GL_TEXTURE_2D, level, 0, 0, mSize.x, mSize.y, mFormat.getGLFormatExternal(), mFormat.getGLType(), (ByteBuffer) bmp.byteBuffer);
            }
        //}
        //else glTexImage2D(GL_TEXTURE_2D, level,mFormat.getGLFormatInternal(), mSize.x, mSize.y,0, mFormat.getGLFormatExternal(), mFormat.getGLType(), null);
        checkEglError("glTexSubImage2D");
        reSetParameters();
        checkEglError("Tex glTexParameter");
        glBindTexture(GL_TEXTURE_2D, previousBinding[0]);
        checkEglError("Tex restore binding");
    }
    public GLTexture(Point size, GLFormat glFormat, Buffer pixels, int textureFilter, int textureWrapper,int level) {
        mFormat = glFormat;
        mFormat.filter = textureFilter;
        mFormat.wrap = textureWrapper;
        this.mSize = size;
        this.mGLFormat = glFormat.getGLFormatInternal();
        int[] TexID = new int[1];
        glGenTextures(1,TexID,0);
        Log.d("GLTexture","TexID:"+TexID[0]);
        mTextureID = TexID[0];
        mTrackingToken = registerTexture(mTextureID);
        Log.d("GLTexture","getTexture:"+mTextureID);
        int[] previousBinding = new int[1];
        glGetIntegerv(GL_TEXTURE_BINDING_2D, previousBinding, 0);
        glBindTexture(GL_TEXTURE_2D, mTextureID);
        //if(pixels != null) {
            glTexStorage2D(GL_TEXTURE_2D, 1, glFormat.getGLFormatInternal(),  size.x, size.y);
            checkEglError("glTexStorage2D");
            if(pixels != null) {
            glTexSubImage2D(GL_TEXTURE_2D, level, 0, 0, size.x, size.y, glFormat.getGLFormatExternal(), glFormat.getGLType(), (ByteBuffer) pixels);
            }
         //}
        //else glTexImage2D(GL_TEXTURE_2D, level,mFormat.getGLFormatInternal(), mSize.x, mSize.y,0, mFormat.getGLFormatExternal(), mFormat.getGLType(), null);
        checkEglError("glTexSubImage2D");
        reSetParameters();
        checkEglError("Tex glTexParameter");
        glBindTexture(GL_TEXTURE_2D, previousBinding[0]);
        checkEglError("Tex restore binding");
    }

    public void loadData(Buffer pixels){
        glBindTexture(GL_TEXTURE_2D, mTextureID);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, mSize.x, mSize.y, mFormat.getGLFormatExternal(), mFormat.getGLType(), pixels);
    }
    void reSetParameters(){
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mFormat.filter);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, mFormat.filter);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, mFormat.wrap);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, mFormat.wrap);
    }
    public void Bufferize(){
        if(!isBuffered) {
            int[] frameBuffer = new int[1];
            glGenFramebuffers(1,frameBuffer,0);
            mBuffer = frameBuffer[0];
            isBuffered = true;
        }
    }

    public void BindBuffer(){
        glBindFramebuffer(GL_FRAMEBUFFER, mBuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, mTextureID, 0);
    }

    public void BufferLoad() {
        Bufferize();
        glBindFramebuffer(GL_FRAMEBUFFER, mBuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, mTextureID, 0);
        glViewport(0, 0, mSize.x, mSize.y);
        checkEglError("Tex BufferLoad");
    }

    public void bind(int slot) {
        glActiveTexture(slot);
        glBindTexture(GL_TEXTURE_2D, mTextureID);
        checkEglError("Tex " + mTextureID + " bind");
    }

    public void textureBuffer(GLFormat outputFormat,ByteBuffer output) {
        glReadPixels(0, 0, mSize.x, mSize.y, outputFormat.getGLFormatExternal(), outputFormat.getGLType(), output);
    }

    public ByteBuffer textureBuffer(GLFormat outputFormat,boolean direct) {
        ByteBuffer buffer;
        if(!direct) buffer = ByteBuffer.allocate(mSize.x * mSize.y * outputFormat.mFormat.mSize * outputFormat.mChannels);
        else buffer = ByteBuffer.allocateDirect(mSize.x * mSize.y * outputFormat.mFormat.mSize * outputFormat.mChannels);
        glReadPixels(0, 0, mSize.x, mSize.y, outputFormat.getGLFormatExternal(), outputFormat.getGLType(), buffer);
        return buffer;
    }
    public ByteBuffer textureBuffer(GLFormat outputFormat) {
        ByteBuffer buffer = ByteBuffer.allocate(mSize.x * mSize.y * outputFormat.mFormat.mSize * outputFormat.mChannels);
        glReadPixels(0, 0, mSize.x, mSize.y, outputFormat.getGLFormatExternal(), outputFormat.getGLType(), buffer);
        return buffer;
    }
    public Bitmap toBitmap(){
        ByteBuffer buffer = textureBuffer(mFormat);
        Bitmap bmp = Bitmap.createBitmap(mSize.x, mSize.y, Bitmap.Config.ARGB_8888);
        bmp.copyPixelsFromBuffer(buffer);
        return bmp;
    }
    public int getByteCount(){
        return mSize.x * mSize.y * mFormat.mFormat.mSize * mFormat.mChannels;
    }


    @Override
    public String toString() {
        return "GLTexture{" +
                "mSize=" + mSize +
                ", mGLFormat=" + mGLFormat +
                ", mTextureID=" + mTextureID +
                ", mFormat=" + mFormat +
                '}';
    }
    public static synchronized void notClosed(){
        StringBuilder str = new StringBuilder();
        for (int textureId : liveTextureTokens.keySet()) {
            str.append(textureId).append(" ");
        }
        Log.d("GLTexture","notClosed:"+str.toString());
    }

    public static synchronized void closeAll(){
        if (liveTextureTokens.isEmpty()) return;
        int[] textureIds = new int[liveTextureTokens.size()];
        int i = 0;
        for (int textureId : liveTextureTokens.keySet()) textureIds[i++] = textureId;
        glDeleteTextures(textureIds.length, textureIds, 0);
        liveTextureTokens.clear();
    }

    @Override
    public synchronized void close() {
        if (mClosed) return;
        mClosed = true;
        // Generation matching prevents an old wrapper from deleting a reused GL object name.
        if (unregisterTexture(mTextureID, mTrackingToken)) {
            glDeleteTextures(1,new int[]{mTextureID},0);
        }
        // mBuffer is a framebuffer object, not a generic buffer object.
        if(isBuffered) glDeleteFramebuffers(1,new int[]{mBuffer},0);
    }
}
