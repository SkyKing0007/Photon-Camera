package com.hinnka.mycamera.processor

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.round
import kotlin.math.sqrt

/**
 * Experiment C-only extraction of the RAW camera->PCS color-spec algorithm
 * from bjzhou/PhotonCamera 1.29.0 DngSdkColorSpec (pinned upstream commit
 * 0a8a11defe7d932d8c8a729120a4d5f159e9d677). It implements its physical
 * Camera2/DNG dual-illuminant, two ForwardMatrix, camera calibration, as-shot
 * neutral, Bradford and Robertson interpolation contract, not a McCamy CCT
 * approximation or an ad hoc XYZ transform. No A/B renderer is touched.
 *
 * Camera2 has no DNG AnalogBalance tag; original dng_color_spec supplies the
 * identity analog vector for absent metadata. Any absent physical matrix or
 * illuminant is rejected before output. Original donor source license Apache-2.0.
 */
internal object Iris26975CDonorDngColorSpec {
    private const val EPS = 1e-6f
    private const val D50X = .3457f
    private const val D50Y = .3585f
    private val PCS = floatArrayOf(.9642957f,1f,.8251046f)
    private val ID = floatArrayOf(1f,0f,0f,0f,1f,0f,0f,0f,1f)
    private val Bradford = floatArrayOf(
        .8951f,.2664f,-.1614f,-.7502f,1.7135f,.0367f,.0389f,-.0685f,1.0296f)
    private val D65ToD50 = floatArrayOf(
        1.0478112f,.0228866f,-.0501270f,
        .0295424f,.9904844f,-.0170491f,
        -.0092345f,.0150436f,.7521316f)
    private class Profile(
        var low: Float, var high: Float,
        var cLow: FloatArray, var cHigh: FloatArray,
        var fLow: FloatArray?, var fHigh: FloatArray?,
        var calLow: FloatArray, var calHigh: FloatArray,
    )
    private data class Matrices(
        val color: FloatArray,val forward: FloatArray?,val calibration: FloatArray)
    private data class Temp(val reciprocal:Double,val u:Double,val v:Double,val slope:Double)
    // The actual dng_color_spec/Robertson table, not a polynomial CCT estimate.
    private val tempTable = arrayOf(
        Temp(0.0,.18006,.26352,-.24341),Temp(10.0,.18066,.26589,-.25479),
        Temp(20.0,.18133,.26846,-.26876),Temp(30.0,.18208,.27119,-.28539),
        Temp(40.0,.18293,.27407,-.30470),Temp(50.0,.18388,.27709,-.32675),
        Temp(60.0,.18494,.28021,-.35156),Temp(70.0,.18611,.28342,-.37915),
        Temp(80.0,.18740,.28668,-.40955),Temp(90.0,.18880,.28997,-.44278),
        Temp(100.0,.19032,.29326,-.47888),Temp(125.0,.19462,.30141,-.58204),
        Temp(150.0,.19962,.30921,-.70471),Temp(175.0,.20525,.31647,-.84901),
        Temp(200.0,.21142,.32312,-1.0182),Temp(225.0,.21807,.32909,-1.2168),
        Temp(250.0,.22511,.33439,-1.4512),Temp(275.0,.23247,.33904,-1.7298),
        Temp(300.0,.24010,.34308,-2.0637),Temp(325.0,.24702,.34655,-2.4681),
        Temp(350.0,.25591,.34951,-2.9641),Temp(375.0,.26400,.35200,-3.5814),
        Temp(400.0,.27218,.35407,-4.3633),Temp(425.0,.28039,.35577,-5.3762),
        Temp(450.0,.28863,.35714,-6.7262),Temp(475.0,.29685,.35823,-8.5955),
        Temp(500.0,.30505,.35907,-11.324),Temp(525.0,.31320,.35968,-15.628),
        Temp(550.0,.32129,.36011,-23.325),Temp(575.0,.32931,.36038,-40.770),
        Temp(600.0,.33724,.36051,-116.45))

    internal data class Solution(
        val cameraToPcs: FloatArray,
        val cameraWhite: FloatArray,
        val sceneWhiteXy: FloatArray,
        val interpolationLow: Float,
    )

    internal fun solve(
        color1:FloatArray,color2:FloatArray?,
        forward1:FloatArray?,forward2:FloatArray?,
        calibration1:FloatArray?,calibration2:FloatArray?,
        neutral:FloatArray,illuminant1Kelvin:Int,illuminant2Kelvin:Int,
    ):Solution {
        fun valid(m:FloatArray)=m.size==9 && m.all { it.isFinite() } &&
            m.sumOf { abs(it).toDouble() } > .01
        // DngSdkColorSpec.prepareProfile permits an absent second illuminant,
        // ForwardMatrix and CameraCalibration. Only the physical first
        // ColorMatrix and as-shot neutral are mandatory in this C path.
        // A matrix-based (no-ForwardMatrix) source uses the inverted adapted
        // ColorMatrix exactly as the pinned original donor.
        require(valid(color1) &&
            (color2 == null || valid(color2)) &&
            (forward1 == null || valid(forward1)) &&
            (forward2 == null || valid(forward2)) &&
            (calibration1 == null || valid(calibration1)) &&
            (calibration2 == null || valid(calibration2)) &&
            neutral.size==3 && neutral.all { it.isFinite() && it>0f }) {
            "26975 C cannot build donor color-spec from physical DNG metadata"
        }
        val kOne=calibration1?.copyOf() ?: ID.copyOf()
        val kTwo=calibration2?.copyOf() ?: ID.copyOf()
        var t1=illuminant1Kelvin.toFloat();var t2=illuminant2Kelvin.toFloat()
        var c1=mul(kOne,normalizeColor(color1))
        var c2=color2?.let { mul(kTwo,normalizeColor(it)) } ?: c1.copyOf()
        var f1=forward1?.let(::normalizeForward)
        var f2=forward2?.let(::normalizeForward)
        var k1=kOne;var k2=kTwo
        if(color2==null || t1<=0f || t2<=0f || abs(t1-t2)<EPS) {
            t1=5000f;t2=5000f;c2=c1;f2=f1;k2=k1
        } else if(t1>t2) {
            val tmpT=t1;t1=t2;t2=tmpT
            val tmpC=c1;c1=c2;c2=tmpC
            val tmpF=f1;f1=f2;f2=tmpF
            val tmpK=k1;k1=k2;k2=tmpK
        }
        val p=Profile(t1,t2,c1,c2,f1,f2,k1,k2)
        val whiteXy=neutralToXy(p,neutral)
        val matrices=find(p,whiteXy)
        val white=cameraWhite(matrices,whiteXy)
        val whiteFromPcs=mul(matrices.color,whiteMap(floatArrayOf(D50X,D50Y),whiteXy))
        val pcsWhite=mulVec(whiteFromPcs,PCS)
        val scale=1f/max(max(max(pcsWhite[0],pcsWhite[1]),pcsWhite[2]),EPS)
        // Preserved from donor even though ForwardMatrix supplies the PCS branch.
        require(scale.isFinite() && scale>0f)
        val cameraToPcs=if (matrices.forward != null) {
            // The reference-camera neutral is required only by the genuine
            // ForwardMatrix branch, not the donor's ColorMatrix inversion.
            val individualToReference=inv(mul(ID,matrices.calibration))
            val referenceWhite=mulVec(individualToReference,white)
            require(referenceWhite.all { it.isFinite() && it>EPS }) {
                "26975 C reference-camera neutral is invalid"
            }
            val inverseWhite=diag(floatArrayOf(
                1f/referenceWhite[0],1f/referenceWhite[1],1f/referenceWhite[2]))
            mul(mul(matrices.forward,inverseWhite),individualToReference)
        } else {
            // Original dng_color_spec cameraToPcsForWhite(): ColorMatrix
            // branch after white-point adaptation and PCS normalization.
            val adapted=mul(matrices.color,whiteMap(floatArrayOf(D50X,D50Y),whiteXy))
            val pcs=mulVec(adapted,PCS)
            val maximum=max(max(pcs[0],pcs[1]),pcs[2])
            val scaleToWhite=1f/max(maximum,EPS)
            inv(FloatArray(9) { adapted[it]*scaleToWhite })
        }
        check(cameraToPcs.all { it.isFinite() })
        val lowWeight=temperatureWeight(p,whiteXy)
        return Solution(cameraToPcs,white,whiteXy,lowWeight)
    }

    /** Original computeXyzD50ToGamut, restricted to the two real output gamuts. */
    internal fun xyzD50ToProPhoto():FloatArray = gamut(.734699f,.265301f,
        .159597f,.840403f,.036598f,.000105f,.345704f,.358540f)
    internal fun xyzD50ToLinearSrgb():FloatArray = gamut(.640f,.330f,
        .300f,.600f,.150f,.060f,.3127f,.3290f)

    internal fun mul(a:FloatArray,b:FloatArray):FloatArray {
        require(a.size==9 && b.size==9)
        return FloatArray(9) { i ->
            val row=i/3;val col=i%3
            a[row*3]*b[col]+a[row*3+1]*b[col+3]+a[row*3+2]*b[col+6]
        }
    }
    internal fun diag(v:FloatArray)=floatArrayOf(v[0],0f,0f,0f,v[1],0f,0f,0f,v[2])
    private fun inv(m:FloatArray):FloatArray {
        require(m.size==9 && m.all{it.isFinite()})
        val d=m[0]*(m[4]*m[8]-m[5]*m[7])-
            m[1]*(m[3]*m[8]-m[5]*m[6])+
            m[2]*(m[3]*m[7]-m[4]*m[6])
        require(d.isFinite() && abs(d)>1e-12f) {"26975 C singular donor color matrix"}
        return floatArrayOf(
            (m[4]*m[8]-m[5]*m[7])/d,(m[2]*m[7]-m[1]*m[8])/d,
            (m[1]*m[5]-m[2]*m[4])/d,(m[5]*m[6]-m[3]*m[8])/d,
            (m[0]*m[8]-m[2]*m[6])/d,(m[2]*m[3]-m[0]*m[5])/d,
            (m[3]*m[7]-m[4]*m[6])/d,(m[1]*m[6]-m[0]*m[7])/d,
            (m[0]*m[4]-m[1]*m[3])/d)
    }
    private fun mulVec(m:FloatArray,v:FloatArray)=floatArrayOf(
        m[0]*v[0]+m[1]*v[1]+m[2]*v[2],
        m[3]*v[0]+m[4]*v[1]+m[5]*v[2],
        m[6]*v[0]+m[7]*v[1]+m[8]*v[2])
    private fun xyz(xy:FloatArray):FloatArray {
        val x=xy[0];val y=xy[1]
        require(x.isFinite() && y.isFinite() && y>EPS)
        return floatArrayOf(x/y,1f,(1f-x-y)/y)
    }
    private fun xy(xyz:FloatArray):FloatArray {
        val total=xyz.sum()
        require(total>EPS && total.isFinite() && xyz.all{it.isFinite()})
        return floatArrayOf(xyz[0]/total,xyz[1]/total)
    }
    private fun normalizeColor(matrix:FloatArray):FloatArray {
        val result=matrix.copyOf()
        val coord=mulVec(result,PCS)
        val maxCoord=max(max(coord[0],coord[1]),coord[2])
        if(maxCoord>0f && (maxCoord<.99f || maxCoord>1.01f)) {
            val scale=1f/maxCoord
            for (index in result.indices) result[index]*=scale
        }
        for(index in result.indices) result[index]=round(result[index]*10000f)/10000f
        return result
    }
    private fun normalizeForward(matrix:FloatArray):FloatArray {
        val rowSum=floatArrayOf(matrix[0]+matrix[1]+matrix[2],
            matrix[3]+matrix[4]+matrix[5],matrix[6]+matrix[7]+matrix[8])
        val result=matrix.copyOf()
        for(row in 0..2) {
            val scale=if(abs(rowSum[row])>EPS)PCS[row]/rowSum[row] else 1f
            for(col in 0..2)result[row*3+col]*=scale
        }
        return result
    }
    private fun cameraWhite(m:Matrices,whiteXy:FloatArray):FloatArray {
        val out=mulVec(m.color,xyz(whiteXy))
        val scale=1f/max(max(max(out[0],out[1]),out[2]),EPS)
        for(i in out.indices) out[i]=(out[i]*scale).coerceIn(.001f,1f)
        return out
    }
    private fun neutralToXy(p:Profile,neutral:FloatArray):FloatArray {
        var last=floatArrayOf(D50X,D50Y)
        repeat(30) { pass ->
            val xyzToCamera=find(p,last).color
            val cameraToXyz=inv(xyzToCamera)
            val next=xy(mulVec(cameraToXyz,neutral))
            if(abs(next[0]-last[0])+abs(next[1]-last[1])<1e-7f) return next
            if(pass==29) {
                next[0]=(last[0]+next[0])*.5f
                next[1]=(last[1]+next[1])*.5f
                return next
            }
            last=next
        }
        return last
    }
    private fun find(p:Profile,whiteXy:FloatArray):Matrices {
        val weight=temperatureWeight(p,whiteXy)
        fun lerp(a:FloatArray,b:FloatArray)=FloatArray(9){i->a[i]*weight+b[i]*(1f-weight)}
        // Kotlin mutable profile fields cannot be smart-cast. Freeze the donor
        // illuminant pair once for this interpolation, just as the physical
        // shot's Camera2/DNG metadata is frozen at shutter.
        val fLow = p.fLow
        val fHigh = p.fHigh
        val forward=when {
            fLow!=null && fHigh!=null -> lerp(fLow,fHigh)
            fLow!=null -> fLow.copyOf()
            else -> fHigh?.copyOf()
        }
        return Matrices(lerp(p.cLow,p.cHigh),forward,
            lerp(p.calLow,p.calHigh))
    }
    private fun temperatureWeight(p:Profile,whiteXy:FloatArray):Float {
        val temp=tempForXy(whiteXy)
        return when {
            temp<=p.low -> 1f
            temp>=p.high -> 0f
            abs(p.low-p.high)<EPS -> 1f
            else -> ((1f/temp - 1f/p.high)/(1f/p.low - 1f/p.high)).coerceIn(0f,1f)
        }
    }
    private fun tempForXy(xy:FloatArray):Float {
        val denom=1.5-xy[0]+6.0*xy[1]
        if(!denom.isFinite() || abs(denom)<1e-12)return 5000f
        val u=2.0*xy[0]/denom
        val v=3.0*xy[1]/denom
        var lastDistance=0.0
        for(index in 1 until tempTable.size) {
            var du=1.0;var dv=tempTable[index].slope
            val length=sqrt(1.0+dv*dv);du/=length;dv/=length
            val uu=u-tempTable[index].u;val vv=v-tempTable[index].v
            var distance=-uu*dv+vv*du
            if(distance<=0.0 || index==tempTable.lastIndex) {
                if(distance>0.0) distance=0.0
                val dt=-distance
                val frac=if(index==1) 0.0 else dt/(lastDistance+dt)
                val reciprocal=tempTable[index-1].reciprocal*frac+
                    tempTable[index].reciprocal*(1.0-frac)
                return (1e6/reciprocal).toFloat().coerceIn(1000f,100000f)
            }
            lastDistance=distance
        }
        return 5000f
    }
    private fun whiteMap(white1:FloatArray,white2:FloatArray):FloatArray {
        val w1=mulVec(Bradford,xyz(white1))
        val w2=mulVec(Bradford,xyz(white2))
        for(i in 0..2) {w1[i]=max(w1[i],0f);w2[i]=max(w2[i],0f)}
        val correction=diag(FloatArray(3){i->
            (if(w1[i]>0f)w2[i]/w1[i] else 10f).coerceIn(.1f,10f)})
        return mul(mul(inv(Bradford),correction),Bradford)
    }
    private fun gamut(
        xr:Float,yr:Float,xg:Float,yg:Float,xb:Float,yb:Float,xw:Float,yw:Float
    ):FloatArray {
        val prim=floatArrayOf(xr/yr,xg/yg,xb/yb,1f,1f,1f,
            (1f-xr-yr)/yr,(1f-xg-yg)/yg,(1f-xb-yb)/yb)
        val inverse=inv(prim)
        val white=floatArrayOf(xw/yw,1f,(1f-xw-yw)/yw)
        val gains=mulVec(inverse,white)
        val rgbToXyz=FloatArray(9){i->prim[i]*gains[i%3]}
        val isD50=abs(xw-D50X)<.002f && abs(yw-D50Y)<.002f
        return inv(if(isD50)rgbToXyz else mul(D65ToD50,rgbToXyz))
    }
}
