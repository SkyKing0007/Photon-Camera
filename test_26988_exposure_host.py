#!/usr/bin/env python3
"""Compile actual pure-Java planner, exact timestamp continuity, all-channel meter and changed Java syntax."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parent;J=R/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc'
java='''import com.particlesdevs.photoncamera.processing.experimentc.*;
import java.nio.*;
public class Host26988 {
 static int n; static void ok(boolean x){n++;if(!x)throw new AssertionError("test "+n);}
 static Iris26988CExposurePlan.Pair plan(long ss,int iso,int gyro,float mm,Integer flicker,float mean,float hi,float peak,float clip,float protection,float demand,boolean ref){return Iris26988CExposurePlan.plan(ss,iso,11041,1000000000L,50,6400,1000000000L,gyro,mm,flicker,mean,hi,peak,clip,protection,demand,ref);}
 public static void main(String[] args){
 // Actual 26987 clipped ISO50 chandelier: do not claim extra photons or clip recovery.
 var clipped=plan(1762954,50,54,24,0,.018770756f,.99f,1f,.002578298f,.333f,.35929406f,true);ok(clipped.shutterNs==1762954&&clipped.iso==50);
 var low=plan(10000000,100,0,24,0,.02f,.25f,.30f,0,0,0,true);ok(low.shutterNs>10000000&&low.iso<100&&low.exposureRatio<=1.0);
 var min=plan(10000000,50,0,24,0,.02f,.25f,.30f,0,0,0,true);ok(min.shutterNs>10000000&&min.iso==50&&min.exposureRatio<=Math.pow(2,.33));
 ok(plan(10000000,50,0,24,0,.02f,.25f,.30f,0,0,0,false).shutterNs==10000000);
 ok(plan(10000000,50,0,24,0,.02f,.25f,.30f,0,.33f,0,true).shutterNs==10000000);
 ok(plan(10000000,50,0,24,0,.02f,.25f,.99f,0,0,0,true).shutterNs==10000000);
 ok(plan(10000000,50,0,24,0,.02f,.25f,.30f,0,0,.04f,true).shutterNs==10000000);
 ok(plan(10000000,50,0,24,1,.02f,.25f,.30f,0,0,0,true).shutterNs==10000000);
 for(int iso:new int[]{50,64,100,200,399,400,800,3200,6400})for(long ss:new long[]{1000000,10000000,20000000,30000000,40000000,70000000})for(int gyro:new int[]{0,15,35,54})for(int flicker:new int[]{0,1,2,3})for(float peak:new float[]{.25f,.5f,.8f,.95f}){
  var x=plan(ss,iso,gyro,24,flicker,.02f,.2f,peak,0,0,0,true);
  ok(x.iso>=50&&x.iso<=6400&&x.shutterNs>=ss&&x.shutterNs<=Math.max(ss,66666666L));
  if(x.shutterNs>ss){ok(peak*x.shutterNs/ss<=.90001&&gyro<=35);ok(x.exposureRatio<=(iso==50?Math.pow(2,.33):1.000001));if(flicker!=0){double period=flicker==1?10000000.:1000000000./120;ok(flicker==1||flicker==2);ok(Math.abs(x.shutterNs/period-Math.rint(x.shutterNs/period))<.000001);}}
 }
 var state=new Iris26988CPreviewContinuity();Object pre=new Object(),tap=new Object(),protect=new Object(),manual=new Object(),stale=new Object();
 long t=1000000000; state.beginAuto(pre,false);state.sample(pre,t,.1f);ok(state.observe(pre,t,10000000,100,.03f));ok(state.anchorReady());
 state.beginAuto(tap,false);ok(!state.anchorReady());state.sample(pre,t+1,.1f);ok(!state.anchorReady());state.sample(tap,t+2,.30f);ok(state.observe(tap,t+2,20000000,100,.06f));ok(state.anchorReady());
 state.beginAuto(protect,true);state.sample(protect,t+3,.20f);ok(state.observe(protect,t+3,15000000,100,.045f));float p=state.gain(protect,t+3);ok(p>1&&Math.abs(Iris26988CPreviewContinuity.whiteAnchored(.2f,p)-.3f)<1e-5);
 state.beginManual(protect,manual,t+3);ok(Float.isNaN(state.gain(protect,t+4)));state.sample(stale,t+4,.01f);state.sample(manual,t+4,.15f);ok(state.observe(manual,t+4,30000000,50,.045f));float g=state.gain(manual,t+4);ok(g>1&&Math.abs(Iris26988CPreviewContinuity.whiteAnchored(.15f,g)-.3f)<1e-5);ok(state.gain(manual,t+3)==1);
 state.beginAuto(tap,false);state.observe(tap,t+10,10000000,100,.03f);ok(state.observe(tap,t+300000010,10000000,100,.03f));ok(!state.anchorReady());
 state.beginAuto(tap,false);state.sample(tap,t+11,.2f);state.observe(tap,t+11,10000000,100,.03f);state.beginManual(tap,manual,t+11);state.sample(manual,t+12,.35f);state.observe(manual,t+12,10000000,100,.03f);ok(state.gain(manual,t+12)<1);ok(Math.abs(Iris26988CPreviewContinuity.whiteAnchored(.35f,state.gain(manual,t+12))-.2f)<1e-5);
 state.beginManual(manual,stale,t+12);state.sample(stale,t+13,.1f);state.observe(stale,t+13,10000000,100,.2f);ok(state.gain(stale,t+13)==1);state.reset();ok(Float.isNaN(state.gain(stale,t+14)));
 ByteBuffer buf=ByteBuffer.allocate(12*96*4);for(int i=0;i<12*96;i++){buf.put((byte)128);buf.put((byte)64);buf.put((byte)32);buf.put((byte)255);}ok(Math.abs(Iris26988CPreviewContinuity.medianGuide(buf)-.21586f)<.0001);
 for(float k:new float[]{.25f,.5f,1f,2f,8f}){ok(Iris26988CPreviewContinuity.whiteAnchored(0,k)==0&&Iris26988CPreviewContinuity.whiteAnchored(1,k)==1);float last=-1;for(int i=0;i<=1000;i++){float v=Iris26988CPreviewContinuity.whiteAnchored(i/1000f,k);ok(v>=last&&v<=1);last=v;}}
 System.out.println("PASS "+n+" actual Java exposure, flicker, sampled highlight, stale-request, tap retention, white-anchored mapping assertions");
 }
}'''
with tempfile.TemporaryDirectory() as t:
 d=Path(t);f=d/'Host26988.java';f.write_text(java)
 subprocess.run(['javac','-d',str(d),*[str(J/x) for x in ['Iris26981CManualExposure.java','Iris26988CExposurePlan.java','Iris26988CPreviewContinuity.java','Iris26975CRawHighlightMeter.java']],str(f)],check=True)
 subprocess.run(['java','-cp',str(d),'Host26988'],check=True)
 subprocess.run(['javac','-d',str(d),str(R/'26985_host_fixtures/ParseJava.java')],check=True)
 subprocess.run(['java','-cp',str(d),'ParseJava',*[str(R/x) for x in (R/'26988_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines() if x.endswith('.java')]],check=True)
