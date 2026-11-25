package com.hinnka.mycamera.processor.experimentc.lkr2420
import java.nio.ByteBuffer
import java.nio.ByteOrder
fun main(){
 val w=256;val h=256
 fun raw(clipped:Boolean):ByteBuffer {
  val buf=ByteBuffer.allocateDirect(w*h*2).order(ByteOrder.nativeOrder())
  val v=buf.asShortBuffer()
  for(y in 0 until h)for(x in 0 until w){
   val sample=if(clipped && x<w/2)1023 else 450+((x*29+y*13+x*y)%440)
   v.put(y*w+x,sample.toShort())
  };return buf
 }
 fun plan(b:ByteBuffer,n:Int,min:Long=100_000,max:Long=125_000_000,base:Long=20_000_000):FloatArray=Iris26985CHdrAuto.plan(b,w,h,w*2,2,FloatArray(4){64f},1023f,64,base,min,max,n)
 check(plan(raw(true),2).isEmpty())
 check(plan(raw(true),3).contentEquals(floatArrayOf(-2f)))
 check(plan(raw(true),4).contentEquals(floatArrayOf(-2f,-2f)))
 check(plan(raw(true),15).contentEquals(floatArrayOf(-2f,-2f)))
 check(plan(raw(true),15,min=10_000_000).isEmpty())
 check(plan(raw(false),15).isEmpty())
 check(plan(ByteBuffer.allocate(16),15).isEmpty())
 val stats=LkrHdrDecision.Stats(.2,.1,.02,HdrPlusNoiseModel(.01,.001,10,doubleArrayOf(.1)))
 fun decide(n:Int,long:Boolean)=LkrHdrDecision.decide(LkrHdrMode.AUTO,stats,.05,long,n).evs
 check(decide(15,true).contentEquals(floatArrayOf(-2f,-2f,1.5f)))
 check(decide(4,true).contentEquals(floatArrayOf(-2f,-2f)))
 check(decide(5,false).contentEquals(floatArrayOf(-2f,-2f)))
 check(LkrHdrDecision.decide(LkrHdrMode.AUTO,null,.05,true,15).evs.isEmpty())
 check(Iris26985CHdrAuto.shutterNs(20_000_000,-2f)==5_000_000L)
 check(Iris26985CHdrAuto.shutterNs(45_000_000,1.5f)>Iris26985CHdrAuto.LONG_CAP_NS)
 println("PASS authentic RawLens Auto clipping/read-noise, 2/3/4/15 slots, no measurement, range and long cap")
}
