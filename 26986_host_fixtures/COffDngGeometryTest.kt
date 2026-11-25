package com.hinnka.mycamera.processor
import kotlin.math.abs
fun main(){
 val B=Iris26986COffDngGeometry
 val full=Iris26986COffDngGeometry.Bounds(0,0,4096,3072)
 val active=Iris26986COffDngGeometry.Bounds(16,8,4080,3064)
 val crop=Iris26986COffDngGeometry.Bounds(32,24,4064,3048)
 val requested=Iris26986COffDngGeometry.Bounds(1024,768,3072,2304)
 val g=FloatArray(4*5*3){i->1f+(i%4)*.2f+(i/4%5)*.07f+(i/4/5)*.11f}
 check(B.rebaseGains(g,5,3,full,full).contentEquals(g))
 check(B.validate(4096,3072,full,requested,active)==2.0)
 check(B.validate(4096,3072,crop,requested,active)==4032.0/2048)
 val result=B.rebaseGains(g,5,3,active,crop)
 for(y in 0..2)for(x in 0..4)for(c in 0..3){
   val u=(crop.left-active.left+crop.width*x/4.0)/active.width
   val v=(crop.top-active.top+crop.height*y/2.0)/active.height
   check(abs(result[(y*5+x)*4+c]-(1+c*.2+4*u*.07+2*v*.11))<1e-6)
 }
 val padded=B.rebaseGains(g,5,3,active,full)
 check(abs(padded.first()-g.first())<1e-6&&abs(padded.last()-g.last())<1e-6)
 check(B.rebaseGains(floatArrayOf(1f,2f,3f,4f),1,1,active,crop).contentEquals(floatArrayOf(1f,2f,3f,4f)))
 fun rejects(block:()->Unit){check(runCatching(block).isFailure)}
 rejects{B.validate(4096,3072,Iris26986COffDngGeometry.Bounds(33,24,4065,3048),requested,active)}
 rejects{B.validate(4096,3072,Iris26986COffDngGeometry.Bounds(2000,1000,4000,3000),requested,active)}
 rejects{B.rebaseGains(floatArrayOf(1f),5,3,active,crop)}
 rejects{B.rebaseGains(g.copyOf().also{it[1]=Float.NaN},5,3,active,crop)}
 println("PASS C OFF packed-RAW geometry, exact unchanged grid, four-channel cropped bilinear rebase, centered zoom, padded borders, invalid CFA/coverage/map rejection")
}
