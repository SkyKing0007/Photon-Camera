#!/usr/bin/env python3
"""Actual entire 26915 final-guide Kotlin function compiled by kotlinc.
Typed fake Android-side GPU carrier only; the production JNI is independently
compiled and tested in test_26915_native_guide.py. This catches source/scope
errors like the 26914 V1 customNoise26914 failure before Actions.
"""
from pathlib import Path
import subprocess,tempfile,sys,shutil
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
P=(R if (R/'app/src').is_dir() else R/'candidate_26915') if LIVE else R/'handoff_payload_26915'
source=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
carrier=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java').read_text()
cpp=(P/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
start=source.index('    private fun packIris26876BFinalGuide(')
stop=source.index('    private fun validateFrame(',start)
fn=source[start:stop]
for k in ['tryCreateFinal1xGuide(w, h)','writeFinal1xGuideCpu(rgba, sensorMask)','twoXWronskiGpuUnchanged=true']:
 assert k in fn,k
assert 'lockCpu()' not in fn and 'mapped.put(' not in fn
assert 'public boolean writeFinal1xGuideCpu(ByteBuffer linearRgba16f, ByteBuffer maskR16f)' in carrier
assert 'writeFinal1xGuideNative(' in carrier and 'MotionV2SharedRgba16fCarrier_writeFinal1xGuideNative(' in cpp
if '--static-only' in sys.argv:
 print('PASS 26915 Kotlin consumer/Java/JNI API signature and frozen full source function; full Android Kotlin compiler remains mandatory in Gradle')
 sys.exit(0)
scaffold='''import java.nio.ByteBuffer
import java.nio.ByteOrder
object PLog { fun i(tag:String,body:String) {if(tag.isEmpty()||body.isEmpty())throw Exception()} }
object LargeDirectBuffer {fun free(x:ByteBuffer) {x.clear()}}
class MotionV2SharedRgba16fCarrier : AutoCloseable {
 companion object {fun tryCreateFinal1xGuide(w:Int,h:Int):MotionV2SharedRgba16fCarrier? {
 if(w<=0||h<=0)return null;return MotionV2SharedRgba16fCarrier() }}
 fun writeFinal1xGuideCpu(rgb:ByteBuffer,mask:ByteBuffer):Boolean = rgb.isDirect&&mask.isDirect
 override fun close() {}
}
class Test {val TAG="test"
 fun requireParity(ok:Boolean,msg:String) {if(!ok)throw IllegalStateException(msg)}
 fun invalid(msg:String):Nothing = throw IllegalStateException(msg)
 fun readR16f26836(texture:Int,w:Int,h:Int):ByteBuffer {
   if(texture<=0)throw IllegalStateException();return ByteBuffer.allocateDirect(w*h*2)
 }
'''
end='''
 fun test() {
  val rgba=ByteBuffer.allocateDirect(5*7*8)
  check(packIris26876BFinalGuide(rgba,2,5,7) is MotionV2SharedRgba16fCarrier)
  try {packIris26876BFinalGuide(rgba,0,5,7);throw Exception("mask 0 wrongly accepted")}
  catch(e:IllegalStateException) {check(e.message?.contains("final 1x selected")==true)}
 }
}
fun main(){Test().test();println("PASS 26915 actual complete Kotlin final-guide consumer compiled and executed")}
'''
with tempfile.TemporaryDirectory() as td:
 t=Path(td);(t/'Test.kt').write_text(scaffold+fn+end)
 subprocess.run(['kotlinc',str(t/'Test.kt'),'-include-runtime','-d',str(t/'test.jar')],check=True,capture_output=True,text=True)
 subprocess.run(['java','-jar',str(t/'test.jar')],check=True)
