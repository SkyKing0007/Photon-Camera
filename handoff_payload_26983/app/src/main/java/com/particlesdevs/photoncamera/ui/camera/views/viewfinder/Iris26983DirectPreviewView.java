package com.particlesdevs.photoncamera.ui.camera.views.viewfinder;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Matrix;
import android.graphics.SurfaceTexture;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.AttributeSet;
import android.view.PixelCopy;
import android.view.Surface;
import android.view.TextureView;
import android.view.ViewTreeObserver;
import com.particlesdevs.photoncamera.util.Log;

/** Camera2 PRIVATE -> Android TextureView/compositor. No app GL shader, YUV conversion,
 * CPU preview reconstruction or processing EGL context. UI thread owns presentation.
 * The camera handler owns the output configuration and request targets. */
public final class Iris26983DirectPreviewView extends TextureView implements TextureView.SurfaceTextureListener {
    private static final String TAG="Iris26983DirectView";
    public interface Callback { void ready(long token,long timestamp); void failed(long token,String reason); }
    private final Handler ui=new Handler(Looper.getMainLooper());
    private final Object outputLock=new Object();
    private Surface output;
    private SurfaceTexture texture;
    private int bufferW,bufferH;
    private volatile long lastTimestamp;
    private long token,minTimestamp;
    private Callback callback;
    private GLPreview gl;
    private GLPreview.Iris26983Geometry geometry;
    private boolean probing,shown;
    public Iris26983DirectPreviewView(Context c,AttributeSet a) {
        super(c,a);setSurfaceTextureListener(this);setOpaque(true);setAlpha(0f);setClickable(false);setFocusable(false);
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();ensureOutput();}
    private void ensureOutput(){
        if(Build.VERSION.SDK_INT<29)return;
        synchronized(outputLock){
            if(output!=null&&output.isValid())return;
            try{
                SurfaceTexture st=getSurfaceTexture();
                if(st==null){st=new SurfaceTexture(false);setSurfaceTexture(st);}
                install(st);
            }catch(RuntimeException e){Log.w(TAG,"direct surface unavailable",e);}
        }
    }
    private void install(SurfaceTexture st){
        if(texture==st&&output!=null&&output.isValid())return;
        if(output!=null)output.release();
        texture=st;output=new Surface(st);
        if(bufferW>0&&bufferH>0)st.setDefaultBufferSize(bufferW,bufferH);
    }
    /** Called before Camera2 session support query; does not create/rebuild a session. */
    public Surface configuredOutput(int w,int h){
        synchronized(outputLock){
            if(Build.VERSION.SDK_INT<29||texture==null||output==null||!output.isValid()||w<=0||h<=0)return null;
            try{bufferW=w;bufferH=h;texture.setDefaultBufferSize(w,h);return output;}
            catch(RuntimeException e){return null;}
        }
    }
    public void arm(long token,long minTimestamp,GLPreview source,Callback cb){
        ui.post(()->{
            if(Build.VERSION.SDK_INT<29||!isAttachedToWindow()||!isHardwareAccelerated()||source==null||
                    source.getWidth()!=getWidth()||source.getHeight()!=getHeight()||getWidth()<=0||
                    !source.iris26983DirectDisplayEligible()) {cb.failed(token,"geometry_or_shader_not_neutral");return;}
            this.token=token;this.minTimestamp=Math.max(minTimestamp,lastTimestamp);gl=source;callback=cb;
            geometry=source.iris26983Geometry();probing=false;shown=false;
            // Keep the layer drawing during warmup without obscuring the original GL view.
            setAlpha(.001f);invalidate();
        });
    }
    public void hide(long expected){ui.post(()->{if(expected==0L||token==expected){token=0;callback=null;gl=null;geometry=null;probing=false;shown=false;setAlpha(0f);}});}
    public void cancelWarmup(long expected){ui.post(()->{if(token==expected){callback=null;probing=false;}});}
    private void fail(String reason){
        long t=token;Callback cb=callback;
        if(t==0||cb==null)return;
        if(!shown)setAlpha(0f); // if already shown, keep live until GL restore is proven
        callback=null;probing=false;
        cb.failed(t,reason);
    }
    private boolean applyGeometry(SurfaceTexture st){
        if(gl==null||geometry==null||!geometry.same(gl.iris26983Geometry()))return false;
        try{
            float[] tx=new float[16];st.getTransformMatrix(tx);
            float[] dest=Iris26983DirectGeometry.map(tx,geometry.orientation,geometry.mirror,geometry.zoom);
            if(!Iris26983DirectGeometry.covers(dest))return false;
            float w=getWidth(),h=getHeight();
            float[] source={0,0,w,0,0,h};float[] target={dest[0]*w,dest[1]*h,dest[2]*w,dest[3]*h,dest[4]*w,dest[5]*h};
            Matrix matrix=new Matrix();if(!matrix.setPolyToPoly(source,0,target,0,3))return false;
            setTransform(matrix);return true;
        }catch(RuntimeException e){return false;}
    }
    @Override public void onSurfaceTextureAvailable(SurfaceTexture st,int w,int h){synchronized(outputLock){install(st);}}
    @Override public void onSurfaceTextureSizeChanged(SurfaceTexture st,int w,int h){synchronized(outputLock){if(bufferW>0&&bufferH>0)st.setDefaultBufferSize(bufferW,bufferH);}}
    @Override public boolean onSurfaceTextureDestroyed(SurfaceTexture st){
        fail("direct_surface_destroyed");setAlpha(0f);
        synchronized(outputLock){if(texture==st){if(output!=null)output.release();output=null;texture=null;}}
        return true;
    }
    @Override public void onSurfaceTextureUpdated(SurfaceTexture st){
        final long timestamp=st.getTimestamp();lastTimestamp=timestamp;
        if(token==0||callback==null||timestamp<=minTimestamp)return;
        if(gl==null||!gl.iris26983DirectDisplayEligible()||!applyGeometry(st)){fail("direct_geometry_or_display_changed");return;}
        if(shown||probing)return;
        probing=true; final long expected=token;final int n=32;
        final Bitmap reference=Bitmap.createBitmap(n,n,Bitmap.Config.ARGB_8888);
        try{
            // Wait a UI turn for the newly applied TextureView transform before sampling it.
            postOnAnimation(()->{
                if(token!=expected||callback==null){reference.recycle();return;}
                Bitmap direct=null;
                try{direct=getBitmap(n,n);}catch(RuntimeException ignored){}
                if(direct==null){reference.recycle();fail("direct_sample_unavailable");return;}
                final Bitmap sample=direct;
                try{PixelCopy.request(gl,reference,result->{
                    try{
                        if(token!=expected||callback==null)return;
                        int[] a=new int[n*n],b=new int[n*n];
                        reference.getPixels(a,0,n,0,0,n,n);sample.getPixels(b,0,n,0,0,n,n);
                        if(result!=PixelCopy.SUCCESS||!Iris26983DirectGeometry.comparable(a,b)){
                            fail("display_geometry_or_color_unproven");return;}
                        ViewTreeObserver observer=getViewTreeObserver();
                        if(!observer.isAlive()){fail("no_frame_commit_observer");return;}
                        observer.registerFrameCommitCallback(()->{
                            if(token==expected&&callback!=null&&lastTimestamp>minTimestamp){
                                shown=true;callback.ready(expected,lastTimestamp);
                            }
                        });
                        setAlpha(1f);invalidate();
                    }catch(RuntimeException e){fail("display_verification_failed");}
                    finally{reference.recycle();sample.recycle();}
                },ui);}catch(RuntimeException e){reference.recycle();sample.recycle();fail("pixelcopy_unavailable");}
            });
        }catch(RuntimeException e){reference.recycle();fail("direct_warmup_failed");}
    }
    @Override protected void onDetachedFromWindow(){
        fail("direct_view_detached");super.onDetachedFromWindow();
        synchronized(outputLock){if(output!=null)output.release();output=null;texture=null;}
    }
}
