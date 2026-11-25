package com.hinnka.mycamera.processor

import kotlin.math.floor

/** C-private bridge from the shutter-frozen physical plane to the packed Bayer DNG grid.
 * Preserve the existing centered B DNG DefaultCropZoom convention, not JPEG resampling.
 * Camera2 gain-map points are rebased using the original C RawPhysicalCrop interpolation
 * (four independent channels; endpoint-normalized bilinear grid). No shading is baked into RAW.
 */
internal object Iris26986COffDngGeometry {
    data class Bounds(val left:Int,val top:Int,val right:Int,val bottom:Int) {
        init { require(left>=0 && top>=0 && right>left && bottom>top) }
        val width get()=right-left
        val height get()=bottom-top
        fun contains(b:Bounds)=left<=b.left&&top<=b.top&&right>=b.right&&bottom>=b.bottom
    }
    fun validate(sensorWidth:Int,sensorHeight:Int,packed:Bounds,requested:Bounds,active:Bounds):Double {
        val sensor=Bounds(0,0,sensorWidth,sensorHeight)
        require(sensor.contains(packed)&&sensor.contains(active)&&active.contains(requested)&&packed.contains(requested))
        require(packed.left%2==0&&packed.top%2==0&&packed.width%2==0&&packed.height%2==0)
        return packed.width.toDouble()/requested.width
    }
    fun rebaseGains(source:FloatArray,columns:Int,rows:Int,active:Bounds,packed:Bounds):FloatArray {
        require(columns>0&&rows>0&&source.size==Math.multiplyExact(Math.multiplyExact(columns,rows),4))
        require(source.all{it.isFinite()&&it>=1f})
        if(active==packed)return source.copyOf()
        fun coordinate(i:Int,n:Int,offset:Int,extent:Int,activeStart:Int,activeExtent:Int):Float {
            val u=if(n>1)i.toFloat()/(n-1) else .5f
            return ((offset-activeStart+extent*u)/activeExtent).coerceIn(0f,1f)*(n-1)
        }
        return FloatArray(source.size){i->
            val channel=i%4;val cell=i/4
            val x=coordinate(cell%columns,columns,packed.left,packed.width,active.left,active.width)
            val y=coordinate(cell/columns,rows,packed.top,packed.height,active.top,active.height)
            val x0=floor(x).toInt();val y0=floor(y).toInt()
            val x1=(x0+1).coerceAtMost(columns-1);val y1=(y0+1).coerceAtMost(rows-1)
            fun sample(xx:Int,yy:Int)=source[(yy*columns+xx)*4+channel]
            val tx=x-x0;val ty=y-y0
            val a=sample(x0,y0)+(sample(x1,y0)-sample(x0,y0))*tx
            val b=sample(x0,y1)+(sample(x1,y1)-sample(x0,y1))*tx
            a+(b-a)*ty
        }
    }
}
