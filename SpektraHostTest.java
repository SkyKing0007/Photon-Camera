package com.unspektrawesome.camera.session;
import com.unspektrawesome.camera.*; import java.util.*;
public class HostTest {
 static int n; static void ok(boolean b){n++;if(!b)throw new AssertionError("assertion "+n);}
 static RawOutput o(RawFormat f,int w,int h,boolean m){return new RawOutput(f,new Size2d(w,h),33333333,0,m);}
 static void reject(Runnable r){try{r.run();throw new AssertionError("accepted invalid route");}catch(IllegalArgumentException expected){n++;}}
 public static void main(String[] a){
 for(int h:new int[]{3072,3064}){
 var b=o(RawFormat.RAW10,4080,h,false);var f=o(RawFormat.RAW10,8160,2*h,true);var small=o(RawFormat.RAW10,2040,h/2,false);var list=List.of(f,small,b);
 ok(RawPreviewPolicy.selectCaptureOutput(list)==b);
 ok(StillCapturePlanner.select(Camera2RawSession.State.STREAMING,list,EnumSet.allOf(RawFormat.class))==b);
 ok(RawPreviewPolicy.selectCaptureOutput(List.of(b,o(RawFormat.RAW10,4080,h,true)))==b);
 ok(RawPreviewPolicy.selectCaptureOutput(List.of(f,o(RawFormat.RAW12,4080,h,false))).format==RawFormat.RAW12);
 ok(RawPreviewPolicy.selectCaptureOutput(List.of(f,o(RawFormat.RAW_SENSOR,4080,h,false))).format==RawFormat.RAW_SENSOR);
 ok(RawPreviewPolicy.selectCaptureOutput(List.of(b,o(RawFormat.RAW_SENSOR,5000,4000,false)))==b);
 reject(()->RawPreviewPolicy.selectCaptureOutput(List.of(f)));
 reject(()->RawPreviewPolicy.selectCaptureOutput(list,EnumSet.of(RawFormat.RAW12)));
 ok(RawPreviewPolicy.select(list,List.of(new IntRange(30,30)),RawPreviewPolicy.Quality.MEDIUM,30).acquisitionOutput.maximumResolutionMode==false);
 }
 Random rng=new Random(26993);for(int i=0;i<10000;i++){
 List<RawOutput> list=new ArrayList<>();for(int j=0;j<8;j++)list.add(o(RawFormat.values()[rng.nextInt(3)],100+2*rng.nextInt(5000),100+2*rng.nextInt(4000),rng.nextBoolean()));
 Set<RawFormat> allowed=EnumSet.noneOf(RawFormat.class);for(var f:RawFormat.values())if(rng.nextBoolean())allowed.add(f);
 RawOutput expected=null;for(var fmt:new RawFormat[]{RawFormat.RAW10,RawFormat.RAW12,RawFormat.RAW_SENSOR}){if(!allowed.contains(fmt))continue;for(var x:list)if(!x.maximumResolutionMode&&x.format==fmt&&(expected==null||x.size.area()>expected.size.area()))expected=x;if(expected!=null)break;}
 if(expected==null)reject(()->RawPreviewPolicy.selectCaptureOutput(list,allowed));else ok(RawPreviewPolicy.selectCaptureOutput(list,allowed)==expected);
 }
 System.out.println("PASS "+n+" actual Java selector/session-planner assertions");
 }
}