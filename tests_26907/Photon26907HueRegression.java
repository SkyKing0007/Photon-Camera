import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2PreviewHueCalibration;

public final class Photon26907HueRegression {
    private static void require(boolean condition,String reason){if(!condition)throw new AssertionError(reason);}
    private static float encodeToLinear(float c){return c<=0.04045f?c/12.92f:(float)Math.pow((c+0.055)/1.055,2.4);}
    private static float[] rgb(float h,float sat,float val){
        float hue=((h%360)+360)%360/60f, chroma=val*sat;
        float x=chroma*(1-Math.abs(hue%2-1));
        float[] a;
        if(hue<1)a=new float[]{chroma,x,0};
        else if(hue<2)a=new float[]{x,chroma,0};
        else if(hue<3)a=new float[]{0,chroma,x};
        else if(hue<4)a=new float[]{0,x,chroma};
        else if(hue<5)a=new float[]{x,0,chroma};
        else a=new float[]{chroma,0,x};
        float m=val-chroma;
        return new float[]{a[0]+m,a[1]+m,a[2]+m};
    }
    private static int argb(float[] a){
        int r=Math.min(255,Math.max(0,Math.round(a[0]*255))),
            g=Math.min(255,Math.max(0,Math.round(a[1]*255))),
            b=Math.min(255,Math.max(0,Math.round(a[2]*255)));
        return 0xff000000|(r<<16)|(g<<8)|b;
    }
    private static void setP3(float[] data,int rawIdx,float[] a){
        float r=encodeToLinear(a[0]),g=encodeToLinear(a[1]),b=encodeToLinear(a[2]);
        data[rawIdx*4] = 0.8224621f*r+0.1775379f*g;
        data[rawIdx*4+1]=0.0331941f*r+0.9668059f*g;
        data[rawIdx*4+2]=0.0170827f*r+0.0723974f*g+0.9105199f*b;
        data[rawIdx*4+3]=1;
    }
    private static MotionV2PreviewHueCalibration.Decision run(boolean mismatch){
        final int pw=192,ph=256,rw=256,rh=192;
        int[] preview=new int[pw*ph];float[] raw=new float[rw*rh*4];
        for(int y=0;y<ph;y++)for(int x=0;x<pw;x++){
            // Non-semantic structured scene: separate orange/yellow bodies, blue background,
            // green leaves and neutral center. Shapes/brightness identical, only hues differ.
            float wave=(float)(0.055*Math.sin(x*0.09+y*0.04)+0.04*Math.cos(y*0.13-x*0.07));
            float vignette=0.9f+(float)(0.07*Math.sin(x*0.12)*Math.cos(y*0.16));
            float h,s=0,v;
            if(x>=25&&x<145&&y>=65&&y<220){
                int region=((x-25)/40+(y-65)/38)%3;
                h=region==0?35:region==1?49:64;
                s=0.70f;
                v=(0.55f+wave)*vignette;
            }else if(x>=145&&y>=65&&y<220){h=120;s=0.6f;v=(0.46f+wave)*vignette;}
            else if(x<80&&y<65){h=210;s=0.6f;v=(0.42f+wave)*vignette;}
            else{h=0;s=0;v=0.52f+wave;}
            float[] a=rgb(h,s,Math.max(0.1f,Math.min(0.9f,v)));
            preview[y*pw+x]=argb(a);
            // Corresponding image is shot with a warmer or yellower red-orange rotation,
            // but EXACT luma and object boundaries; positive shift means capture is yellower.
            if(mismatch && h>15 && h<85)h+=16;
            float[] b=rgb(h,s,Math.max(0.1f,Math.min(0.9f,v)));
            // Orientation 6 maps portrait(x,y) -> raw(sx=y, sy=x).
            setP3(raw,x*rw+y,b);
        }
        return MotionV2PreviewHueCalibration.measure(preview,pw,ph,raw,rw,rh);
    }
    public static void main(String[] args){
        MotionV2PreviewHueCalibration.Decision changed=run(true);
        require(changed.valid,"hue-drift test not activated: "+changed.reason+" corr="+changed.alignment);
        require(changed.alignment>0.5f,"low correspondence for synthetic structured test");
        boolean moved=false;float least=0;
        for(float d:changed.deltaRad)if(d<-0.07f){moved=true;least=Math.min(least,d);}
        require(moved,"no dynamic orange/yellow correction after measured shift");
        require(least> -0.47f,"unbounded hue shift");
        MotionV2PreviewHueCalibration.Decision same=run(false);
        require(!same.valid,"correct scene should be identity: "+same.reason);
        for(float d:same.deltaRad)require(d==0,"already matching scene altered");
        MotionV2PreviewHueCalibration.Decision bad=MotionV2PreviewHueCalibration.measure(new int[0],192,256,new float[12],256,192);
        require(!bad.valid,"invalid buffer should fail closed");
        System.out.println("PASS 26907 actual calibration utility javac: per-color measured correction="+least+
            " rad, already-matching identity, invalid geometry rejection, orientation="+changed.orientation+
            " corr="+changed.alignment);
    }
}
