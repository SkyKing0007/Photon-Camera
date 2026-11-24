package com.particlesdevs.photoncamera.ui.camera.views.viewfinder;

/** Exact inverse of main_vs/main_fs preview coordinates, expressed in normalized view pixels.
 * TextureView supplies its actual SurfaceTexture buffer transform; no sensor-orientation guess. */
public final class Iris26983DirectGeometry {
    private Iris26983DirectGeometry() {}
    public static float[] map(float[] st,int degrees,boolean mirror,float zoom) {
        if(st==null || st.length!=16 || !Float.isFinite(zoom) || zoom<1f || degrees%90!=0)
            throw new IllegalArgumentException("unsupported direct geometry");
        for(float value:st) if(!Float.isFinite(value)) throw new IllegalArgumentException("bad buffer transform");
        if(Math.abs(st[3])+Math.abs(st[7])>1e-5f || Math.abs(st[15]-1f)>1e-5f)
            throw new IllegalArgumentException("nonaffine buffer transform");
        float[] src={0f,0f,1f,0f,0f,1f,1f,1f};
        float[] dst=new float[8];
        double a=Math.toRadians(degrees),cs=Math.cos(a),sn=Math.sin(a);
        for(int i=0;i<4;i++) {
            double sx=src[2*i],sy=1.0-src[2*i+1];
            double u=st[0]*sx+st[4]*sy+st[12],v=st[1]*sx+st[5]*sy+st[13];
            if(mirror)v=1-v;
            double x=2*(v-.5)*zoom,y=2*(u-.5)*zoom;
            dst[2*i]=(float)((cs*x-sn*y+1)*.5);
            dst[2*i+1]=(float)((1-sn*x-cs*y)*.5);
        }
        double det=(dst[2]-dst[0])*(dst[5]-dst[1])-(dst[4]-dst[0])*(dst[3]-dst[1]);
        if(!Double.isFinite(det)||Math.abs(det)<1e-6)throw new IllegalArgumentException("degenerate direct geometry");
        return dst;
    }
    /** Require all display corners to lie inside mapped source geometry (minor crop rounding allowed). */
    public static boolean covers(float[] p) {
        if(p==null||p.length!=8)return false;
        double ax=p[2]-p[0],ay=p[3]-p[1],bx=p[4]-p[0],by=p[5]-p[1];
        double det=ax*by-ay*bx;
        if(!Double.isFinite(det)||Math.abs(det)<1e-6)return false;
        for(int x=0;x<2;x++)for(int y=0;y<2;y++) {
            double dx=x-p[0],dy=y-p[1],u=(dx*by-dy*bx)/det,v=(ax*dy-ay*dx)/det;
            if(u<-.012||u>1.012||v<-.012||v>1.012)return false;
        }
        return true;
    }
    /** Reject an unproven/wrongly oriented direct image, even if the HAL accepted its stream.
     * Use a small same-scene luma comparison once at handoff, not repeated GPU readbacks.
     * Flat, dark or rapidly changing scenes fail closed; no image quality processing is changed. */
    public static boolean comparable(int[] a,int[] b) {
        if(a==null||b==null||a.length!=b.length||a.length<64)return false;
        double sa=0,sb=0,saa=0,sbb=0,sab=0,err=0;
        for(int i=0;i<a.length;i++) {
            double x=luma(a[i]),y=luma(b[i]); sa+=x;sb+=y;saa+=x*x;sbb+=y*y;sab+=x*y;err+=Math.abs(x-y);
        }
        double n=a.length,va=saa-sa*sa/n,vb=sbb-sb*sb/n;
        if(va/n<36||vb/n<36)return false;
        double corr=(sab-sa*sb/n)/Math.sqrt(va*vb);
        return Double.isFinite(corr)&&corr>=.94&&err/n<=16&&Math.abs(sa-sb)/n<=12;
    }
    private static double luma(int rgb){return .2126*((rgb>>16)&255)+.7152*((rgb>>8)&255)+.0722*(rgb&255);}
}
