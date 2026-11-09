#!/usr/bin/env python3
"""Compile ACTUAL, UNMODIFIED production 26914 B true-2x Kotlin lambda and helper.

A Kotlin helper-only regression missed the original 26914 leaked variable. This
regression compiles the complete actual production expression with typed stub
interfaces and checks both imported-profile and RAW-burst fallback call paths.
The Android project, NDK, GLSL and assemble are STILL separate mandatory gates.
"""
from pathlib import Path
import subprocess, tempfile, sys, hashlib
R=Path(__file__).resolve().parent
SOURCE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'

def balanced_body(src, signature):
    at=src.index(signature)
    start=src.index('{',at)
    dep=0
    for k in range(start,len(src)):
        if src[k]=='{': dep+=1
        elif src[k]=='}':
            dep-=1
            if dep==0:return src[at:k+1]
    raise AssertionError('unterminated production Kotlin body '+signature)

def compile_actual(kotlin_file, expect_failure=False):
    original=kotlin_file.read_text()
    owner=balanced_body(original,'    private fun iris26914BNoiseForPhysical(')
    marker='                    { rgb2x: Int, clip2x: Int ->'
    begin=original.index(marker,original.index('iris26864NativeWronski2x = if'))
    close=original.index('\n                    }\n                } else null,', begin)
    actual_lambda=original[begin:close+len('\n                    }')]
    # A real direct source extraction, not a translated mock implementation.
    assert 'val customNoise26914 = iris26914BNoiseForPhysical(' in actual_lambda
    assert 'GlesIris26864NativeRawr.run(' in actual_lambda
    assert 'IRIS_26864_REAL_WRONSKI_B_2X_DISPATCH' in actual_lambda
    assert 'GlesIris26912HighlightReference.select(' in actual_lambda
    owner=owner.replace('private fun iris26914BNoiseForPhysical','fun iris26914BNoiseForPhysical',1)
    source='''package test
import com.hinnka.mycamera.processor.*

enum class RawBurstFrameRole { NORMAL }
class Frame(val role:RawBurstFrameRole,val frameNumber:Long,val sensorTimestampNs:Long,
            val physicalCameraId:String?,val sensitivityIso:Int)
class Size(val x:Int,val y:Int)
class Parameters(var iris26903NightB:Boolean=false, val blackLevel:FloatArray=floatArrayOf(0f,0f,0f,0f),
    val motionV2ColorTransform:FloatArray=floatArrayOf(1f,1f,1f), val motionV2DirectColorValid:Boolean=true)
class MgcBase(val motionV2FrameNumber:Long=77L,val motionV2AlternativeHighlight26912:Boolean=true,
              val motionV2PreviewHighlightP99526912:Float=.9f)
object PhotonCamera { fun getApplicationContextStatic():Any=Any() }
object PLog { fun i(tag:String,message:String) { check(message.isNotBlank()) } }
fun invalid(message:String):Nothing=error(message)
fun requireParity(ok:Boolean, message:String) { check(ok){message} }
class Model(val shotNoise:FloatArray,val readNoise:FloatArray)
class Profile(val model:Model) {fun evaluate(iso:Int):Model?=if(iso>0)model else null}
object IrisNoiseProfileStore {
 val selected=mutableMapOf<String,Profile>()
 fun loadBOffForPhysical(context:Any,physical:String):Profile?=selected[physical]
}
object LiveProduction {
 const val TAG="26864"
 val size=Size(48,48)
 val referenceTimestamp=991122L
 val frames=listOf(Frame(RawBurstFrameRole.NORMAL,77L,991122L,"physical-5",200),
                   Frame(RawBurstFrameRole.NORMAL,78L,991123L,"physical-5",200))
 val mgcBase=MgcBase()
 val parameters=Parameters()
 val cfa=0
 val wb=floatArrayOf(1f,1f,1f)
 val lsc=floatArrayOf()
 val lscWidth=0
 val lscHeight=0
 val whiteLevel=1023f
'''+owner+'''
 fun capture(rgb2x:Int,clip2x:Int){
   val productionLambda:(Int,Int)->Unit = '''+actual_lambda+'''
   productionLambda(rgb2x,clip2x)
 }
}
fun main() {
 val model=Model(floatArrayOf(.01f,.02f,.03f,.04f),floatArrayOf(.001f,.002f,.003f,.004f))
 IrisNoiseProfileStore.selected["physical-5"]=Profile(model)
 LiveProduction.parameters.iris26903NightB=false
 LiveProduction.capture(11,12)
 check(GlesIris26864NativeRawr.records.size==1)
 check(GlesIris26864NativeRawr.records[0].noise?.size==8)
 check(GlesIris26864NativeRawr.records[0].noise?.get(0)==.01f)
 check(GlesIris26864NativeRawr.records[0].noise?.get(7)==.004f)
 IrisNoiseProfileStore.selected.clear()
 LiveProduction.parameters.iris26903NightB=true
 LiveProduction.capture(13,14)
 check(GlesIris26864NativeRawr.records.size==2)
 check(GlesIris26864NativeRawr.records[1].noise==null)
 check(GlesIris26864NativeRawr.records[0].true2x && GlesIris26864NativeRawr.records[1].true2x)
 check(GlesIris26864NativeRawr.records[0].reference==0 && GlesIris26864NativeRawr.records[1].reference==0)
 check(GlesIris26864NativeRawr.records[0].frozen.closed)
 check(GlesIris26864NativeRawr.records[1].frozen.closed)
 println("PASS 26914 real entire Wronski consumer Kotlin lambda compiled: Photo/Night, custom/fallback, reference and frozen-ingress lifetime")
}
'''
    stubs='''package com.hinnka.mycamera.processor
import test.*
class Frozen(val width:Int,val height:Int):AutoCloseable {
 var closed=false
 val buffers=arrayOf<java.nio.ByteBuffer>()
 val stridesBytes=intArrayOf(96)
 val exposures=floatArrayOf(.02f)
 val blackByFrameByPhase=floatArrayOf(0f)
 val sensorWhiteByFrame=floatArrayOf(1023f)
 override fun close() {closed=true}
}
object GlesIris26864FrozenRawrIngress {
 fun borrowNormals(frames:List<Frame>,w:Int,h:Int,black:FloatArray,white:Float):Frozen {
  require(frames.isNotEmpty() && w>0 && h>0 && black.size==4 && white>0)
  return Frozen(w,h)
 }
}
class Motion(val staticTrusted:Boolean,val shutterAdjacent:Set<Int>?)
object GlesIris26889BOffSceneMotion {
 fun classify(frozen:Frozen,cfa:Int,ref:Int):Motion=Motion(true,null)
}
object GlesIris26870GpuSharpest {
 fun select(frozen:Frozen,cfa:Int,ref:Int,adjacent:Set<Int>?):Int=ref
}
object GlesIris26912HighlightReference {
 fun select(buffers:Array<java.nio.ByteBuffer>,strides:IntArray,exposures:FloatArray,black:FloatArray,
            whites:FloatArray,w:Int,h:Int,chosen:Int,ref:Int,p995:Float,staticSafe:Boolean):Int=chosen
}
class FrozenColor(val amazeWhiteBalance:FloatArray)
object GlesIris26856RawrColorContract {
 fun freeze(wb:FloatArray,transform:FloatArray,valid:Boolean):FrozenColor=FrozenColor(wb)
}
object GlesIris26864NativeRawr {
 data class Record(val true2x:Boolean,val noise:FloatArray?,val reference:Int,val frozen:Frozen)
 val records=mutableListOf<Record>()
 fun run(app:Any,frozen:Frozen,wb:FloatArray,lsc:FloatArray,lscW:Int,lscH:Int,cfa:Int,
         cropX:Int,cropY:Int,fullW:Int,fullH:Int,reference:Int,true2x:Boolean,
         rgb2x:Int,clip2x:Int,physicalIdentity:Long,noise:FloatArray?) {
  check(!frozen.closed && physicalIdentity!=0L && fullW>0 && fullH>0)
  records.add(Record(true2x,noise?.copyOf(),reference,frozen))
 }
}
'''
    with tempfile.TemporaryDirectory(prefix='photon_26914_consumer_') as d:
        root=Path(d)
        a=root/'Production.kt';a.write_text(source)
        b=root/'Stubs.kt';b.write_text(stubs)
        jar=root/'scope.jar'
        p=subprocess.run(['kotlinc',str(a),str(b),'-include-runtime','-d',str(jar)],capture_output=True,text=True)
        if expect_failure:
            assert p.returncode!=0, 'Original failed 26914 source unexpectedly compiled'
            assert 'unresolved reference' in p.stderr.lower() and 'customNoise26914' in p.stderr,p.stderr[:4000]
            print('PASS compiler reproduces genuine original failed Kotlin unresolved scope')
            return
        if p.returncode:raise AssertionError('ACTUAL Wronski Kotlin compilation FAILED:\n'+p.stderr[-5000:])
        out=subprocess.run(['java','-jar',str(jar)],capture_output=True,text=True)
        if out.returncode:raise AssertionError('Kotlin production snippet runtime FAILED:\n'+out.stderr[-3000:])
        print(out.stdout.strip())
if __name__=='__main__':
    f=Path(sys.argv[1]) if len(sys.argv)>1 else R/SOURCE
    compile_actual(f,expect_failure='--expect-failure' in sys.argv)
