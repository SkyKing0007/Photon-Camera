#!/usr/bin/env python3
"""Actually javac/java compile the 26948 B manual shutter allocation (not just a mock)."""
import pathlib,tempfile,subprocess,sys
from build_26948_incremental import R,fail,scope,sha
JAVA=r"""
import com.particlesdevs.photoncamera.capture.Iris26909ShutterIsoMath;
public class Iris26948FlickerHost {
 static void check(boolean c,String s){if(!c)throw new AssertionError(s);}
 public static void main(String[] args){
  int n=0;
  for(long period:new long[]{10_000_000L,8_333_333L}){
   int harmonic=period==10_000_000L?2:3;
   long skew=(long)Math.round(harmonic * (double)period/.96);
   long detected=Iris26909ShutterIsoMath.verifiedMainsPeriodNs(harmonic,skew,.96);
   check(detected==period,"mains period mismatch");n++;
   check(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(harmonic,skew,Double.NaN)==0,"invalid fraction");n++;
   check(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(harmonic,skew,.4)==0,"ROI unsafe");n++;
   check(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(0,skew,.96)==0,"unmeasured harmonic");n++;
  }
  check(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(3,23_000_000L,.9)==0,"wrong lighting frequency accepted");n++;
  for(int iso:new int[]{50,100,200,400})for(long shutter:new long[]{4_000_000L,7_000_000L,11_500_000L,17_000_000L,25_000_000L,70_000_000L}){
   Iris26909ShutterIsoMath.Plan p=Iris26909ShutterIsoMath.solveBrightnessAware(shutter,iso,50,3200,100000L,100_000_000L,100_000_000L,0L);
   if(p==null){n++;continue;}
   for(long period:new long[]{0L,8_333_333L,10_000_000L,20_000_000L}){
    Iris26909ShutterIsoMath.Plan s=Iris26909ShutterIsoMath.snapVerifiedBPlan(p,period,100000L,50,3200,100_000_000L);
    check(s.shutterNs<=p.shutterNs,"shutter extended/clipping");n++;
    check(Math.abs(Math.log(s.shutterNs*(double)s.iso/p.targetEnergy))<.045,"highlight energy altered");n++;
    check(s.frameDurationNs>=s.shutterNs,"frame duration invalid");n++;
    check(s.iso>=50&&s.iso<=3200,"ISO out of physical limits");n++;
    if(p.shutterNs<period||period==0)check(s.shutterNs==p.shutterNs,"short shutter changed");n++;
   }
  }
  Iris26909ShutterIsoMath.Plan tiny=Iris26909ShutterIsoMath.solveBrightnessAware(3_140_000L,100,50,3200,100000L,100000000L,100000000L,0);
  check(tiny!=null,"bright highlight plan missing");n++;
  check(Iris26909ShutterIsoMath.snapVerifiedBPlan(tiny,10_000_000L,100000L,50,3200,100000000L).shutterNs==tiny.shutterNs,"3.14ms highlight shutter changed");n++;
  System.out.println("PASS actual JDK javac/java B-only 26948 verified flicker manual + original highlighted shutter budget cases="+n);
 }
}
"""
def main():
 _,_,new=scope();path='app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java'
 source=(R if '--live' in sys.argv else R/'handoff_payload_26948')/path
 if not source.is_file() or sha(source)!=new[path]:fail('source math candidate is absent/stale')
 with tempfile.TemporaryDirectory(prefix='p26948_java_host_') as d:
  d=pathlib.Path(d); t=d/'Iris26948FlickerHost.java';t.write_text(JAVA)
  subprocess.run(['javac','-encoding','UTF-8','-d',str(d),str(source),str(t)],check=True,capture_output=True)
  subprocess.run(['java','-cp',str(d),'Iris26948FlickerHost'],check=True)
 print('PASS 26948 real javac/java actual production Iris26909ShutterIsoMath, shutter-first and highlight budget preserved')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
