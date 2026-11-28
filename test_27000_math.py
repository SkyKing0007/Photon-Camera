from pathlib import Path
import tempfile,subprocess
R=Path(__file__).resolve().parent
s=(R/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawSceneExposureEstimator.kt').read_text()
start=s.index('    fun measureSceneBrightness(');end=s.index('    /** Reproduces MGC',start)
consts='\n'.join(x for x in s.splitlines() if x.strip().startswith('private const val ') and any((' '+n+' ') in x for n in ('SIGNAL_FLOOR','NANOS_PER_MILLISECOND','MILLIS_PER_SECOND','MGC_V25_SENSOR_SENSITIVITY','SCENE_BRIGHTNESS_CALIBRATION','SCENE_BRIGHTNESS_LOG_FLOOR')))
assert len(consts.splitlines())==6,consts
m=s[s.index('internal data class RawSceneBrightnessMeasurement('):s.index('internal enum class RawSceneExposureShotMaxSource')]
code=m+'\ninternal data class RawSceneLinearFrame(val width:Int,val height:Int,val rgb:FloatArray)\n'+consts+'\n'+s[start:end].replace('    fun measureSceneBrightness(', '    internal fun measureSceneBrightness(',1)+"""
fun main(){
 val f=RawSceneLinearFrame(1,1,floatArrayOf(0.12f,0.15f,0.2f))
 fun m(ap:Float,ref:Int,d:Boolean)=measureSceneBrightness(f,10000000,200,ref,ap,d)!!
 for(ap in listOf(1.63f,1.8f,2.6f,4f)) for(ref in listOf(50,100)){
  val fixed=m(ap,ref,false);val dynamic=m(ap,ref,true)
  check(kotlin.math.abs(fixed.sensorSensitivity-17.61f)<0.00001f)
  check(kotlin.math.abs(dynamic.sensorSensitivity-ref/(ap*ap))<0.00002f)
  check(fixed.currentTetMs==dynamic.currentTetMs)
  check((dynamic.logSceneBrightness>fixed.logSceneBrightness)==(dynamic.sensorSensitivity<fixed.sensorSensitivity))
 }
 check(measureSceneBrightness(f,10000000,200,50,Float.NaN,true)==null)
 println("PASS actual Kotlin lens sensitivity equation, 8 cases, fixed legacy, TET invariant and invalid metadata")
}
"""
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'Math.kt').write_text(code)
 subprocess.run(['kotlinc',str(p/'Math.kt'),'-include-runtime','-d',str(p/'math.jar')],check=True)
 subprocess.run(['java','-jar',str(p/'math.jar')],check=True)
