package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;

/**
 * IRIS_26907_HUE_REFERENCE_METER
 * Pure deterministic CPU-only low-resolution correspondence and hue residual estimator.
 * No fixed hue correction, scene-name classification or exposure/contrast/saturation writes.
 * Its input must be a complete shutter-time preview copy and a camera-aligned, linear Display-P3
 * RGB sample of the identical candidate. Uncertain registration returns the identity lookup.
 */
public final class MotionV2PreviewHueCalibration {
    public static final int BINS = 48;
    public static final int NO_OFFSET = 0;
    private static final float PI = (float)Math.PI;
    private static final float TWO_PI = 2.0f * PI;
    private static final float MAX_HUE_CHANGE = 0.32f; // Bounded measured residual (~18 degrees), never a fixed hue adjustment.
    private MotionV2PreviewHueCalibration() {}

    public static final class Decision {
        public final float[] deltaRad;
        public final boolean valid;
        public final String reason;
        public final int correspondingPixels;
        public final int supportedBins;
        public final int orientation;
        public final int dx, dy;
        public final float alignment;
        Decision(float[] delta, boolean valid, String reason, int pixels, int bins, int orientation,
                 int dx, int dy, float correlation) {
            this.deltaRad=delta; this.valid=valid; this.reason=reason;
            this.correspondingPixels=pixels; this.supportedBins=bins;
            this.orientation=orientation; this.dx=dx; this.dy=dy; this.alignment=correlation;
        }
    }

    private static Decision neutral(String reason, float alignment) {
        return new Decision(new float[BINS],false,reason,0,0,-1,0,0,alignment);
    }

    private static final class Lab {
        float L, a, b, chroma, hue;
        Lab(float l, float x, float y) {
            L=l; a=x; b=y;
            chroma=(float)Math.hypot(x,y);
            hue=(float)Math.atan2(y,x);
        }
    }

    private static Lab oklab(float r, float g, float b) {
        float l=(float)Math.cbrt(Math.max(0,0.4122214708f*r + 0.5363325363f*g + 0.0514459929f*b));
        float m=(float)Math.cbrt(Math.max(0,0.2119034982f*r + 0.6806995451f*g + 0.1073969566f*b));
        float s=(float)Math.cbrt(Math.max(0,0.0883024619f*r + 0.2817188376f*g + 0.6299787005f*b));
        return new Lab(0.2104542553f*l + 0.7936177850f*m - 0.0040720468f*s,
                       1.9779984951f*l - 2.4285922050f*m + 0.4505937099f*s,
                       0.0259040371f*l + 0.7827717662f*m - 0.8086757660f*s);
    }

    private static float decode(float v) {
        return v <= 0.04045f ? v/12.92f : (float)Math.pow((v+0.055f)/1.055f,2.4);
    }
    private static float wrap(float d) {
        while(d>PI)d-=TWO_PI;
        while(d< -PI)d+=TWO_PI;
        return d;
    }
    private static float clamp(float v,float a,float b) { return Math.max(a,Math.min(b,v)); }
    private static float smooth(float a,float b,float x) {
        float u=clamp((x-a)/(b-a),0,1);
        return u*u*(3-2*u);
    }

    // Eight exact rectangle-preserving orthogonal orientations. Geometry is validated per call.
    private static int index(int orientation,int x,int y,int w,int h,int pw,int ph) {
        if(x<0||x>=pw||y<0||y>=ph)return -1;
        int sx,sy;
        switch(orientation){
            case 0:sx=x;sy=y;break;
            case 1:sx=w-1-x;sy=y;break;
            case 2:sx=x;sy=h-1-y;break;
            case 3:sx=w-1-x;sy=h-1-y;break;
            case 4:sx=y;sy=h-1-x;break;
            case 5:sx=w-1-y;sy=x;break;
            case 6:sx=y;sy=x;break;
            case 7:sx=w-1-y;sy=h-1-x;break;
            default:return -1;
        }
        return sx<0||sy<0||sx>=w||sy>=h?-1:sy*w+sx;
    }

    private static float registration(float[] preview,float[] candidate,int orientation,
                                      int dx,int dy,int w,int h,int pw,int ph) {
        double dot=0,aa=0,bb=0;
        final int side=Math.max(10,pw/12), top=Math.max(12,ph/12);
        for(int y=top;y<ph-top;y+=4)for(int x=side;x<pw-side;x+=4){
            int mx=x+dx,my=y+dy;
            int left=index(orientation,mx-1,my,w,h,pw,ph);
            int right=index(orientation,mx+1,my,w,h,pw,ph);
            int up=index(orientation,mx,my-1,w,h,pw,ph);
            int down=index(orientation,mx,my+1,w,h,pw,ph);
            if(left<0||right<0||up<0||down<0)continue;
            float ax=preview[y*pw+x+1]-preview[y*pw+x-1];
            float ay=preview[(y+1)*pw+x]-preview[(y-1)*pw+x];
            float bx=candidate[right]-candidate[left],by=candidate[down]-candidate[up];
            dot+=ax*bx+ay*by;aa+=ax*ax+ay*ay;bb+=bx*bx+by*by;
        }
        return aa>1.e-7&&bb>1.e-7?(float)(dot/Math.sqrt(aa*bb)):-1;
    }

    /**
     * @param previewArgb Bitmap.getPixels() row-major TOP-first, shutter-time preview.
     * @param cameraP3Rgba GL RGBA32F textureBuffer row-major BOTTOM-first, unexposed linear P3.
     * @param rawWidth raw probe image width (normally 256 for 192x256 preview).
     * @param rawHeight raw probe image height (normally 192 for 192x256 preview).
     */
    public static Decision measure(int[] previewArgb,int previewW,int previewH,
                                   float[] cameraP3Rgba,int rawWidth,int rawHeight) {
        if(previewArgb==null||cameraP3Rgba==null||previewW<48||previewH<48
                ||previewW>256||previewH>256||rawWidth<48||rawHeight<48
                ||previewArgb.length!=previewW*previewH
                ||cameraP3Rgba.length!=rawWidth*rawHeight*4)
            return neutral("invalid_buffer_geometry",-1);
        if(!((rawWidth==previewW&&rawHeight==previewH)
                ||(rawWidth==previewH&&rawHeight==previewW)))
            return neutral("nonmatching_geometry",-1);
        final int np=previewW*previewH,nr=rawWidth*rawHeight;
        float[] pl=new float[np],cl=new float[nr];
        Lab[] pLab=new Lab[np],cLab=new Lab[nr];
        for(int i=0;i<np;i++){
            int c=previewArgb[i];
            float r=((c>>>16)&255)/255f,g=((c>>>8)&255)/255f,b=(c&255)/255f;
            pl[i]=0.2126f*r+0.7152f*g+0.0722f*b;
            pLab[i]=oklab(decode(r),decode(g),decode(b));
        }
        for(int i=0;i<nr;i++){
            float r=cameraP3Rgba[i*4],g=cameraP3Rgba[i*4+1],b=cameraP3Rgba[i*4+2];
            if(!Float.isFinite(r)||!Float.isFinite(g)||!Float.isFinite(b))return neutral("nonfinite_source",-1);
            // Display P3 D65 -> linear sRGB D65 (shared reference for both previews).
            float sr=1.22494018f*r-0.22494018f*g;
            float sg=-0.04205695f*r+1.04205695f*g;
            float sb=-0.01963755f*r-0.07863605f*g+1.0982736f*b;
            // Display-P3 legitimately extends beyond sRGB (e.g. deep orange). Negative
            // converted sRGB CHANNELS do not invalidate a physically positive P3 color:
            // the OKLab LMS cone response remains positive for these real gamut colors.
            Lab v=oklab(sr,sg,sb);
            cLab[i]=v;
            cl[i]=clamp((float)Math.pow(clamp(v.L,0,1),1.8),0,1);
        }
        int start=(rawWidth==previewW&&rawHeight==previewH)?0:4;
        int end=start+4;
        float best=-1,second=-1;
        int bestO=-1,bestDx=0,bestDy=0;
        for(int o=start;o<end;o++){
            float local=-1;
            int localDx=0,localDy=0;
            for(int dy=-8;dy<=8;dy+=4)for(int dx=-8;dx<=8;dx+=4){
                float sc=registration(pl,cl,o,dx,dy,rawWidth,rawHeight,previewW,previewH);
                if(sc>local){local=sc;localDx=dx;localDy=dy;}
            }
            for(int dy=localDy-3;dy<=localDy+3;dy++)for(int dx=localDx-3;dx<=localDx+3;dx++){
                float sc=registration(pl,cl,o,dx,dy,rawWidth,rawHeight,previewW,previewH);
                if(sc>local){local=sc;localDx=dx;localDy=dy;}
            }
            if(local>best){second=best;best=local;bestO=o;bestDx=localDx;bestDy=localDy;}
            else if(local>second)second=local;
        }
        if(best<0.50f||best-second<0.07f)return neutral("registration_uncertain",best);

        @SuppressWarnings("unchecked") ArrayList<Float>[] bins=(ArrayList<Float>[])new ArrayList[BINS];
        for(int k=0;k<BINS;k++)bins[k]=new ArrayList<>();
        int matched=0;
        for(int y=16;y<previewH-16;y+=1)for(int x=16;x<previewW-16;x+=1){
            int cx=x+bestDx,cy=y+bestDy;
            int source=index(bestO,cx,cy,rawWidth,rawHeight,previewW,previewH);
            int sourceL=index(bestO,cx-2,cy,rawWidth,rawHeight,previewW,previewH);
            int sourceR=index(bestO,cx+2,cy,rawWidth,rawHeight,previewW,previewH);
            int sourceU=index(bestO,cx,cy-2,rawWidth,rawHeight,previewW,previewH);
            int sourceD=index(bestO,cx,cy+2,rawWidth,rawHeight,previewW,previewH);
            if(source<0||sourceL<0||sourceR<0||sourceU<0||sourceD<0)continue;
            int pos=y*previewW+x;
            Lab a=pLab[pos],b=cLab[source];
            if(a.chroma<0.045f||b.chroma<0.045f||a.L<0.16f||a.L>0.94f
                    ||b.L<0.10f||b.L>0.95f||Math.abs(a.L-b.L)>0.42f)continue;
            if(Math.abs(wrap(pLab[pos-2].hue-a.hue))>0.17f
                    ||Math.abs(wrap(pLab[pos+2].hue-a.hue))>0.17f
                    ||Math.abs(wrap(pLab[pos-2*previewW].hue-a.hue))>0.17f
                    ||Math.abs(wrap(pLab[pos+2*previewW].hue-a.hue))>0.17f
                    ||Math.abs(wrap(cLab[sourceL].hue-b.hue))>0.17f
                    ||Math.abs(wrap(cLab[sourceR].hue-b.hue))>0.17f
                    ||Math.abs(wrap(cLab[sourceU].hue-b.hue))>0.17f
                    ||Math.abs(wrap(cLab[sourceD].hue-b.hue))>0.22f)continue;
            float delta=wrap(a.hue-b.hue);
            if(Math.abs(delta)>0.75f)continue;  // Do not infer correspondence from unrelated objects.
            float hue=b.hue<0?b.hue+TWO_PI:b.hue;
            int bin=Math.min(BINS-1,(int)(hue*BINS/TWO_PI));
            bins[bin].add(delta);
            matched++;
        }
        if(matched<150)return new Decision(new float[BINS],false,"insufficient_consistent_color_pairs",matched,0,bestO,bestDx,bestDy,best);
        float[] median=new float[BINS],weight=new float[BINS];
        int supported=0;
        // A sparse global hue table must NEVER propagate a supported color's shift
        // through an unrelated material or an unmeasured part of the hue circle.
        // Evidence is owned by each measured circular sector, with only a narrow
        // adjacent-sector feather for continuity at the red/violet wrap boundary.
        for(int j=0;j<BINS;j++){
            ArrayList<Float> list=bins[j];
            if(list.size()<48)continue;
            Collections.sort(list);
            float med=list.get(list.size()/2);
            float[] dev=new float[list.size()];
            for(int k=0;k<dev.length;k++)dev[k]=Math.abs(wrap(list.get(k)-med));
            Arrays.sort(dev);
            float mad=dev[dev.length/2];
            if(mad>=0.14f)continue;
            median[j]=clamp(med,-MAX_HUE_CHANGE,MAX_HUE_CHANGE);
            weight[j]=smooth(48,192,list.size())*(1-smooth(0.04f,0.14f,mad));
            if(weight[j]>=0.06f)supported++;
        }
        if(supported<2)return neutral("insufficient_supported_hues",best);
        float[] deltas=new float[BINS];
        int nonzero=0;
        for(int j=0;j<BINS;j++){
            float total=0,wsum=0;
            // Circular, compact-support reconstruction. Unmeasured sectors more
            // than one sector away stay at identity instead of acquiring a guess.
            for(int off=-1;off<=1;off++){
                int k=(j+off+BINS)%BINS;
                if(weight[k]<0.06f)continue;
                // Direct measurements take precedence. Do not mix contradictory
                // neighboring residuals and smear real yellow/orange boundaries.
                if(weight[j]>=0.06f && off!=0
                        && Math.abs(wrap(median[k]-median[j]))>0.14f)continue;
                float w=weight[k]*(off==0?1.0f:0.25f);
                total+=w*median[k];wsum+=w;
            }
            if(wsum<0.06f)continue;
            float estimated=clamp(total/wsum,-MAX_HUE_CHANGE,MAX_HUE_CHANGE);
            float confidence=clamp(wsum/1.30f,0.0f,1.0f);
            float significance=smooth(0.015f,0.065f,Math.abs(estimated));
            deltas[j]=estimated*confidence*significance;
            if(Math.abs(deltas[j])>=0.025f)nonzero++;
        }
        if(nonzero<2)return neutral("already_consistent",best);
        return new Decision(deltas,true,"measured_pixel_correspondence",matched,supported,bestO,bestDx,bestDy,best);
    }
}
