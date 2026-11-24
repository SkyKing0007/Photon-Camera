#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);a=p.parse_args();r=a.root/'src/main/java/com/particlesdevs/photoncamera/processing/experimentc'
java='''import com.particlesdevs.photoncamera.processing.experimentc.*;
public class Host26981 {
 static int n; static void ok(boolean b){n++;if(!b)throw new AssertionError("assertion "+n);}
 static Iris26981CManualExposure.Pair plan(long ss,int iso,int gyro,float mm,Integer flicker,float mean,float high,float clip,float protection){return Iris26981CManualExposure.plan(ss,iso,11041L,1000000000L,50,3200,1000000000L,gyro,mm,flicker,mean,high,clip,protection);}
 public static void main(String[] args){
 var t=new Iris26981CExposureTracking();t.selectLens("0");t.selectUserComp(0);
 // Replay the 26980 staircase; one target at the unprotected base, no repeated compensation.
 float step=1f/6f;ok(t.observeProtection(.37f,.98f,.0033f,0,step,0,-12,12));ok(t.compensation(0,-12,12,step)==-2);
 for(float d:new float[]{.36f,.35f,.42f,.6f,1.5f}){t.resetRequest();ok(!t.observeProtection(d,.97f,.003f,1f/3f,step,0,-12,12));ok(t.compensation(0,-12,12,step)==-2);}
 t.clearProtection();ok(!t.observeProtection(.12f,.92f,.001f,0,step,0,-12,12));ok(t.compensation(0,-12,12,step)==0);
 t.clearProtection();ok(t.observeProtection(5f,1f,.03f,0,step,0,-12,12));ok(t.compensation(0,-12,12,step)==-9);
 t.selectUserComp(3);ok(t.protectionEv()==0);ok(t.compensation(3,-12,12,step)==3);ok(t.observeProtection(.40f,.95f,.01f,0,step,3,-12,12));ok(t.compensation(3,-12,12,step)==1);
 t.selectLens("1");ok(t.protectionEv()==0);ok(!t.observeProtection(Float.NaN,.95f,.01f,0,step,0,-12,12));
 t.clearProtection();ok(!t.observeAuto(1000000000L,30000000L,1600,1,true));ok(!t.observeAuto(1100000000L,30000000L,1600,2,true));ok(!t.observeAuto(1200000000L,30000000L,1600,2,true));ok(t.observeAuto(1400000000L,30000000L,1600,2,true));
 ok(!t.observeLocked(1500000000L,.1f,.002f,.90f));ok(!t.observeLocked(1620000000L,.1f,.003f,.92f));ok(!t.observeLocked(1740000000L,Float.NaN,Float.NaN,Float.NaN));ok(!t.observeLocked(1860000000L,.16f,.003f,.92f));ok(t.observeLocked(1980000000L,.16f,.003f,.92f));
 var moderate=plan(30000000L,1600,5,24,0,.015f,.2f,0,0);ok(moderate.shutterNs>30000000L&&moderate.shutterNs<66666666L);ok(moderate.iso<1600);
 var protectedDark=plan(30000000L,1600,5,24,0,.015f,.2f,0,.33f);ok(protectedDark.shutterNs==moderate.shutterNs);ok(protectedDark.iso==moderate.iso);
 var longLens=plan(30000000L,1600,5,100,0,.015f,.2f,0,0);ok(longLens.shutterNs<=moderate.shutterNs);
 ok(plan(30000000L,1600,36,24,0,.015f,.2f,0,0).shutterNs==30000000L);ok(plan(30000000L,1600,0,24,null,.015f,.2f,0,0).shutterNs==30000000L);
 ok(plan(30000000L,1600,0,24,0,.015f,.9f,0,0).shutterNs==30000000L);ok(plan(30000000L,1600,0,24,0,.015f,.2f,.002f,0).shutterNs==30000000L);
 ok(plan(70000000L,3200,0,24,0,.015f,.2f,0,0).shutterNs==70000000L);ok(plan(20000000L,3211,36,24,0,.015f,.2f,0,0).iso==3200);
 for(int iso:new int[]{50,400,800,1600,3200,3215})for(long ss:new long[]{100000L,10000000L,20000000L,30000000L,33333333L,40000000L,70000000L})for(int f:new int[]{0,1,2,3})for(int gyro:new int[]{0,15,35,40})for(float mm:new float[]{24,50,100}){
  var x=plan(ss,iso,gyro,mm,f,.02f,.3f,0,.33f);ok(x.iso>=50&&x.iso<=3200);ok(x.shutterNs>=ss&&x.shutterNs<=Math.max(ss,66666666L));ok((double)x.shutterNs*x.iso<=(double)ss*iso);if(x.shutterNs>ss){ok((double)x.shutterNs*.3/ss<=.85001);if(f==1||f==2){double period=f==1?10000000.:1000000000./120;ok(Math.abs(x.shutterNs/period-Math.rint(x.shutterNs/period))<.000001);}}}
 System.out.println("PASS "+n+" actual 26981 Java absolute target, touch settling, adaptive exposure and flicker/limit assertions; intermediate example="+moderate.shutterNs+"ns ISO="+moderate.iso);
 }
}'''
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td);f=d/'Host26981.java';f.write_text(java)
 subprocess.run(['javac','-d',str(d),*[str(r/x) for x in ['Iris26981CExposureTracking.java','Iris26981CManualExposure.java']],str(f)],check=True)
 subprocess.run(['java','-cp',str(d),'Host26981'],check=True)
