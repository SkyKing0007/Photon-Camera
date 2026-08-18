package com.particlesdevs.photoncamera.processing.processor;

import com.particlesdevs.photoncamera.util.Log;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;

/** IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW */
public final class MotionV2DngColorShadow {
    private static final String TAG="MotionV2DngColorShadow";
    private MotionV2DngColorShadow(){}

    private static final float[] XYZ_TO_LINEAR_SRGB=new float[]{
         3.2404542f,-1.5371385f,-0.4985314f,
        -0.9692660f, 1.8760108f, 0.0415560f,
         0.0556434f,-0.2040259f, 1.0572252f
    };

    public static void logShadow(Object parameters){
        if(parameters==null)return;
        String[] names=new String[]{
            "cameraNeutral","neutralColorPoint","asShotNeutral",
            "calibrationIlluminant1","calibrationIlluminant2",
            "cameraCalibration1","cameraCalibration2",
            "colorMatrix1","colorMatrix2",
            "forwardTransform1","forwardTransform2",
            "forwardMatrix1","forwardMatrix2",
            "sensorToXYZ","sensorToXyz","sensorToProPhoto"
        };
        float[] sensorToXyz=null;
        StringBuilder found=new StringBuilder();
        for(String name:names){
            Object value=field(parameters,name);
            if(value==null)continue;
            if(found.length()>0)found.append(" | ");
            found.append(name).append('=').append(describe(value));
            if(sensorToXyz==null&&(name.equals("sensorToXYZ")||name.equals("sensorToXyz"))){
                float[] m=matrix9(value);
                if(m!=null)sensorToXyz=m;
            }
        }
        Log.d(TAG,"IRIS_26474_DNG_METADATA_SHADOW"
                +" jpegOutputOwner=26430 shadowOnly=true discovered={"+found+"}");
        if(sensorToXyz!=null){
            float[] shadow=multiply3x3(XYZ_TO_LINEAR_SRGB,sensorToXyz);
            Log.d(TAG,"IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW"
                    +" source=sensorToXYZ target=linear_sRGB outputApplied=false matrix="+fmt(shadow));
        }else{
            Log.d(TAG,"IRIS_26474_DNG_SCENE_LINEAR_COLOR_SHADOW"
                    +" source=sensorToXYZ available=false outputApplied=false");
        }
    }

    private static Object field(Object o,String name){
        Class<?> c=o.getClass();
        while(c!=null){
            try{
                Field f=c.getDeclaredField(name);
                f.setAccessible(true);
                return f.get(o);
            }catch(Throwable ignored){}
            c=c.getSuperclass();
        }
        return null;
    }

    private static float[] matrix9(Object v){
        try{
            if(v instanceof float[]){
                float[] a=(float[])v;
                if(a.length>=9){
                    float[] r=new float[9];
                    System.arraycopy(a,0,r,0,9);
                    return r;
                }
            }
            if(v instanceof double[]){
                double[] a=(double[])v;
                if(a.length>=9){
                    float[] r=new float[9];
                    for(int i=0;i<9;i++)r[i]=(float)a[i];
                    return r;
                }
            }
            if(v.getClass().isArray()&&Array.getLength(v)>=9){
                float[] r=new float[9];
                for(int i=0;i<9;i++)r[i]=Float.parseFloat(String.valueOf(Array.get(v,i)));
                return r;
            }
            for(String methodName:new String[]{"getArray","getData"}){
                try{
                    Method m=v.getClass().getMethod(methodName);
                    float[] r=matrix9(m.invoke(v));
                    if(r!=null)return r;
                }catch(Throwable ignored){}
            }
        }catch(Throwable ignored){}
        return null;
    }

    private static String describe(Object v){
        float[] m=matrix9(v);
        if(m!=null)return fmt(m);
        return String.valueOf(v);
    }

    private static float[] multiply3x3(float[] a,float[] b){
        float[] r=new float[9];
        for(int y=0;y<3;y++)for(int x=0;x<3;x++){
            float s=0;
            for(int k=0;k<3;k++)s+=a[y*3+k]*b[k*3+x];
            r[y*3+x]=s;
        }
        return r;
    }

    private static String fmt(float[] a){
        return String.format(Locale.US,
            "[%.7f,%.7f,%.7f;%.7f,%.7f,%.7f;%.7f,%.7f,%.7f]",
            a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8]);
    }
}

