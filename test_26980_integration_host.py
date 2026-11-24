#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);a=p.parse_args();r=a.root/'src/main/java/com/particlesdevs/photoncamera/processing/experimentc'
java='''import com.particlesdevs.photoncamera.processing.experimentc.*;
import java.util.*;
public class Host26980 {
 static int n; static void ok(boolean b){n++;if(!b)throw new AssertionError("assertion "+n);}
 static Iris26980CManualExposure.Pair plan(long ss,int iso,boolean steady,Integer flicker,float mean,float high,float clipped,float protect){
 return Iris26980CManualExposure.plan(ss,iso,11041L,1000000000L,50,3200,1000000000L,steady,flicker,mean,high,clipped,protect);}
 public static void main(String[] args){
 var dark=plan(40000000L,3200,true,0,.0148f,.2f,0f,0f);
 ok(dark.shutterNs==1000000000L/17);ok(dark.iso==2176);ok((double)dark.shutterNs*dark.iso<=40000000d*3200);
 var hz50=plan(40000000L,3200,true,1,.0148f,.2f,0f,0f);ok(hz50.shutterNs==50000000L);ok(hz50.iso==2560);
 var hz60=plan(33333333L,3200,true,2,.0148f,.2f,0f,0f);ok(hz60.shutterNs>=33333333L);ok(Math.abs(hz60.shutterNs/8333333.333333-Math.rint(hz60.shutterNs/8333333.333333))<.00001);
 ok(plan(40000000L,3200,true,2,.0148f,.2f,0f,0f).shutterNs==40000000L);
 ok(plan(40000000L,3200,false,0,.0148f,.2f,0f,0f).shutterNs==40000000L);
 ok(plan(40000000L,3200,true,null,.0148f,.2f,0f,0f).shutterNs==40000000L);
 ok(plan(40000000L,3200,true,0,.0148f,.8f,0f,0f).shutterNs==40000000L);
 ok(plan(40000000L,3200,true,0,.0148f,.2f,.01f,0f).shutterNs==40000000L);
 ok(plan(40000000L,3200,true,0,.0148f,.2f,0f,.33f).shutterNs==40000000L);
 var bright=plan(296055L,50,true,0,.013f,.9f,0f,.33f);ok(bright.shutterNs==296055L);ok(bright.iso==50);
 ok(plan(70000000L,3200,true,0,.0148f,.2f,0f,0f).shutterNs==70000000L);
 ok(plan(20000000L,3211,false,0,.0148f,.2f,0f,0f).iso==3200);ok(plan(30000000L,3215,false,0,.0148f,.2f,0f,0f).iso==3200);
 for(int iso:new int[]{50,100,399,400,800,1600,3200,3215})for(long ss:new long[]{100000L,10000000L,20000000L,30000000L,40000000L,70000000L})for(int f:new int[]{0,1,2,3}){
  var x=plan(ss,iso,true,f,.02f,.3f,0f,0f);ok(x.iso>=50&&x.iso<=3200);ok(x.shutterNs>=ss&&x.shutterNs<=Math.max(ss,1000000000L/17));ok((double)x.shutterNs*x.iso<=(double)ss*iso);}
 // Both logged 15-frame patterns: 0+15 and 7+8, with incompatible physical ISO attempts.
 for(int pre:new int[]{0,7,14,15}){
  var g=new Iris26980CExactExposureGroup(15);long ss=pre==0?20000000L:30000000L;int iso=pre==0?3211:3215;
  for(int i=0;i<pre;i++)ok(g.admit(ss,iso));if(pre==0)ok(g.admit(ss,iso));
  while(g.remaining()>0){int before=g.remaining();ok(!g.admit(ss,iso-1));ok(g.remaining()==before);ok(!g.admit(ss+1,iso));ok(g.remaining()==before);ok(g.admit(ss,iso));ok(g.remaining()==before-1);}
  ok(g.accepted()==15);ok(g.attemptsRemaining()>=0);try{g.admit(ss,iso);throw new AssertionError();}catch(IllegalArgumentException e){ok(true);}
 }
 for(int size=2;size<=30;size++){var g=new Iris26980CExactExposureGroup(size);ok(g.admit(10000,50));for(int i=1;i<size;i++){ok(!g.admit(10001,50));ok(g.admit(10000,50));}ok(g.remaining()==0);}
 var exhausted=new Iris26980CExactExposureGroup(2);ok(exhausted.admit(10000,50));for(int i=0;i<5;i++)ok(!exhausted.admit(10000,51));ok(exhausted.attemptsRemaining()==0);try{exhausted.admit(10000,50);throw new AssertionError();}catch(IllegalArgumentException e){ok(true);}
 // Actual runtime ticket class: RAW can arrive before start or result; late rejected leases are closed,
 // never consume the accepted count or the limited provisional leases.
 List<String> closed=new ArrayList<>();var join=new Iris26976CRawTicketJoin<String>(2,2,closed::add,true);
 ok(join.image(10,"early")==null);ok(join.start(10).equals("early"));join.reject(10);ok(join.acceptedCount()==0);ok(join.image(10,"late rejected")==null);ok(closed.contains("late rejected"));
 ok(join.start(20)==null);join.reject(20);ok(join.image(20,"after rejection")==null);ok(closed.contains("after rejection"));
 ok(join.image(30,"good one")==null);ok(join.start(30).equals("good one"));ok(join.acceptedCount()==1);ok(join.start(40)==null);ok(join.image(40,"good two").equals("good two"));ok(join.acceptedCount()==2);join.close();
 var bounded=new Iris26976CRawTicketJoin<String>(15,5,closed::add,true);for(int i=1;i<=8;i++)bounded.image(i,"pending"+i);ok(bounded.pendingCount()==5);bounded.trimPending(2);ok(bounded.pendingCount()==2);bounded.close();ok(bounded.pendingCount()==0);
 System.out.println("PASS "+n+" actual C exposure optimizer, flicker/limits, exact frame replacement and RAW ticket assertions");
 }
}'''
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td);f=d/'Host26980.java';f.write_text(java)
 subprocess.run(['javac','-d',str(d),*[str(r/x) for x in ['Iris26980CManualExposure.java','Iris26980CExactExposureGroup.java','Iris26976CRawTicketJoin.java']],str(f)],check=True)
 subprocess.run(['java','-cp',str(d),'Host26980'],check=True)
