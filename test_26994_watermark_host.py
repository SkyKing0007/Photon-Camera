#!/usr/bin/env python3
"""Real production compositor compiled with JVM Android API models; not Android device proof."""
import pathlib,tempfile,subprocess,sys
root=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parent
src=root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26994COffWatermark.kt'
with tempfile.TemporaryDirectory() as d:
 t=pathlib.Path(d)
 (t/'Context.kt').write_text('''package android.content
import java.io.File
class Context(val root:File){val assets=Assets(root)}
class Assets(val root:File){fun open(s:String)=File(root,s).inputStream()}
''')
 (t/'Log.kt').write_text('''package android.util
object Log{fun i(tag:String,msg:String):Int{println(msg);return 0}}
''')
 (t/'Bitmap.kt').write_text('''package android.graphics
import java.nio.ByteBuffer
import javax.imageio.ImageIO
class ColorSpace(val isSrgb:Boolean=true)
class Bitmap(val width:Int,val height:Int,val config:Config=Config.ARGB_8888,val isMutable:Boolean=true,val rgb:IntArray=IntArray(width*height),val rowBytes:Int=width){
 enum class Config{ARGB_8888,ALPHA_8}
 val colorSpace=ColorSpace();val byteCount=rowBytes*height;var bytes=ByteArray(byteCount);var isRecycled=false
 fun recycle(){check(!isRecycled);isRecycled=true}
 fun getPixel(x:Int,y:Int)=rgb[y*width+x]
 fun getPixels(a:IntArray,offset:Int,stride:Int,x:Int,y:Int,w:Int,h:Int){for(j in 0 until h)System.arraycopy(rgb,(y+j)*width+x,a,offset+j*stride,w)}
 fun setPixels(a:IntArray,offset:Int,stride:Int,x:Int,y:Int,w:Int,h:Int){check(isMutable);for(j in 0 until h)System.arraycopy(a,offset+j*stride,rgb,(y+j)*width+x,w)}
 fun copyPixelsToBuffer(b:ByteBuffer){b.put(bytes)}
 fun copyPixelsFromBuffer(b:ByteBuffer){check(isMutable);b.get(bytes)}
 fun copy(c:Config,mutable:Boolean)=Bitmap(width,height,c,mutable,rgb.copyOf(),rowBytes)
}
object BitmapFactory{class Options{var inScaled=false;var inPreferredConfig=Bitmap.Config.ARGB_8888};fun decodeStream(s:java.io.InputStream,p:Any?,o:Options):Bitmap?{val i=ImageIO.read(s)?:return null;return Bitmap(i.width,i.height,rgb=i.getRGB(0,0,i.width,i.height,null,0,i.width))}}
class Gainmap(val gainmapContents:Bitmap,val ratioMin:FloatArray=floatArrayOf(1f,1f,1f),val ratioMax:FloatArray=floatArrayOf(2f,2f,2f),val gamma:FloatArray=floatArrayOf(1f,1f,1f),val epsilonSdr:FloatArray=floatArrayOf(.001f,.001f,.001f),val epsilonHdr:FloatArray=floatArrayOf(.001f,.001f,.001f))
''')
 (t/'Test.kt').write_text('''package com.hinnka.mycamera.processor.experimentc
import android.content.Context
import android.graphics.*
import java.io.File
import javax.imageio.ImageIO
import kotlin.math.*
fun main(args:Array<String>){
 val ctx=Context(File(args[0]));val wm=Iris26994COffWatermark;var tested=0L
 for((w,h) in listOf(3072 to 4096,4096 to 3072,401 to 601,601 to 401,101 to 101))for(bright in listOf(false,true))for(mutable in listOf(false,true)){
  val gray=if(bright)220 else 40;val bg=0xff000000.toInt() or (gray shl 16) or (gray shl 8) or gray
  val source=Bitmap(w,h,isMutable=mutable,rgb=IntArray(w*h){bg});val g=Iris26994COffWatermark.Geometry(w,h)
  check(wm.useDark(g,source::getPixel)==bright);check(abs(g.wmWidth/w-.115f)<1e-6 && abs(g.margin-min(w,h)*.025f)<1e-5)
  val im=ImageIO.read(File(ctx.root,"watermark/iris_camera_watermark_${if(bright)"dark" else "white"}.png"));check(im.width==2048&&im.height==1312)
  val logo=im.getRGB(0,0,2048,1312,null,0,2048);val area=IntArray(g.w*g.h){bg};val mask=wm.composite(g,logo,area)
  val gw=(w+1)/2;val gh=(h+1)/2;val stride=gw+3;val gm=Bitmap(gw,gh,Bitmap.Config.ALPHA_8,rowBytes=stride);gm.bytes=ByteArray(stride*gh){((it%253)+1).toByte()};val original=gm.bytes.copyOf();val gain=Gainmap(gm)
  val result=wm.apply(ctx,source,gain);check((result===source)==mutable)
  val touched=BooleanArray(original.size);val opaque=BooleanArray(original.size);var count=0
  for(y in 0 until h)for(x in 0 until w){val inside=x in g.x0 until g.x1 && y in g.y0 until g.y1;val i=if(inside)(y-g.y0)*g.w+x-g.x0 else -1;val a=if(inside)mask[i].toInt() and 255 else 0
    if(a==0)check(result.getPixel(x,y)==bg) else {count++;check(result.getPixel(x,y)==area[i]);val sx=((x+.5)*gw/w-.5).coerceIn(0.0,gw-1.0);val sy=((y+.5)*gh/h-.5).coerceIn(0.0,gh-1.0);for(yy in floor(sy).toInt()..ceil(sy).toInt())for(xx in floor(sx).toInt()..ceil(sx).toInt()){val j=yy*stride+xx;touched[j]=true;if(a==255)opaque[j]=true}}
    if(!mutable)check(source.getPixel(x,y)==bg);tested++}
  check(count>0 && count<g.w*g.h)
  for(i in original.indices){val old=original[i].toInt() and 255;val now=gm.bytes[i].toInt() and 255;check(now<=old);if(!touched[i])check(now==old);if(opaque[i])check(now==0)}
  check(gain.ratioMin.contentEquals(floatArrayOf(1f,1f,1f))&&gain.ratioMax.contentEquals(floatArrayOf(2f,2f,2f)))
 }
 val g=Iris26994COffWatermark.Geometry(400,600);val a=IntArray(2048*1312){0x80ffffff.toInt()};val b=IntArray(g.w*g.h){0xff000000.toInt()};val m=wm.composite(g,a,b);check(m.all{(it.toInt() and 255)==128});check(b.all{it==0xff808080.toInt()})
 println("PASS $tested output pixel comparisons; actual assets, adaptive selection, immutable source, transparent pixels, padded gain map support, opaque logo unity, half-alpha blend")
}
''')
 subprocess.run(['kotlinc',str(src),*[str(p) for p in t.glob('*.kt')],'-include-runtime','-d',str(t/'test.jar')],check=True)
 subprocess.run(['java','-Xmx2g','-jar',str(t/'test.jar'),str(root/'app/src/main/assets')],check=True)
