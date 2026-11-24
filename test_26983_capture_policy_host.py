from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parent
rel=Path('app/src/main/java/com/particlesdevs/photoncamera/capture')
a=r/'actual'/rel;b=r/'candidate'/rel
pairs=[('Iris26909ShutterIsoMath','Iris26983COnShutterIsoMath'),('Iris26910CaptureSafety','Iris26983COnCaptureSafety')]
for orig,copy in pairs:
 s=(b/(copy+'.java')).read_text().replace(copy,orig).replace('isVerifiedPeriodLockedCOnPlan26968','isVerifiedPeriodLockedBPlan26968').replace('snapVerifiedCOnPlan','snapVerifiedBPlan').replace('Call only from C Photo Super Res ON paths.','Call only from B-owned paths.').replace('shared by all C ON physical cameras','shared by all B physical cameras').replace('\n\n// Independent C Photo SR ON copy of the 26982 B policy; no C OFF math.','')
 assert s==(a/(orig+'.java')).read_text()
with tempfile.TemporaryDirectory() as td:
 t=Path(td);p=t/'Parity.java';p.write_text('''import com.particlesdevs.photoncamera.capture.*;
import java.util.Random;
public class Parity {
 static void ck(boolean ok){if(!ok)throw new AssertionError();}
 static void eq(Iris26909ShutterIsoMath.Plan b,Iris26983COnShutterIsoMath.Plan c){
   ck((b==null)==(c==null));if(b==null)return;
   ck(b.shutterNs==c.shutterNs && b.iso==c.iso && b.frameDurationNs==c.frameDurationNs && Double.doubleToLongBits(b.targetEnergy)==Double.doubleToLongBits(c.targetEnergy) && b.shutterFirstUseful==c.shutterFirstUseful);
 }
 public static void main(String[] args){Random rng=new Random(26983);int valid=0;
 for(int i=0;i<10000;i++){
  long shutter=rng.nextInt(100000000)+1L;int iso=50+rng.nextInt(6400);int lo=50,hi=6400;long min=1000,max=100000000L,frame=100000000L;double focal=8+rng.nextDouble()*492;boolean ois=rng.nextBoolean(),moving=rng.nextBoolean();float mean=rng.nextFloat(),clipped=rng.nextFloat()*0.02f;long period=new long[]{0,8333333,10000000}[rng.nextInt(3)];
  var b=Iris26909ShutterIsoMath.solve26970(shutter,iso,lo,hi,min,max,frame,focal,ois,moving,mean,clipped,period);var c=Iris26983COnShutterIsoMath.solve26970(shutter,iso,lo,hi,min,max,frame,focal,ois,moving,mean,clipped,period);eq(b,c);if(b!=null)valid++;
  ck(Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(b,period)==Iris26983COnShutterIsoMath.isVerifiedPeriodLockedCOnPlan26968(c,period));eq(Iris26909ShutterIsoMath.snapVerifiedBPlan(b,period,min,lo,hi,frame),Iris26983COnShutterIsoMath.snapVerifiedCOnPlan(c,period,min,lo,hi,frame));
  float mean2=rng.nextFloat();int n=rng.nextInt(8);ck(Iris26909ShutterIsoMath.rawSceneRemeter26970(mean,mean2,clipped,n)==Iris26983COnShutterIsoMath.rawSceneRemeter26970(mean,mean2,clipped,n));
  int harmonic=rng.nextInt(10);long skew=rng.nextInt(100000000);double span=rng.nextDouble();ck(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(harmonic,skew,span)==Iris26983COnShutterIsoMath.verifiedMainsPeriodNs(harmonic,skew,span));
  int count=rng.nextInt(33)-1;boolean aux=rng.nextBoolean();ck(Iris26910CaptureSafety.completionTimeoutMs(count,shutter,aux)==Iris26983COnCaptureSafety.completionTimeoutMs(count,shutter,aux));
  boolean started=rng.nextBoolean(),completed=rng.nextBoolean(),ready=rng.nextBoolean();long elapsed=rng.nextInt(3000)-1;ck(Iris26910CaptureSafety.attemptStalled(started,completed,ready,elapsed)==Iris26983COnCaptureSafety.attemptStalled(started,completed,ready,elapsed));
  long frozen=rng.nextInt(100000000)+1;int frozenIso=rng.nextInt(6400)+1;double window=rng.nextDouble();boolean require=rng.nextBoolean();ck(Iris26910CaptureSafety.frozenNormalPairMatches(shutter,iso,frozen,frozenIso,window,require)==Iris26983COnCaptureSafety.frozenNormalPairMatches(shutter,iso,frozen,frozenIso,window,require));
  float ev=rng.nextFloat()*-5;double energy=(double)shutter*iso;ck(Double.doubleToLongBits(Iris26910CaptureSafety.targetEnergy(energy,ev))==Double.doubleToLongBits(Iris26983COnCaptureSafety.targetEnergy(energy,ev)));
  ck(Float.floatToIntBits(Iris26910CaptureSafety.lowLightPreviewLiftEv(shutter,iso,mean,clipped))==Float.floatToIntBits(Iris26983COnCaptureSafety.lowLightPreviewLiftEv(shutter,iso,mean,clipped)));
 }
 ck(valid>1000);System.out.println("PASS 10000 B/C acquisition policy comparisons ("+valid+" admitted shutter plans), exact copied sources, bit-exact math");
 }
}''')
 subprocess.run(['javac','-d',str(t),*[str(root/(name+'.java')) for root,idx in [(a,0),(b,1)] for name in [q[idx] for q in pairs]],str(p)],check=True)
 subprocess.run(['java','-cp',str(t),'Parity'],check=True)
