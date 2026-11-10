import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2PreviewHueCalibration;

/** Compile and execute the ACTUAL production 26916 calibration, not a mock. */
public final class Photon26916HueRegression {
    private static void require(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static float decode(float c){return c<=0.04045f?c/12.92f:(float)Math.pow((c+0.055f)/1.055f,2.4);}
    private static float[] rgb(float h,float sat,float val){
        h=((h%360)+360)%360/60f;
        float chroma=val*sat,x=chroma*(1-Math.abs(h%2-1));
        float[] a=h<1?new float[]{chroma,x,0}:h<2?new float[]{x,chroma,0}:
            h<3?new float[]{0,chroma,x}:h<4?new float[]{0,x,chroma}:
            h<5?new float[]{x,0,chroma}:new float[]{chroma,0,x};
        float m=val-chroma;return new float[]{a[0]+m,a[1]+m,a[2]+m};
    }
    private static int argb(float[] a){
        int r=Math.min(255,Math.max(0,Math.round(a[0]*255)));
        int g=Math.min(255,Math.max(0,Math.round(a[1]*255)));
        int b=Math.min(255,Math.max(0,Math.round(a[2]*255)));
        return 0xff000000|(r<<16)|(g<<8)|b;
    }
    private static void p3(float[] out,int idx,float[] a){
        float r=decode(a[0]),g=decode(a[1]),b=decode(a[2]);
        out[4*idx]=0.8224621f*r+0.1775379f*g;
        out[4*idx+1]=0.0331941f*r+0.9668059f*g;
        out[4*idx+2]=0.0170827f*r+0.0723974f*g+0.9105199f*b;
        out[4*idx+3]=1f;
    }
    private static MotionV2PreviewHueCalibration.Decision scene(boolean mismatch){
        final int pw=192,ph=256,rw=256,rh=192;
        int[] preview=new int[pw*ph];float[] raw=new float[rw*rh*4];
        for(int y=0;y<ph;y++)for(int x=0;x<pw;x++){
            float wave=(float)(0.055*Math.sin(x*0.09+y*0.04)+0.04*Math.cos(y*0.13-x*0.07));
            float vignette=0.9f+(float)(0.07*Math.sin(x*0.12)*Math.cos(y*0.16));
            float h,s=0,v;
            if(x>=25&&x<145&&y>=65&&y<220){
                int region=((x-25)/40+(y-65)/38)%3;
                h=region==0?35:region==1?49:64;s=0.70f;v=(0.55f+wave)*vignette;
            }else if(x>=145&&y>=65&&y<220){h=120;s=0.6f;v=(0.46f+wave)*vignette;}
            else if(x<80&&y<65){h=210;s=0.6f;v=(0.42f+wave)*vignette;}
            else{h=0;s=0;v=0.52f+wave;}
            v=Math.max(0.1f,Math.min(0.9f,v));
            preview[y*pw+x]=argb(rgb(h,s,v));
            if(mismatch&&h>15&&h<85)h+=16f;
            // Orientation 6: portrait preview(x,y) maps to RAW landscape(y,x).
            p3(raw,x*rw+y,rgb(h,s,v));
        }
        return MotionV2PreviewHueCalibration.measure(preview,pw,ph,raw,rw,rh);
    }
    public static void main(String[] args){
        var altered=scene(true);
        require(altered.valid,"measured synthetic hue correction lost: "+altered.reason+
                " registration="+altered.alignment+" supported="+altered.supportedBins);
        require(altered.alignment>=0.50f,"registration score unsafe");
        float min=0f;
        int used=0,zeros=0;
        for(float d:altered.deltaRad){
            require(Float.isFinite(d)&&Math.abs(d)<=0.32001f,"unbounded or nonfinite");
            min=Math.min(min,d);
            if(Math.abs(d)>0.001f)used++;
            else zeros++;
        }
        require(min<-0.015f,"measured difference not adjusted");
        require(zeros>=24,"insufficient unsupported hue sectors protected from global extrapolation: "+zeros);
        require(used<=20,"unmeasured full-circle hue rotation: "+used);
        var same=scene(false);
        require(!same.valid,"identical preview/RAW erroneously adjusted");
        for(float d:same.deltaRad)require(d==0f,"identical scene changed");
        var bad=MotionV2PreviewHueCalibration.measure(new int[0],192,256,new float[5],256,192);
        require(!bad.valid,"invalid image dimensions accepted");
        System.out.println("PASS actual 26916 javac: registered hue residual, confidence-zero unsupported hue bins, identity, invalid geometry, hue-shift="+min);
    }
}
