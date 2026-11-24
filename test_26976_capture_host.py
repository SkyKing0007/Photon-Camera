#!/usr/bin/env python3
"""Real Java C acquisition regressions, independent of Android HAL availability."""
import argparse,pathlib,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);a=p.parse_args()
r=a.root/'src/main/java/com/particlesdevs/photoncamera/processing/experimentc'
classes=['Iris26976CRawTicketJoin','Iris26976CExposureEpoch','Iris26975CDonorExposurePolicy','Iris26975CHighlightFreeze']
java=r'''
import com.particlesdevs.photoncamera.processing.experimentc.*;
import java.util.*;
public final class CAcquisition26976 {
 static int checks;
 static void ok(boolean condition) {++checks; if(!condition) throw new AssertionError("check "+checks);}
 static class Lease {final long ts;int closes;Lease(long ts){this.ts=ts;}void close(){if(++closes!=1)throw new AssertionError("double close "+ts);}}
 static void burst(int n,int pre) {
  List<Lease> leases=new ArrayList<>();List<Long> staged=new ArrayList<>();
  Iris26976CRawTicketJoin<Lease> j=new Iris26976CRawTicketJoin<>(n, n+1,Lease::close);
  long last=1000;
  for(int i=0;i<pre;i++) {long ts=last+=100;ok(j.start(ts)==null);Lease raw=new Lease(ts);leases.add(raw);Lease got=j.image(ts,raw);ok(got==raw);staged.add(got.ts);got.close();}
  // Reproduce all four logged failures: stale preview images AFTER existing pre-ZSL admission.
  for(int i=0;i<5;i++) {Lease stale=new Lease(last+i+1);leases.add(stale);ok(j.image(stale.ts,stale)==null);}
  ok(j.acceptedCount()==pre);
  for(int i=pre;i<n;i++) {
   long ts=last+=100;Lease raw=new Lease(ts);leases.add(raw);Lease got;
   if(i%2==0){ok(j.image(ts,raw)==null);got=j.start(ts);}
   else {ok(j.start(ts)==null);got=j.image(ts,raw);}
   ok(got==raw);staged.add(got.ts);got.close();
   Lease duplicate=new Lease(ts);leases.add(duplicate);ok(j.image(ts,duplicate)==null&&duplicate.closes==1);
  }
  // Unexpected future/old arrivals after the complete budget never poison it.
  Lease late=new Lease(last+1);leases.add(late);ok(j.image(late.ts,late)==null&&late.closes==1);
  ok(j.acceptedCount()==n&&j.pendingCount()==0&&staged.size()==n);
  ok(new HashSet<>(staged).size()==n);j.close();j.close();for(Lease l:leases)ok(l.closes==1);
 }
 public static void main(String[] args){
  // 26975 device log pre/post: 13/2, 1/14, 14/1, 1/14; full ring and no ring; slider endpoints.
  for(int pre:new int[]{13,1,14,1,15,0})burst(15,pre);
  burst(2,0);burst(2,2);burst(30,29);burst(30,30);
  Iris26976CRawTicketJoin<Lease> j=new Iris26976CRawTicketJoin<>(15,2,Lease::close);
  Lease a=new Lease(10),b=new Lease(20),c=new Lease(30);j.image(10,a);j.image(20,b);j.image(30,c);
  ok(a.closes==1&&j.pendingCount()==2&&j.acceptedCount()==0);j.close();ok(b.closes==1&&c.closes==1);
  Iris26976CRawTicketJoin<Lease> early=new Iris26976CRawTicketJoin<>(2,2,Lease::close);
  Lease e2=new Lease(200),e1=new Lease(100);early.image(200,e2);early.image(100,e1);ok(early.start(100)==e1);e1.close();ok(early.start(200)==e2);e2.close();early.close();
  boolean rejected=false;try{early.start(300);}catch(IllegalArgumentException ex){rejected=true;}ok(rejected);
  // Positive actual physical ISO outside advertised bounds must preserve donor pair; no invented gain.
  var pair=Iris26975CDonorExposurePolicy.freeze(0,0,8333333L,25,10000000L,100,100000,1000000000L,50,6400,1000000000L);
  ok(pair.shutterNs==8333333L&&pair.iso==25);
  pair=Iris26975CDonorExposurePolicy.freeze(0,0,8333333L,640,null,null,0,0,0,0,null);ok(pair.shutterNs==8333333L&&pair.iso==640);
  var protect=Iris26975CHighlightFreeze.freezeOwnMeter(false,8333333L,25,1.5f,100000,1000000000L,50,6400);
  ok(protect.exposureNs==8333333L&&protect.iso==25&&protect.appliedProtectionEv==0);
  protect=Iris26975CHighlightFreeze.freezeOwnMeter(false,8333333L,640,1f,100000,1000000000L,50,6400);ok(protect.exposureNs<8333333L&&protect.iso==640&&protect.appliedProtectionEv>.9f);
  protect=Iris26975CHighlightFreeze.freezeOwnMeter(false,8333333L,640,1f,0,0,0,0);ok(protect.exposureNs==8333333L&&protect.iso==640);
  ok(!Iris26975CDonorExposurePolicy.allowHighlightAdjustment(3,1));ok(!Iris26975CDonorExposurePolicy.allowHighlightAdjustment(3,null));ok(Iris26975CDonorExposurePolicy.allowHighlightAdjustment(3,0));
  rejected=false;try{Iris26975CDonorExposurePolicy.freeze(0,0,0L,640,null,null,0,0,0,0,null);}catch(IllegalArgumentException ex){rejected=true;}ok(rejected);
  rejected=false;try{Iris26975CDonorExposurePolicy.freeze(10000000,25,10000000L,25,10000000L,25,100000,1000000000L,50,6400,null);}catch(IllegalArgumentException ex){rejected=true;}ok(rejected);
  Iris26976CExposureEpoch ep=new Iris26976CExposureEpoch();
  ok(!ep.observeAuto(100,10000000,100,null));ok(!ep.observeAuto(200,10000000,100,null));ok(ep.observeAuto(300,10000000,100,null));
  ok(!ep.observeAuto(200,10000000,100,2));ep.reset();ok(ep.observeAuto(1,10000000,100,2));
  ep.reset();ok(!ep.observeLocked(1000000000L,10000000,100,.10f,0));ok(!ep.observeLocked(1300000000L,10000000,100,.3f,0));
  ok(!ep.observeLocked(1500000000L,10000000,100,.3f,0));ok(ep.observeLocked(2000000000L,10000000,100,.3f,0));
  ok(!ep.observeLocked(2500000000L,5000000,100,.3f,0)); // change in actual pair resets baseline
  ep.reset();for(int i=1;i<=10;i++)ok(ep.observeLocked(i*500000000L,10000000,100,Float.NaN,Float.NaN)==(i==10));
  System.out.println("PASS "+checks+" acquisition assertions; exact logged partial bursts, full/empty ring, out-of-order images, stale/duplicate lease retirement, bounds, flicker and HAL remeter");
 }
}
'''
with tempfile.TemporaryDirectory(prefix='26976-C-host-') as d:
 d=pathlib.Path(d);f=d/'CAcquisition26976.java';f.write_text(java)
 subprocess.run(['javac','-d',str(d),*[str(r/(n+'.java')) for n in classes],str(f)],check=True)
 subprocess.run(['java','-cp',str(d),'CAcquisition26976'],check=True)
