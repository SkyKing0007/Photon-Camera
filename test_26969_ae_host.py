#!/usr/bin/env python3
"""Real production Java AE solver, metering, frame loop, 1/14s and 50/60 Hz host compilation."""
import pathlib,sys,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parent
root=R/'handoff_payload_26969' if '--payload' in sys.argv else R
f=root/'app/src/main/java/com/particlesdevs/photoncamera/capture'
files=[f/('Iris26969RawrAe'+s+'.java') for s in ('Math','Metering','Loop')]
for x in files:assert x.is_file(),x
program=r'''
import com.particlesdevs.photoncamera.capture.*;
public final class TestAe26969 {
 static void ck(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[] args) {
  var l=new Iris26969RawrAeMath.Limits();l.isoMin=100;l.isoMax=12800;l.isoAnalogMax=3200;
  ck(Iris26969RawrAeMath.DEFAULT_MAX_STILL_SHUTTER_NS==71_428_571L,"1/14 default");
  var r=Iris26969RawrAeMath.solve(33_333_333.0*12824.0,l,0f,0L);
  ck(r.shutterNs<=71_428_571L,"1/14 cap");ck(r.iso<=3200,"analog ceiling");
  ck(r.digitalGainEv>=0f && r.digitalGainEv<=2.0f,"bounded gain");
  for(long per:new long[]{8_333_333L,10_000_000L}){
    var x=Iris26969RawrAeMath.solve(40_000_000.0*600.0,l,0f,per);
    ck(x.shutterNs%per==0,"50/60 flicker period");ck(x.shutterNs<=71_428_571L,"flicker max");
  }
  int[] h=new int[128],c=new int[128];h[54]=900;c[56]=900;
  var loop=new Iris26969RawrAeLoop();long ns=1_000_000_000L;
  for(int i=0;i<180;i++,ns+=33_333_333L){
    var f=new Iris26969RawrAeMetering.Frame(ns,20_000_000L,400,1.8f,h,c,0);
    var step=loop.update(f,l,i<80?0:i<120?10_000_000L:8_333_333L,0f,0);
    ck(step!=null,"step returned");ck(step.request.shutterNs<=71_428_571L,"loop max");
    ck(step.request.iso<=3200,"loop analog cap");ck(Double.isFinite(step.targetLogExposure),"finite target");
    if(i>=80){long per=i<120?10_000_000L:8_333_333L;
      if(step.request.shutterNs>=per)ck(step.request.shutterNs%per==0,"flicker snap loop");}
  }
  ck(loop.update(new Iris26969RawrAeMetering.Frame(2L,20_000_000L,400,1.8f,h,c,0),l,0L,0f,0)==null,"reject nonmonotonic timestamp");
  loop.reset();ck(loop.update(new Iris26969RawrAeMetering.Frame(2L,20_000_000L,400,1.8f,h,c,0),l,0L,0f,0)!=null,"reset");
  System.out.println("PASS 26969 production RAWR AE Java host 1/14, 50/60 Hz, no-flicker loop, ISO analog gain, temporal reset");
 }
}
'''
with tempfile.TemporaryDirectory(prefix='iris26969_ae_') as t:
 p=pathlib.Path(t);(p/'TestAe26969.java').write_text(program)
 subprocess.run(['javac','--release','17','-d',str(p),*(str(f) for f in files),str(p/'TestAe26969.java')],check=True)
 subprocess.run(['java','-cp',str(p),'TestAe26969'],check=True)
