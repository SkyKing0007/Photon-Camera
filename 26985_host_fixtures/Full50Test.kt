package com.hinnka.mycamera.processor.experimentc.lkr2420
import java.io.File
fun main(args:Array<String>){
 val w=8192;val h=6144
 val meta=RawFrameMetadata("host-physical",1,200,20_000_000L,BayerPattern.RGGB,ImmutableFloatValues(floatArrayOf(64f,64f,64f,64f)),1023f,ImmutableDoubleValues(doubleArrayOf(.5,1.0,.8)),ImmutableDoubleValues(doubleArrayOf(1.0,.1,.2,.3,1.0,.4,.5,.6,1.0)),referenceIlluminant1=21)
 val p=MergeProvenance("RawLens 2.4.20 host 50MP",15,15,0,12345L,2,"host-physical",true)
 val dest=File(args[0]);dest.outputStream().buffered(1024*1024).use{out->
  LinearRgbDngWriter.writeStriped(out,w,h,meta,p,stripRows=256,captureTimeMillis=1700000000000L,white=2f){y,rows,band->
    check(rows<=256); for(i in 0 until rows*w*3)band[i]=when(i%3){0->.25f;1->.5f;else->1.5f}
  }
 }
 check(dest.length()>w.toLong()*h*6L)
 println("PASS full 8192x6144 50,331,648-pixel HDR Linear DNG striped writer: ${dest.length()} bytes")
}
