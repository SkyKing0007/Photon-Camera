package com.hinnka.mycamera.processor.experimentc.lkr2420
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
fun main(args:Array<String>) {
 val n=6*4*3
 val values=FloatArray(n) { i-> (i%9)*0.25f }
 val meta=RawFrameMetadata("physical-test",6,400,20000000L,BayerPattern.RGGB,ImmutableFloatValues(floatArrayOf(64f,64f,64f,64f)),1023f,ImmutableDoubleValues(doubleArrayOf(.5,1.0,.8)),ImmutableDoubleValues(doubleArrayOf(1.0,0.1,0.2,0.3,1.0,0.4,0.5,0.6,1.0)),referenceIlluminant1=21,noiseProfile=ImmutableDoubleValues(doubleArrayOf(.01,.002,.02,.003,.03,.004)))
 val p=MergeProvenance("2.4.20",8,6,2,12345L,2,"physical-test",true)
 for(white in listOf(1f,2f)) File(args[0],"linear-$white.dng").outputStream().use{out->LinearRgbDngWriter.writeStriped(out,6,4,meta,p,stripRows=2,captureTimeMillis=1700000000000L,white=white) { y,rows,band->values.copyInto(band,0,y*18,(y+rows)*18) }}
 check(LinearRgbDngWriter.quantize(.5f)==32768)
 check(runCatching{LinearRgbDngWriter.quantize(Float.NaN)}.isFailure)
 val rgb=FloatArray(4*4*3){if(it%3==0).2f else if(it%3==1).3f else .4f}
 val model=LensShadingModel(2,2,FloatArray(16){1f+(it%4)*.2f},IntRectSnapshot(0,0,2,2))
 val b=java.nio.FloatBuffer.wrap(rgb)
 LkrLensShading.applyShadingMapped(b,4,4,model,0,0,.5f,.5f,null,1f)
 check(kotlin.math.abs(rgb[0]-.2f)<1e-6 && kotlin.math.abs(rgb[1]-.39f)<1e-6 && kotlin.math.abs(rgb[2]-.64f)<1e-6)
 println("PASS donor Kotlin writer / real TinyDNG JNI / mapped lens shading")
}
