#!/usr/bin/env python3
"""Compile real C native-buffer lease in Kotlin JVM, run exact byte and ownership tests."""
import argparse,pathlib,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');o=p.parse_args();assert o.live!=o.payload
D=(R if o.live else R/'handoff_payload_26989')/'app/src/main/java/com/hinnka/mycamera/processor';S=D/'Iris26989CRawMemory.kt'
code=r'''package com.hinnka.mycamera.processor
import java.nio.ByteBuffer
import java.nio.ByteOrder
fun main(){
 var assertions=0;var allocations=0;var frees=0
 fun ok(v:Boolean){assertions++;check(v){"assertion $assertions"}}
 fun alloc(n:Long):ByteBuffer{allocations++;return ByteBuffer.allocateDirect(n.toInt()).order(ByteOrder.nativeOrder())}
 fun free(b:ByteBuffer){check(b.isDirect);frees++}
 fun bad(block:()->Unit){ok(runCatching(block).isFailure)}
 // Exact little/native endian RAW16, tight, padded, nonzero source position and even CFA crops.
 for(w in listOf(2,4,16,64))for(h in listOf(2,6,16))for(pad in listOf(0,8,32))for(offset in listOf(0,4)){
  val stride=w*2+pad;val source=ByteBuffer.allocateDirect(stride*h+offset+8).order(ByteOrder.nativeOrder())
  for(y in 0 until h)for(x in 0 until w)source.putShort(offset+y*stride+2*x, (y*257+x*19+19).toShort())
  source.position(offset);source.limit(offset+(h-1)*stride+w*2)
  val pos=source.position();val lim=source.limit()
  val lease=Iris26989CRawMemory.copy(source,stride,0,0,w,h,::alloc,::free)
  val b=lease.readOnly();ok(b.isDirect&&b.isReadOnly&&b.remaining()==w*h*2&&b.order()==ByteOrder.nativeOrder())
  for(y in 0 until h)for(x in 0 until w)ok(b.getShort(2*(y*w+x))==(y*257+x*19+19).toShort())
  source.putShort(pos,0);ok(b.getShort(0)==19.toShort());ok(source.position()==pos&&source.limit()==lim)
  bad{b.putShort(0,0)};lease.close();lease.close();bad{lease.readOnly()}
 }
 val p=ByteBuffer.allocateDirect(16*8).order(ByteOrder.nativeOrder());for(i in 0 until 64)p.putShort(i*2,i.toShort())
 val q=Iris26989CRawMemory.copy(p,16,2,2,4,4,::alloc,::free)
 for(y in 0 until 4)for(x in 0 until 4)ok(q.readOnly().getShort(2*(y*4+x))==((y+2)*8+x+2).toShort());q.close()
 val a=allocations
 bad{Iris26989CRawMemory.copy(p,16,1,0,4,4,::alloc,::free)};bad{Iris26989CRawMemory.copy(p,2,0,0,4,4,::alloc,::free)}
 bad{Iris26989CRawMemory.copy(p,16,0,0,4,10,::alloc,::free)};bad{Iris26989CRawMemory.copy(ByteBuffer.allocate(128),16,0,0,4,4,::alloc,::free)};ok(a==allocations)
 bad{Iris26989CRawMemory.copy(p,16,0,0,4,4,{null},::free)}
 var badFree=0;bad{Iris26989CRawMemory.copy(p,16,0,0,4,4,{ByteBuffer.allocateDirect(7)},{badFree++})};ok(badFree==1)
 Iris26989CRawMemory.reserve(100,200);bad{Iris26989CRawMemory.reserve(101,200)};Iris26989CRawMemory.reserve(100,200);Iris26989CRawMemory.release(100);Iris26989CRawMemory.release(100);bad{Iris26989CRawMemory.release(1)}
 Iris26989CRawMemory.reserve(200,200);Iris26989CRawMemory.release(200);ok(allocations==frees)
 // Race independent reservations and exactly-once closes; actual synchronized lease methods.
 val pool=java.util.concurrent.Executors.newFixedThreadPool(4);val owned=Iris26989CRawMemory.copy(p,16,0,0,4,4,{ByteBuffer.allocateDirect(it.toInt())},{badFree++});(1..20).map{pool.submit{owned.close()}}.forEach{it.get()};pool.shutdown();ok(badFree==2)
 println("PASS $assertions actual Kotlin RAW16 ownership assertions: exact sample bytes, crop/padding, no alias, readonly, rejection, bounded reservation, close races")
}
'''
with tempfile.TemporaryDirectory() as td:
 t=pathlib.Path(td);f=t/'MemoryHost.kt';f.write_text(code)
 subprocess.run(['kotlinc',str(S),str(f),'-include-runtime','-d',str(t/'host.jar')],check=True)
 subprocess.run(['java','-jar',str(t/'host.jar')],check=True)
